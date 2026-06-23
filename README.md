# MealMatch Perú

MVP de aplicación web B2C Freemium de búsqueda inversa de recetas para estudiantes universitarios.

## Características
- Búsqueda de recetas por ingredientes
- Base de datos de recetas peruanas locales
- Frontend responsivo (móvil-first) con Tailwind CSS

## Stack Tecnológico

### Backend
- Python 3.11
- FastAPI
- SQLAlchemy (ORM)
- SQLite (base de datos)

### Frontend
- HTML5 + JavaScript
- Tailwind CSS (CDN)

## Estructura del Proyecto

```text
MealMatch/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # API principal
│   │   ├── models.py            # Modelos SQLAlchemy
│   │   ├── database.py          # Configuración de BD
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   └── recipes.py       # Endpoints de recetas
│   │   └── services/
│   │       ├── __init__.py
│   │       └── recipe_service.py # Lógica de negocio
│   ├── data/
│   │   └── recipes.json         # Datos crudos
│   ├── seed.py                  # Script de inicialización
│   ├── requirements.txt
│   └── Dockerfile
└── frontend/
    └── index.html               # Interfaz de usuario
```

## Instalación y Ejecución Local

### 1. Prerrequisitos
- Python 3.9+
- pip

### 2. Configurar Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
python seed.py
uvicorn app.main:app --reload --port 8000
```

La API estará disponible en: `http://localhost:8000`

Documentación interactiva (Swagger): `http://localhost:8000/docs`

### 3. Abrir Frontend

Simplemente abre `frontend/index.html` en tu navegador, o usa un servidor estático:

```bash
cd frontend
python -m http.server 3000
```

Luego visita: `http://localhost:3000`

## Endpoints

- `GET /` - Bienvenida
- `GET /health` - Health check
- `POST /recipes/match` - Buscar recetas por ingredientes
  - Query params: `ingredients` (lista), `limit` (opcional, default 10)
- `GET /recipes/search/{query}` - Buscar recetas por texto
- `GET /recipes/{recipe_id}` - Detalle de receta

## Datos

El proyecto incluye recetas de muestra peruanas iniciales. Para integrar fuentes externas:

- **OpenFoodFacts API**: Integrar para obtener productos locales del Perú
- **Kaggle Datasets**: Descargar y procesar dataset de recetas
- **Nutrition5k / USDA**: Enriquecer información nutricional

## Próximos Pasos (Post-MVP)

1. **Base de datos real**: Migrar de SQLite a PostgreSQL (AWS RDS)
2. **Autenticación**: Usuarios y favoritos (OAuth2 + JWT)
3. **Instrucciones detalladas**: PASO A PASO para cada receta con imágenes reales
4. **Almacenamiento**: S3 para imágenes, CDN para entrega
5. **IA / Recomendación**: Filtros colaborativos y ML
6. **Colaboración**: Compartir recetas en comunidad
7. **Carrito de compras**: Integración con tiendas locales

## Licencia
MIT
