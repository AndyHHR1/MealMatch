import json
import os


def load_peruvian_recipes_json(json_path: str = None) -> list:
    """
    Carga recetas peruanas tradicionales desde un archivo JSON local.

    Ruta por defecto: backend/data/peruvian_recipes.json
    """
    if json_path is None:
        json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "peruvian_recipes.json")

    if not os.path.exists(json_path):
        print(f"[RecetasPeruanas] Archivo no encontrado: {json_path}")
        return []

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        recipes = []
        for r in data.get("recipes", []):
            if not r.get("name") or not r.get("ingredients"):
                continue

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


