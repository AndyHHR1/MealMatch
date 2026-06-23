from typing import List, Dict, Any
import json
import re
from app.models import Recipe

def _normalize(ingredient: str) -> str:
    return re.sub(r"[^a-z0-9áéíóúñü\s]", "", ingredient.strip().lower()).strip()

class RecipeService:
    def __init__(self, db_session):
        self.db = db_session

    def match_recipes_by_ingredients(self, ingredients: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        if not ingredients:
            return []

        user_set = set(_normalize(i) for i in ingredients if i.strip())
        if not user_set:
            return []

        recipes = self.db.query(Recipe).all()
        scored: List[Dict[str, Any]] = []

        for recipe in recipes:
            recipe_ings = json.loads(recipe.ingredients)
            recipe_set = set(_normalize(i) for i in recipe_ings)

            matched_set = user_set & recipe_set
            missing_set = recipe_set - user_set

            matched_count = len(matched_set)
            missing_count = len(missing_set)
            recipe_total = len(recipe_set)
            user_total = len(user_set)

            if recipe_total == 0 or user_total == 0:
                continue

            coverage = matched_count / recipe_total
            match_ratio = matched_count / user_total
            missing_ratio = missing_count / recipe_total

            if coverage == 1.0:
                final_score = 100.0
            else:
                final_score = (coverage * 100) - (missing_ratio * 30)

            matched_list = sorted(matched_set)
            missing_list = sorted(missing_set)
            recipe_ings_normalized = sorted(recipe_set)

            scored.append({
                "id": recipe.id,
                "name": recipe.name,
                "description": recipe.description,
                "ingredients": recipe_ings,
                "prep_time_minutes": recipe.prep_time_minutes,
                "difficulty": recipe.difficulty,
                "region": recipe.region,
                "match_score": round(final_score, 1),
                "coverage": round(coverage * 100, 1),
                "matched_count": matched_count,
                "missing_count": missing_count,
                "matched_ingredients": matched_list,
                "missing_ingredients": missing_list,
                "image_url": recipe.image_url,
                "tags": json.loads(recipe.tags) if recipe.tags else [],
                "nutritional_info": json.loads(recipe.nutritional_info) if recipe.nutritional_info else {},
                "servings": recipe.servings,
            })

        scored.sort(key=lambda x: (x["match_score"], x["coverage"]), reverse=True)
        return scored[:limit]

    def get_recipe_by_id(self, recipe_id: int) -> Dict[str, Any] | None:
        recipe = self.db.query(Recipe).filter(Recipe.id == recipe_id).first()
        if not recipe:
            return None

        return {
            "id": recipe.id,
            "name": recipe.name,
            "description": recipe.description,
            "ingredients": json.loads(recipe.ingredients),
            "steps": json.loads(recipe.steps) if recipe.steps else [],
            "prep_time_minutes": recipe.prep_time_minutes,
            "difficulty": recipe.difficulty,
            "region": recipe.region,
            "image_url": recipe.image_url,
            "tags": json.loads(recipe.tags) if recipe.tags else [],
            "nutritional_info": json.loads(recipe.nutritional_info) if recipe.nutritional_info else {},
            "servings": recipe.servings,
        }

    def search_recipes(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        query_lower = query.lower()
        recipes = self.db.query(Recipe).all()
        results = []

        for recipe in recipes:
            if (query_lower in recipe.name.lower() or 
                query_lower in (recipe.description or "").lower() or
                (recipe.tags and query_lower in recipe.tags.lower())):
                results.append({
                    "id": recipe.id,
                    "name": recipe.name,
                    "description": recipe.description,
                    "ingredients": json.loads(recipe.ingredients),
                    "prep_time_minutes": recipe.prep_time_minutes,
                    "difficulty": recipe.difficulty,
                    "region": recipe.region,
                    "image_url": recipe.image_url,
                    "tags": json.loads(recipe.tags) if recipe.tags else [],
                    "nutritional_info": json.loads(recipe.nutritional_info) if recipe.nutritional_info else {},
                    "servings": recipe.servings,
                })

        return results[:limit]
