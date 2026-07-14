from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import engine, Base
from app.routes import recipes
from app.services.recipe_service import RecipeService

Base.metadata.create_all(bind=engine)

CATEGORIZED_INGREDIENTS_CACHE: dict[str, list[str]] | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global CATEGORIZED_INGREDIENTS_CACHE
    from app.database import SessionLocal
    from app.models import Recipe
    db = SessionLocal()
    try:
        # Carga/recarga automática del dataset según su firma (Recetas_Peru_200)
        from load_recetas_peru import load_database
        load_database()
        CATEGORIZED_INGREDIENTS_CACHE = RecipeService(db).get_ingredients_categorized()
    finally:
        db.close()
    yield


app = FastAPI(
    title="MealMatch Perú API",
    description="API para búsqueda inversa de recetas peruanas",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recipes.router)


@app.get("/admin/ingest/stats")
def ingest_stats():
    """Devuelve estadísticas de la base de datos."""
    from app.database import SessionLocal
    from app.models import Recipe
    db = SessionLocal()
    try:
        total = db.query(Recipe).count()
        by_source = {}
        for r in db.query(Recipe.source_dataset, Recipe.id).all():
            src = r[0] or "unknown"
            by_source[src] = by_source.get(src, 0) + 1
        return {"total_recipes": total, "by_source": by_source}
    finally:
        db.close()


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "mealmatch-api"}


@app.get("/")
def root():
    return {"message": "Bienvenido a MealMatch Perú API"}
