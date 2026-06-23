from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.recipe_service import RecipeService
from typing import List

router = APIRouter(prefix="/recipes", tags=["recipes"])

@router.post("/match")
def match_recipes(
    ingredients: List[str] = Query(..., description="Lista de ingredientes separados por coma"),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    service = RecipeService(db)
    results = service.match_recipes_by_ingredients(ingredients, limit=limit)
    return {"results": results, "count": len(results)}

@router.get("/{recipe_id}")
def get_recipe_detail(recipe_id: int, db: Session = Depends(get_db)):
    service = RecipeService(db)
    recipe = service.get_recipe_by_id(recipe_id)
    if not recipe:
        return {"error": "Receta no encontrada"}, 404
    return recipe

@router.get("/search/{query}")
def search_recipes(
    query: str,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    service = RecipeService(db)
    results = service.search_recipes(query, limit=limit)
    return {"results": results, "count": len(results)}
