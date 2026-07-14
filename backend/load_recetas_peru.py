import csv
import hashlib
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import SessionLocal, Base, engine
from app.models import Recipe, DatasetMeta

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "Recetas_Peru_200.csv")
SOURCE_DATASET = "Recetas_Peru_200"
SIGNATURE_KEY = "recetas_peru_200_signature"


def _csv_signature(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


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


def load_database(force: bool = False):
    if not os.path.exists(CSV_PATH):
        print(f"❌ No se encontró el dataset: {CSV_PATH}")
        return

    Base.metadata.create_all(bind=engine)
    signature = _csv_signature(CSV_PATH)
    db: Session = SessionLocal()
    try:
        meta = db.query(DatasetMeta).filter(DatasetMeta.key == SIGNATURE_KEY).first()
        stored_signature = meta.value if meta else None
        has_recipes = db.query(Recipe).count() > 0
        # Red de seguridad: si hay datos viejos con ingredientes unidos (" y "), recargar.
        stale_joined = db.query(Recipe).filter(Recipe.ingredients.like("% y %")).first() is not None

        if not force and stored_signature == signature and has_recipes and not stale_joined:
            print("✅ Recetas_Peru_200 ya está actualizado (sin cambios).")
            return

        # Recarga: vacía la tabla y vuelve a insertar desde el CSV
        db.query(Recipe).delete()
        db.commit()

        added = 0
        with open(CSV_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row.get("recipe_title") or not row.get("ingredients"):
                    continue
                db.add(_row_to_recipe(row))
                added += 1

        if meta is None:
            meta = DatasetMeta(key=SIGNATURE_KEY)
            db.add(meta)
        meta.value = signature
        db.commit()
        print(f"✅ Recetas_Peru_200 recargado: {added} recetas.")
    except Exception as e:
        print(f"❌ Error cargando Recetas_Peru_200: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    load_database()

