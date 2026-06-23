from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routes import recipes

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MealMatch Perú API",
    description="API para búsqueda inversa de recetas peruanas",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recipes.router)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "mealmatch-api"}

@app.get("/")
def root():
    return {"message": "Bienvenido a MealMatch Perú API"}
