import csv
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Recipe

DATA_DIR = "/home/non/MealMatch/backend/data"
CSV_PATH = os.path.join(DATA_DIR, "1_Recipe_csv.csv")

PERuvian_TERMS = [
    'ceviche peruano', 'lomo saltado', 'causa', 'anticucho', 'rocoto',
    'huancaina', 'pollo a la brasa', 'seco de', 'arroz con pollo',
    'tacu tacu', 'humita', 'juane', 'ocopa', 'chicharrones',
    'papa a la huancaína', 'pepián', 'carapulcra', 'escabeche',
    'bistec a la criolla', 'aguadito', 'peruvian', 'peru',
    'papa a la oca', 'solterito', 'caldo de gallina',
]

def is_peruvian(row):
    text = f"{row.get('recipe_title', '')} {row.get('description', '')} {row.get('category', '')}".lower()
    return any(term in text for term in PERuvian_TERMS)

def clean_recipe(row):
    ingredients = json.loads(row.get('ingredients', '[]') or '[]')
    directions = json.loads(row.get('directions', '[]') or '[]')
    
    if not ingredients or not directions:
        return None
    
    return {
        "name": row['recipe_title'].strip(),
        "description": row.get('description', '') or f"Receta: {row['recipe_title']}",
        "ingredients": json.dumps(ingredients),
        "steps": json.dumps(directions),
        "prep_time_minutes": None,
        "difficulty": "Media",
        "region": "Perú",
        "image_url": "",
        "tags": json.dumps(["archive_dataset", "peru"]),
        "nutritional_info": json.dumps({}),
        "servings": 1,
        "is_local": True,
        "source_dataset": "archive_recipes",
    }

def load_from_archive():
    if not os.path.exists(CSV_PATH):
        print(f"❌ No encontrado: {CSV_PATH}")
        return
    
    db = SessionLocal()
    try:
        print("═" * 60)
        print("[Archive] Cargando recetas peruanas desde 1_Recipe_csv.csv...")
        print("═" * 60)
        
        added = 0
        skipped = 0
        total = 0
        
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                total += 1
                if not is_peruvian(row):
                    skipped += 1
                    continue
                
                recipe_data = clean_recipe(row)
                if not recipe_data:
                    skipped += 1
                    continue
                
                existing = db.query(Recipe).filter(Recipe.name == recipe_data["name"]).first()
                if existing:
                    skipped += 1
                    continue
                
                db.add(Recipe(**recipe_data))
                added += 1
                
                if added % 200 == 0:
                    db.commit()
                    print(f"  ... +{added} recetas (procesadas {total})")
        
        db.commit()
        print(f"\n✅ Completado:")
        print(f"  Filas: {total}")
        print(f"  Nuevas: {added}")
        print(f"  Omitidas: {skipped}")
        print(f"  Total BD: {db.query(Recipe).count()}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    load_from_archive()
