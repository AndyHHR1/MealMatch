from fastapi import APIRouter, Depends, Body, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.recipe_service import RecipeService
from typing import List

router = APIRouter(prefix="/recipes", tags=["recipes"])

@router.get("/search/{query}")
def search_recipes(
    query: str,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    service = RecipeService(db)
    results = service.search_recipes(query, limit=limit)
    return {"results": results, "count": len(results)}

@router.get("/{recipe_id}")
def get_recipe_detail(recipe_id: int, db: Session = Depends(get_db)):
    service = RecipeService(db)
    recipe = service.get_recipe_by_id(recipe_id)
    if not recipe:
        return {"error": "Receta no encontrada"}, 404
    return recipe

@router.post("/match")
def match_recipes(
    payload: dict = Body(..., example={"ingredients": ["pollo", "papa", "cebolla"], "limit": 10}),
    db: Session = Depends(get_db)
):
    ingredients = payload.get("ingredients", [])
    limit = payload.get("limit", 10)
    if not isinstance(ingredients, list) or len(ingredients) == 0:
        return {"results": [], "count": 0, "message": "Debe enviar un array de ingredientes."}
    if not isinstance(limit, int) or limit < 1 or limit > 50:
        limit = 10
    service = RecipeService(db)
    results = service.match_recipes_by_ingredients(ingredients, limit=limit)
    return {
        "results": results,
        "count": len(results),
        "meta": {
            "user_ingredients": ingredients,
            "limit": limit
        }
    }
