import csv
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import SessionLocal, Base, engine
from app.models import Recipe

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "Recetas_Peru_200.csv")
SOURCE_DATASET = "Recetas_Peru_200"


def _row_to_recipe(row: dict) -> Recipe:
    return Recipe(
        name=row["recipe_title"].strip(),
        description=(row.get("description") or None),
        ingredients=row["ingredients"],
        steps=(row.get("directions") or None),
        prep_time_minutes=None,
        difficulty=None,
        region=(row.get("subcategory") or None),
        image_url=None,
        tags=json.dumps([row["category"], row["subcategory"]]),
        is_local=True,
        nutritional_info=None,
        servings=None,
        source_dataset=SOURCE_DATASET,
    )


def load_database():
    if not os.path.exists(CSV_PATH):
        print(f"❌ No se encontró el dataset: {CSV_PATH}")
        return

    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        if db.query(Recipe).count() > 0:
            print("⚠️  La base ya tiene recetas. Carga de Recetas_Peru_200 omitida.")
            return

        added = 0
        with open(CSV_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row.get("recipe_title") or not row.get("ingredients"):
                    continue
                db.add(_row_to_recipe(row))
                added += 1

        db.commit()
        print(f"✅ Recetas_Peru_200: {added} recetas insertadas.")
    except Exception as e:
        print(f"❌ Error cargando Recetas_Peru_200: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    load_database()
