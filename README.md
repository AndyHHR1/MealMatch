# MealMatch Perú

MVP de aplicación web B2C Freemium de búsqueda inversa de recetas para estudiantes universitarios.

## Descripción

Los usuarios ingresan ingredientes sueltos que tienen en su refrigeradora y el sistema les devuelve recetas viables (enfoque local peruano) para evitar el desperdicio de comida.

## Stack Tecnológico

- **Backend:** Python 3.11 + FastAPI + SQLAlchemy
- **Frontend:** HTML5 + JavaScript + Tailwind CSS (CDN)
- **Base de Datos:** SQLite (desarrollo) / PostgreSQL (producción)
- **Analítica:** Mixpanel Browser SDK

## Estructura del Proyecto

```
MealMatch/
├── backend/
│   ├── app/
│   │   ├── main.py                    # API principal
│   │   ├── models.py                  # Modelos SQLAlchemy
│   │   ├── database.py                # Configuración BD
│   │   ├── routes/
│   │   │   └── recipes.py             # Endpoints
│   │   └── services/
│   │       └── recipe_service.py      # Lógica de matching
│   ├── data/
│   │   └── 1_Recipe_csv.csv           # Archive dataset (recetas peruanas)
│   ├── load_archive.py                # Carga de recetas desde CSV
│   ├── seed.py                        # Recetas de ejemplo
│   └── Dockerfile
├── frontend/
│   └── index.html                     # Interfaz de usuario
├── docker-compose.yml
└── README.md
```

## Instalación y Ejecución

### Desarrollo Local

**Backend:**
```bash
cd backend
./venv/bin/uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
python3 -m http.server 3000
```

Abrir http://localhost:3000

### Producción (Docker)

```bash
docker-compose up --build
```

La app estará disponible en http://localhost:3000

**Cargar recetas:**
```bash
docker exec mealmatch-backend-1 python3 /app/load_archive.py
```

## Endpoints

- `GET /` - Bienvenida
- `GET /health` - Health check
- `POST /recipes/match` - Buscar recetas por ingredientes
  ```json
  {
    "ingredients": ["pollo", "papa", "cebolla"],
    "limit": 10
  }
  ```
- `GET /recipes/search/{query}` - Buscar recetas por texto
- `GET /recipes/{id}` - Detalle de receta

## Datos

Fuentes utilizadas:

1. **Archive Dataset (Kaggle)** - 62,126 recetas, filtrado por términos peruanos
   - https://www.kaggle.com/datasets/prashantsingh001/recipes-dataset-64k-dishes
2. **Extended Recipes Dataset (Kaggle)** - Dataset extendido
   - https://www.kaggle.com/datasets/wafaaelhusseini/extended-recipes-dataset-64k-dishes
Para cargar datos:
```bash
docker exec mealmatch-backend-1 python3 /app/load_archive.py
```

## Tracking

Evento `recipe_steps_viewed` se dispara cuando:
- Usuario ingresa ≥ 3 ingredientes
- Hace clic en "Ver preparación"

Props: `user_id`, `ingredient_count`, `recipe_matched`, `time_to_match`

## Variables de Entorno

| Variable | Descripción | Default |
|----------|-------------|---------|
| `DATABASE_URL` | URL de base de datos | `sqlite:///./mealmatch.db` |
| `CORS_ORIGINS` | Orígenes permitidos | `*` |
| `MIXPANEL_TOKEN` | Token de Mixpanel | vacío |