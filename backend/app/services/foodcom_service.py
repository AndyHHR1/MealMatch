import csv
import json
import re
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Recipe

# ──────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ──────────────────────────────────────────────────────────────
# Subir 2 niveles desde app/services/ hasta backend/, luego a data/
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
CSV_PATH = os.path.join(DATA_DIR, "recipes.csv")

# Términos de búsqueda para recetas peruanas
PERuvian_SEARCH_TERMS = [
    'peruvian', 'peru', 'ceviche', 'lomo saltado', 'causa', 
    'anticucho', 'rocoto', 'huancaina', 'brasa', 'seco',
    'arroz con pollo', 'tacu tacu', 'humita', 'juane', 'ocopa',
    'aguadito', 'chicharrones', 'papa a la', 'solterito',
    'pepián', 'carapulcra', 'escabeche', 'bistec a la criolla',
    'cuy', 'pachamanca', 'oca', 'caldo de gallina',
    'monsefú', 'manchape', 'locro', 'papa rellena',
]

# ──────────────────────────────────────────────────────────────
# PARSERS
# ──────────────────────────────────────────────────────────────

def parse_r_vector(text: str) -> list:
    """Parsea formato R: c("item1", "item2", ...) a lista Python."""
    if not text or text == 'NA':
        return []
    # Remover el prefijo c( y el sufijo )
    text = text.strip()
    if text.startswith('c('):
        text = text[2:]
    if text.endswith(')'):
        text = text[:-1]
    
    # Parsear comillas dobles
    items = re.findall(r'"([^"]*)"', text)
    if not items:
        # Fallback: split por coma
        items = [x.strip().strip('"') for x in text.split(',') if x.strip()]
    
    return [item.strip() for item in items if item.strip()]


def is_peruvian_recipe(row: dict) -> bool:
    """Determina si una receta es peruana basándose en múltiples campos."""
    name = row.get('Name', '').lower()
    description = row.get('Description', '').lower()
    keywords = row.get('Keywords', '').lower()
    category = row.get('RecipeCategory', '').lower()
    
    combined = f"{name} {description} {keywords} {category}"
    
    return any(term in combined for term in PERuvian_SEARCH_TERMS)


def clean_ingredients(ingredients: list) -> list:
    """Limpia lista de ingredientes."""
    cleaned = []
    for ing in ingredients:
        ing = ing.strip()
        if ing and len(ing) > 1:
            # Remover cantidades al inicio (opcional)
            cleaned.append(ing)
    return cleaned[:20]  # Limitar a 20 ingredientes


def clean_steps(steps: list) -> list:
    """Limpia lista de pasos."""
    cleaned = []
    for step in steps:
        step = step.strip()
        if step and len(step) > 10:
            cleaned.append(step)
    return cleaned[:15]  # Limitar a 15 pasos


def transform_row_to_recipe(row: dict) -> dict | None:
    """Transforma una fila del CSV a formato Recipe."""
    if not is_peruvian_recipe(row):
        return None
    
    ingredients = parse_r_vector(row.get('RecipeIngredientParts', ''))
    steps = parse_r_vector(row.get('RecipeInstructions', ''))
    
    if not ingredients:
        return None
    
    name = row.get('Name', '').strip()
    if not name:
        return None
    
    # Limpiar HTML entities en el nombre
    name = name.replace('&amp;', '&').replace('&nbsp;', ' ')
    
    # Extraer nutritional info
    nutritional_info = {}
    try:
        nutritional_info['calories'] = float(row.get('Calories', 0)) if row.get('Calories') else None
        nutritional_info['protein'] = float(row.get('ProteinContent', 0)) if row.get('ProteinContent') else None
        nutritional_info['carbs'] = float(row.get('CarbohydrateContent', 0)) if row.get('CarbohydrateContent') else None
        nutritional_info['fat'] = float(row.get('FatContent', 0)) if row.get('FatContent') else None
    except (ValueError, TypeError):
        pass
    
    # Limpiar valores None
    nutritional_info = {k: v for k, v in nutritional_info.items() if v is not None}
    
    return {
        "name": name,
        "description": row.get('Description', '') or f"Receta peruana: {name}",
        "ingredients": json.dumps(clean_ingredients(ingredients)),
        "steps": json.dumps(clean_steps(steps)),
        "prep_time_minutes": int(row.get('PrepTime', 0)) if row.get('PrepTime') and row.get('PrepTime').isdigit() else None,
        "difficulty": "Media",
        "region": "Perú",
        "image_url": "",
        "tags": json.dumps(["foodcom", "peru", "scraped"]),
        "nutritional_info": json.dumps(nutritional_info),
        "servings": int(row.get('RecipeServings', 1)) if row.get('RecipeServings') and str(row.get('RecipeServings')).isdigit() else 1,
        "is_local": True,
        "source_dataset": "foodcom_peruvian",
    }


# ──────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────

def load_peruvian_recipes_from_foodcom(limit: int = None):
    """Carga recetas peruanas desde Food.com CSV."""
    if not os.path.exists(CSV_PATH):
        print(f"❌ Archivo no encontrado: {CSV_PATH}")
        return
    
    db: Session = SessionLocal()
    try:
        print("═" * 60)
        print("[FoodCom] Cargando recetas peruanas desde Food.com...")
        print("═" * 60)
        
        added = 0
        skipped = 0
        total_rows = 0
        
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                total_rows += 1
                
                if total_rows % 50000 == 0:
                    print(f"[FoodCom] Procesadas {total_rows} filas... +{added} recetas peruanas")
                
                recipe_data = transform_row_to_recipe(row)
                if recipe_data is None:
                    skipped += 1
                    continue
                
                # Verificar duplicados
                existing = db.query(Recipe).filter(Recipe.name == recipe_data["name"]).first()
                if existing:
                    skipped += 1
                    continue
                
                recipe = Recipe(**recipe_data)
                db.add(recipe)
                added += 1
                
                # Commit en lotes de 100
                if added % 100 == 0:
                    db.commit()
                
                # Límite opcional
                if limit and added >= limit:
                    break
        
        db.commit()
        
        print("═" * 60)
        print(f"[FoodCom] Completado:")
        print(f"  Filas procesadas: {total_rows}")
        print(f"  Recetas nuevas: {added}")
        print(f"  Omitidas: {skipped}")
        print(f"  Total en BD: {db.query(Recipe).count()}")
        print("═" * 60)
        
        return added
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    load_peruvian_recipes_from_foodcom()
