# ═══════════════════════════════════════════════════════════════
# SERVICIO DE INGESTA - OPENFOODFACTS PERÚ
# ═══════════════════════════════════════════════════════════════
# Fuente: https://world.openfoodfacts.org/api/v2/
# Filtro Perú: https://world.openfoodfacts.org/facets/countries/Peru
#
# Esta fuente NO requiere API key. Solo requiere conexión a internet.
# ═══════════════════════════════════════════════════════════════

import requests
import json
import re
import os
from sqlalchemy.orm import Session
from app.models import Recipe

# ──────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ──────────────────────────────────────────────────────────────
# URL base para búsqueda (API v1 funciona mejor para filtros por país)
OPENFOODFACTS_SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"

# Parámetros alternativos que funcionan para filtrar por Perú
OPENFOODFACTS_PARAMS_V1 = {
    "search_terms": "",
    "search_simple": "1",
    "action": "process",
    "json": "1",
    "page_size": "50",
    # Opción 1: Filtro por país de venta
    "purchase_places": "Peru",
    # Opción 2: Filtro por tiendas en Perú (complementario)
    "stores": "Peru",
}


# ──────────────────────────────────────────────────────────────
# FUNCIÓN PRINCIPAL DE INGESTA
# ──────────────────────────────────────────────────────────────

def fetch_openfoodfacts_peru(max_pages: int = 20, page_size: int = 50) -> list:
    """
    Consume la API de OpenFoodFacts buscando productos de Perú.
    
    Usa la API v1 con búsqueda por términos peruanos y filtra
    manualmente los productos que pertenecen a Perú.
    
    Parámetros:
        max_pages: número máximo de páginas a recorrer
        page_size: productos por página
    
    Retorna:
        Lista de productos crudos de OpenFoodFacts.
    """
    all_products = []
    
    # Términos relacionados con comida peruana
    search_terms = [
        "ceviche",
        "lomo+saltado",
        "aji+amarillo",
        "papa",
        "quinoa",
        "causa",
        "anticucho",
        "pollo+a+la+brasa",
    ]
    
    headers = {"User-Agent": "MealMatch-Peru/1.0 (contacto@mealmatch.pe)"}
    base_url = "https://world.openfoodfacts.org/cgi/search.pl"
    
    for term in search_terms:
        for page in range(1, min(max_pages + 1, 4)):
            params = {
                "search_terms": term,
                "search_simple": 1,
                "action": "process",
                "json": 1,
                "page": page,
                "page_size": page_size,
            }
            
            try:
                response = requests.get(base_url, params=params, headers=headers, timeout=20)
                if response.status_code != 200:
                    print(f"[OpenFoodFacts] HTTP {response.status_code} para '{term}' p{page}")
                    break
                
                data = response.json()
                products = data.get("products", [])
                
                if not products:
                    break
                
                # Filtrar productos peruanos
                peruvian_products = []
                for p in products:
                    if _is_peruvian_product(p):
                        peruvian_products.append(p)
                
                # Evitar duplicados
                existing_codes = {p["_id"] for p in all_products}
                new_products = [p for p in peruvian_products if p["_id"] not in existing_codes]
                all_products.extend(new_products)
                
                print(f"[OpenFoodFacts] '{term}' p{page}: {len(products)} total, {len(peruvian_products)} peruanos, +{len(new_products)} nuevos")
                
                if len(products) < page_size:
                    break
                    
            except Exception as e:
                print(f"[OpenFoodFacts] Error en '{term}' p{page}: {e}")
                break
    
    print(f"[OpenFoodFacts] Total productos peruanos obtenidos: {len(all_products)}")
    return all_products


def _is_peruvian_product(product: dict) -> bool:
    """
    Determina si un producto de OpenFoodFacts es peruano.
    Busca en múltiples campos del producto.
    """
    # Campos a revisar
    name = (product.get("product_name") or "").lower()
    categories = (product.get("categories") or "").lower()
    countries = (product.get("countries") or "").lower()
    purchase_places = (product.get("purchase_places") or "").lower()
    stores = (product.get("stores") or "").lower()
    
    # Palabras clave que indican Perú
    peruvian_indicators = [
        "peru", "perú", "peruvian",
        "ají", "aji", "rocoto", "muña",
        "papa amarilla", "papa nativa",
        "quinoa", "kiwicha", "cañihua",
        "ceviche", "causa", "lomo saltado",
        "anticucho", "pollo a la brasa",
        "pisco", "chicha", "cancha",
        "choclo", "frejol", "canchita",
        "lima", "costa", "sierra", "selva",
    ]
    
    combined = f"{name} {categories} {countries} {purchase_places} {stores}"
    
    return any(indicator in combined for indicator in peruvian_indicators)


# ──────────────────────────────────────────────────────────────
# NORMALIZACIÓN Y TRANSFORMACIÓN
# ──────────────────────────────────────────────────────────────

def _normalize_ingredient_text(text: str) -> list:
    """
    Convierte el texto crudo de ingredientes de OFF a lista limpia.
    OFF devuelve: "ingrediente1, ingrediente2 (subingrediente)..."
    """
    if not text:
        return []
    
    # Separar por comas, luego por paréntesis y guiones
    parts = re.split(r'[,;]', text)
    cleaned = []
    for part in parts:
        # Quitar cantidades entre paréntesis: "(500mg)" → ""
        part = re.sub(r'\([^)]*\)', '', part)
        # Quitar porcentajes: "5%" → ""
        part = re.sub(r'\d+%', '', part)
        # Quitar números iniciales: "100g de" → "de"
        part = re.sub(r'^\d+[\.,]?\d*\s*(g|kg|mg|ml|l|unidades?|ud|piezas?|cucharaditas?|cdas?|tazas?)\s*(de\s*)?', '', part, flags=re.IGNORECASE)
        # Quitar guiones y asteriscos decorativos
        part = part.replace('*', '').replace('-', '').replace('_', '').strip()
        
        if part and len(part) > 1:
            cleaned.append(part)
    
    return cleaned


def _extract_nutriments(product: dict) -> dict:
    """Extrae información nutricional relevante del producto."""
    nutriments = product.get("nutriments", {})
    
    result = {}
    mapping = {
        "calories": ["energy-kcal_100g", "energy-kcal", "calories_100g", "energy"],
        "protein": ["proteins_100g", "proteins"],
        "carbs": ["carbohydrates_100g", "carbohydrates"],
        "fat": ["fat_100g", "fat"],
        "fiber": ["fiber_100g", "fiber"],
        "sodium": ["sodium_100g", "salt_100g"],
    }
    
    for key, possible_fields in mapping.items():
        for field in possible_fields:
            value = nutriments.get(field)
            if value is not None:
                try:
                    result[key] = round(float(value), 1)
                except (TypeError, ValueError):
                    pass
                break
    
    return result


def _infer_difficulty(ingredients_count: int) -> str:
    """Infiere dificultad basada en cantidad de ingredientes."""
    if ingredients_count <= 4:
        return "Fácil"
    elif ingredients_count <= 8:
        return "Media"
    else:
        return "Difícil"


def transform_off_product_to_recipe(product: dict) -> dict | None:
    """
    Transforma un producto de OpenFoodFacts a formato Recipe.
    Solo procesa productos que parecen ser peruanos o tienen ingredientes válidos.
    Devuelve None si no tiene datos mínimos.
    """
    name = (
        product.get("product_name_es") or 
        product.get("product_name") or 
        product.get("product_name_en") or
        ""
    ).strip()
    
    if not name:
        return None
    
    # Filtrar productos que claramente no son alimentos
    non_food_keywords = ["shampoo", "jabón", "detergente", "clean", "soap", "electronic", "battery"]
    name_lower = name.lower()
    if any(kw in name_lower for kw in non_food_keywords):
        return None
    
    ingredients_text = product.get("ingredients_text", "")
    ingredients_list = _normalize_ingredient_text(ingredients_text)
    
    # Fallback: usar la lista estructurada de OFF si existe
    if not ingredients_list and product.get("ingredients"):
        try:
            structured = product["ingredients"]
            ingredients_list = [
                ing.get("text", "").strip() 
                for ing in structured 
                if ing.get("text", "").strip()
            ]
        except (TypeError, AttributeError):
            pass
    
    if not ingredients_list:
        # Si no tenemos ingredientes, al menos guardamos el texto crudo
        ingredients_list = [ingredients_text] if ingredients_text else ["Ver etiqueta del producto"]
    
    # Determinar si es peruano basándose en múltiples campos
    categories = product.get("categories", "") or ""
    countries = product.get("countries", "") or ""
    purchase_places = product.get("purchase_places", "") or ""
    stores = product.get("stores", "") or ""
    
    # Palabras clave peruanas
    peruvian_keywords = [
        "ají", "papa", "quinoa", "kiwicha", "cañihua", "rocoto",
        "lima", "perú", "peruvian", "ceviche", "causa", "lomo",
        "sec", "anticucho", "pisco", "chicha", "cancha", "choclo",
        "ají amarillo", "ají panca", "rocoto", "muña"
    ]
    
    combined_text = f"{name} {categories} {countries} {purchase_places} {stores}".lower()
    is_peruvian = any(kw in combined_text for kw in peruvian_keywords)
    
    region = "Perú" if is_peruvian else "Internacional"
    
    # Generar tags
    tags = ["openfoodfacts", "peru"]
    if is_peruvian:
        tags.append("tipico_peruano")
    
    # Imagen
    image_url = product.get("image_url", "")
    if image_url and not image_url.startswith("http"):
        image_url = "https://" + image_url
    
    return {
        "name": name,
        "description": ingredients_text or f"Producto registrado en OpenFoodFacts. Categorías: {categories}",
        "ingredients": json.dumps(ingredients_list),
        "steps": json.dumps([]),  # OFF no provee pasos de preparación
        "prep_time_minutes": None,
        "difficulty": _infer_difficulty(len(ingredients_list)),
        "region": region,
        "image_url": image_url,
        "tags": json.dumps(tags),
        "nutritional_info": json.dumps(_extract_nutriments(product)),
        "servings": 1,
        "is_local": is_peruvian,
        "source_dataset": "openfoodfacts",
    }


# ──────────────────────────────────────────────────────────────
# GUARDADO EN BASE DE DATOS
# ──────────────────────────────────────────────────────────────

def save_recipes_to_db(db: Session, recipes_data: list, update_existing: bool = False) -> int:
    """
    Guarda las recetas transformadas en la base de datos.
    
    Parámetros:
        db: sesión de SQLAlchemy
        recipes_data: lista de dicts (formato Recipe)
        update_existing: si True, actualiza registros existentes por nombre
    
    Retorna:
        Cantidad de registros nuevos insertados.
    """
    added = 0
    updated = 0
    
    for data in recipes_data:
        existing = db.query(Recipe).filter(Recipe.name == data["name"]).first()
        
        if existing:
            if update_existing:
                for key, value in data.items():
                    setattr(existing, key, value)
                updated += 1
            continue
        
        recipe = Recipe(**data)
        db.add(recipe)
        added += 1
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[OpenFoodFacts] Error guardando en BD: {e}")
        raise
    
    print(f"[OpenFoodFacts] Guardados: {added} nuevos, {updated} actualizados.")
    return added


# ──────────────────────────────────────────────────────────────
# FUNCIÓN ORQUESTADORA
# ──────────────────────────────────────────────────────────────

def ingest_openfoodfacts_peru(
    db: Session,
    max_pages: int = 20,
    page_size: int = 50,
    update_existing: bool = False
) -> dict:
    """
    Ingesta completa: descarga, transforma y guarda productos de Perú.
    
    Uso desde el endpoint /admin/ingest o desde seed.py
    
    Retorna:
        {
            "source": "openfoodfacts",
            "downloaded": int,
            "transformed": int,
            "inserted": int,
            "updated": int,
            "skipped": int
        }
    """
    print("═" * 60)
    print("[INGESTA] Iniciando OpenFoodFacts Perú...")
    print("═" * 60)
    
    # 1. Descargar productos crudos
    raw_products = fetch_openfoodfacts_peru(max_pages=max_pages, page_size=page_size)
    downloaded = len(raw_products)
    print(f"[INGESTA] Descargados {downloaded} productos crutos.")
    
    # 2. Transformar a formato receta
    transformed_recipes = []
    skipped = 0
    
    for product in raw_products:
        recipe_data = transform_off_product_to_recipe(product)
        if recipe_data:
            transformed_recipes.append(recipe_data)
        else:
            skipped += 1
    
    transformed = len(transformed_recipes)
    print(f"[INGESTA] Transformados {transformed} productos. Omitidos: {skipped}")
    
    # 3. Guardar en BD
    inserted = save_recipes_to_db(db, transformed_recipes, update_existing=update_existing)
    
    # 4. Estadísticas finales
    total_in_db = db.query(Recipe).filter(Recipe.source_dataset == "openfoodfacts").count()
    
    result = {
        "source": "openfoodfacts_peru",
        "downloaded": downloaded,
        "transformed": transformed,
        "inserted": inserted,
        "updated": updated if update_existing else 0,
        "skipped": skipped,
        "total_in_db": total_in_db,
    }
    
    print("═" * 60)
    print(f"[INGESTA] Completado: {json.dumps(result, indent=2)}")
    print("═" * 60)
    
    return result


# ──────────────────────────────────────────────────────────────
# EJECUCIÓN DIRECTA (para pruebas)
# ──────────────────────────────────────────────────────────────
# CARGA DE RECETAS PERUANAS TRADICIONALES (JSON LOCAL)
# ──────────────────────────────────────────────────────────────

def load_peruvian_recipes_json(json_path: str = None) -> list:
    """
    Carga recetas peruanas tradicionales desde un archivo JSON local.
    
    Ruta por defecto: backend/data/peruvian_recipes.json
    """
    if json_path is None:
        # Subir dos niveles desde app/services/ hasta backend/, luego entrar a data/
        json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "peruvian_recipes.json")
    
    if not os.path.exists(json_path):
        print(f"[RecetasPeruanas] Archivo no encontrado: {json_path}")
        return []
    
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        recipes = []
        for r in data.get("recipes", []):
            # Validar campos mínimos
            if not r.get("name") or not r.get("ingredients"):
                continue
            
            # Normalizar a formato Recipe
            recipe_data = {
                "name": r["name"],
                "description": r.get("description", ""),
                "ingredients": json.dumps(r["ingredients"]),
                "steps": json.dumps(r.get("steps", [])),
                "prep_time_minutes": r.get("prep_time_minutes"),
                "difficulty": r.get("difficulty", "Media"),
                "region": r.get("region", "Nacional"),
                "image_url": r.get("image_url", ""),
                "tags": json.dumps(r.get("tags", [])),
                "nutritional_info": json.dumps(r.get("nutritional_info", {})),
                "servings": r.get("servings", 1),
                "is_local": True,
                "source_dataset": "peruvian_traditional",
            }
            recipes.append(recipe_data)
        
        print(f"[RecetasPeruanas] Cargadas {len(recipes)} recetas desde JSON.")
        return recipes
        
    except Exception as e:
        print(f"[RecetasPeruanas] Error cargando JSON: {e}")
        return []


# ──────────────────────────────────────────────────────────────
# ORQUESTADOR ACTUALIZADO
# ──────────────────────────────────────────────────────────────

def ingest_all_sources(db: Session, max_recipes: int = 500):
    """
    Ejecuta todas las fuentes de ingesta y guarda en BD.
    Prioridad: Recetas peruanas JSON > OpenFoodFacts
    """
    all_recipes = []

    # 1. Recetas peruanas tradicionales (JSON local)
    print("═" * 60)
    print("[INGESTA] Cargando recetas peruanas tradicionales...")
    peruvian_recipes = load_peruvian_recipes_json()
    all_recipes.extend(peruvian_recipes)
    
    # 2. OpenFoodFacts Perú
    print("\n[INGESTA] Iniciando OpenFoodFacts Perú...")
    off_products = fetch_openfoodfacts_peru(max_pages=5, page_size=20)
    for prod in off_products:
        name = prod.get("product_name", "").strip()
        if not name:
            continue
        recipe = {
            "name": name,
            "description": prod.get("ingredients_text", ""),
            "ingredients": json.dumps(prod.get("ingredients", [])),
            "steps": json.dumps([]),
            "prep_time_minutes": None,
            "difficulty": "Variable",
            "region": "Perú",
            "image_url": prod.get("image_url", ""),
            "tags": json.dumps(["openfoodfacts", "peru"]),
            "nutritional_info": json.dumps(prod.get("nutriments", {})),
            "servings": 1,
            "is_local": True,
            "source_dataset": "openfoodfacts"
        }
        all_recipes.append(recipe)

    # Guardar en BD (evitar duplicados por nombre)
    existing_names = {r[0] for r in db.query(Recipe.name).all()}
    added = 0
    for rec in all_recipes:
        if rec["name"] not in existing_names:
            recipe = Recipe(**rec)
            db.add(recipe)
            existing_names.add(rec["name"])
            added += 1
    db.commit()
    
    print("═" * 60)
    print(f"[INGESTA] Completado. Recetas nuevas: {added}")
    print(f"[INGESTA] Total en BD: {db.query(Recipe).count()}")
    print("═" * 60)


if __name__ == "__main__":
    import sys
    import os
    
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        result = ingest_openfoodfacts_peru(db, max_pages=5, page_size=20)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    finally:
        db.close()
