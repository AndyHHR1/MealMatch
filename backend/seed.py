import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Recipe

# Si querés las recetas de ejemplo clasicas, ejecutá: python3 seed.py --seed
# Por defecto, carga AMBAS

USE_SEED = "--seed" in sys.argv or "--only" not in sys.argv

SAMPLE_RECIPES = [
    {
        "name": "Seco de Pollo",
        "description": "Plato bandera de la costa norte, guiso de pollo con cilantro y cerveza.",
        "ingredients": json.dumps(["pollo", "cilantro", "cebolla", "tomate", "aji amarillo", "cerveza", "zanahoria", "frejol"]),
        "steps": json.dumps(["Licuar cilantro, cebolla, aji y tomate.", "Freir el pollo y agregar la mezcla.", "Cocinar a fuego lento con cerveza."]),
        "prep_time_minutes": 60,
        "difficulty": "Media",
        "region": "Costa",
        "image_url": "https://placehold.co/600x400?text=Seco+de+Pollo",
        "tags": json.dumps(["guiso", "cerveza", "almuerzo"]),
        "nutritional_info": json.dumps({"calories": 520, "protein": 38, "carbs": 18, "fat": 32}),
        "servings": 4,
        "is_local": True,
        "source_dataset": "seed",
    },
    {
        "name": "Lomo Saltado",
        "description": "Clásico salteado de lomo con cebolla, tomate y papas fritas.",
        "ingredients": json.dumps(["lomo", "cebolla", "tomate", "papa", "sillao", "aji panca", "aceite"]),
        "steps": json.dumps(["Saltear la carne a fuego alto.", "Agregar cebolla y tomate.", "Mezclar con papas fritas y sillao."]),
        "prep_time_minutes": 35,
        "difficulty": "Media",
        "region": "Nacional",
        "image_url": "https://placehold.co/600x400?text=Lomo+Saltado",
        "tags": json.dumps(["salteado", "carne", "clasico", "almuerzo"]),
        "nutritional_info": json.dumps({"calories": 650, "protein": 45, "carbs": 35, "fat": 35}),
        "servings": 2,
        "is_local": True,
        "source_dataset": "seed",
    },
    {
        "name": "Arroz con Pollo",
        "description": "Arroz teñido con aji amarillo y pollo desmenuzado.",
        "ingredients": json.dumps(["pollo", "arroz", "aji amarillo", "cebolla", "zanahoria", "frejol", "culantro", "limon"]),
        "steps": json.dumps(["Preparar el aderezo.", "Cocinar el pollo.", "Agregar el arroz y hervir."]),
        "prep_time_minutes": 50,
        "difficulty": "Media",
        "region": "Costa",
        "image_url": "https://placehold.co/600x400?text=Arroz+con+Pollo",
        "tags": json.dumps(["arroz", "pollo", "almuerzo"]),
        "nutritional_info": json.dumps({"calories": 580, "protein": 35, "carbs": 55, "fat": 22}),
        "servings": 4,
        "is_local": True,
        "source_dataset": "seed",
    },
    {
        "name": "Papa a la Huancaina",
        "description": "Papas hervidas bañadas en salsa de aji amarillo y queso.",
        "ingredients": json.dumps(["papa", "aji amarillo", "queso", "leche", "galleta", "cebolla", "aceite", "sal"]),
        "steps": json.dumps(["Hervir las papas.", "Licuar la salsa.", "Bañar las papas y decorar."]),
        "prep_time_minutes": 30,
        "difficulty": "Fácil",
        "region": "Sierra",
        "image_url": "https://placehold.co/600x400?text=Papa+a+la+Huancaina",
        "tags": json.dumps(["papa", "salsa", "entrada"]),
        "nutritional_info": json.dumps({"calories": 350, "protein": 12, "carbs": 38, "fat": 18}),
        "servings": 4,
        "is_local": True,
        "source_dataset": "seed",
    },
    {
        "name": "Ají de Gallina",
        "description": "Crema de ají amarillo con gallina desmenuzada y pan.",
        "ingredients": json.dumps(["gallina", "aji amarillo", "cebolla", "pan", "leche", "queso", "nuez", "papas"]),
        "steps": json.dumps(["Desmenuzar la gallina.", "Preparar la crema de ají.", "Servir con papas hervidas."]),
        "prep_time_minutes": 70,
        "difficulty": "Media",
        "region": "Costa",
        "image_url": "https://placehold.co/600x400?text=Aji+de+Gallina",
        "tags": json.dumps(["guiso", "aji", "almuerzo"]),
        "nutritional_info": json.dumps({"calories": 540, "protein": 32, "carbs": 25, "fat": 32}),
        "servings": 4,
        "is_local": True,
        "source_dataset": "seed",
    },
    {
        "name": "Ceviche",
        "description": "Pescado fresco marinado en limón con cebolla y ají.",
        "ingredients": json.dumps(["pescado", "limon", "cebolla", "aji limo", "cilantro", "sal", "camote", "choclo"]),
        "steps": json.dumps(["Cortar el pescado.", "Marinar en limón.", "Mezclar con cebolla y ají."]),
        "prep_time_minutes": 20,
        "difficulty": "Media",
        "region": "Costa",
        "image_url": "https://placehold.co/600x400?text=Ceviche",
        "tags": json.dumps(["pescado", "mar", "frio"]),
        "nutritional_info": json.dumps({"calories": 280, "protein": 32, "carbs": 20, "fat": 10}),
        "servings": 2,
        "is_local": True,
        "source_dataset": "seed",
    },
    {
        "name": "Anticuchos",
        "description": "Brochetas de corazón marinado a la parrilla.",
        "ingredients": json.dumps(["corazon", "aji panca", "comino", "oregano", "vinagre", "sal", "pimienta", "limon"]),
        "steps": json.dumps(["Marinar la carne.", "Armar brochetas.", "Asar a la parrilla."]),
        "prep_time_minutes": 50,
        "difficulty": "Media",
        "region": "Nacional",
        "image_url": "https://placehold.co/600x400?text=Anticuchos",
        "tags": json.dumps(["parrilla", "corazon", "callejero"]),
        "nutritional_info": json.dumps({"calories": 380, "protein": 28, "carbs": 5, "fat": 24}),
        "servings": 4,
        "is_local": True,
        "source_dataset": "seed",
    },
    {
        "name": "Pollo a la Brasa",
        "description": "Pollo entero cocido en horno a brasa con especias.",
        "ingredients": json.dumps(["pollo", "sal", "pimienta", "comino", "ajo", "vinagre", "papas", "ensalada"]),
        "steps": json.dumps(["Marinar el pollo.", "Hornear a alta temperatura.", "Servir con papas y ensalada."]),
        "prep_time_minutes": 90,
        "difficulty": "Media",
        "region": "Nacional",
        "image_url": "https://placehold.co/600x400?text=Pollo+a+la+Brasa",
        "tags": json.dumps(["pollo", "horno", "domingo"]),
        "nutritional_info": json.dumps({"calories": 720, "protein": 48, "carbs": 30, "fat": 40}),
        "servings": 4,
        "is_local": True,
        "source_dataset": "seed",
    },
    {
        "name": "Causa Limeña",
        "description": "Pastel de papa amarilla relleno de pollo o atún.",
        "ingredients": json.dumps(["papa", "aji amarillo", "limon", "pollo", "mayonesa", "palta", "huevo"]),
        "steps": json.dumps(["Hacer puré de papa.", "Preparar el relleno.", "Intercalar capas y decorar con palta."]),
        "prep_time_minutes": 45,
        "difficulty": "Media",
        "region": "Costa",
        "image_url": "https://placehold.co/600x400?text=Causa+Limenya",
        "tags": json.dumps(["papa", "entrada", "frio"]),
        "nutritional_info": json.dumps({"calories": 420, "protein": 20, "carbs": 45, "fat": 20}),
        "servings": 6,
        "is_local": True,
        "source_dataset": "seed",
    },
]

def seed_database():
    from app.services.ingestion_service import load_peruvian_recipes_json
    
    db: Session = SessionLocal()
    try:
        if USE_SEED:
            existing_count = db.query(Recipe).count()
            if existing_count == 0:
                recipes_data = load_peruvian_recipes_json()
                if recipes_data:
                    for recipe_data in recipes_data:
                        db.add(Recipe(**recipe_data))
                    db.commit()
                    print(f"✅ Seed: {len(recipes_data)} recetas peruanas tradicionales insertadas.")
                else:
                    print("⚠️  No se pudieron cargar recetas peruanas del JSON.")
            else:
                print(f"⚠️  La base ya tiene {existing_count} recetas. Seed omitido.")
        
        total = db.query(Recipe).count()
        print(f"\n📊 Total recetas en BD: {total}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
