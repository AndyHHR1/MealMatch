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
    db = SessionLocal()
    try:
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

# ──────────────────────────────────────────────────────────────
# ENDPOINT DE INGESTA (solo desarrollo/admin)
# ──────────────────────────────────────────────────────────────

from pydantic import BaseModel, Field
from app.services.ingestion_service import ingest_openfoodfacts_peru


class IngestRequest(BaseModel):
    max_pages: int = Field(default=10, ge=1, le=100, description="Páginas de OpenFoodFacts a recorrer")
    page_size: int = Field(default=50, ge=1, le=100, description="Productos por página")
    update_existing: bool = Field(default=False, description="Actualizar productos existentes")


@app.post("/admin/ingest")
def trigger_ingest(req: IngestRequest):
    """
    Ingesta productos de OpenFoodFacts Perú a la base de datos.

    ⚠️ Solo para desarrollo. En producción, proteger con autenticación.
    """
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        result = ingest_openfoodfacts_peru(
            db,
            max_pages=req.max_pages,
            page_size=req.page_size,
            update_existing=req.update_existing
        )
        return {"status": "ok", "source": "openfoodfacts", "details": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


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
