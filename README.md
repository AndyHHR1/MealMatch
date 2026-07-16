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
│   │   └── Recetas_Peru_200.csv       # Dataset oficial (producción)
│   ├── load_recetas_peru.py           # Carga dataset Recetas_Peru_200
│   ├── load_archive.py                # Carga archive dataset (histórico)
│   ├── seed.py                        # Recetas de ejemplo
│   └── Dockerfile
├── frontend/
│   ├── index.html                     # Interfaz principal
│   └── recipe.html                    # Vista detallada "A cocinar"
├── docker-compose.yml
└── README.md
```

## Datos

El dataset oficial de producción es **`Recetas_Peru_200.csv`** (200 recetas peruanas), ubicado en `backend/data/`.

Columnas base: `recipe_title, category, subcategory, description, ingredients, directions, num_ingredients, num_steps`.
Columnas detalladas (solo usadas en **"A cocinar"**): `ingredientes_con_cantidades, preparacion_detallada`.
`ingredients` y `directions` vienen como arreglos JSON en texto. Las columnas detalladas también vienen como JSON.

- **Carga automática:** al arrancar el backend, si la base está vacía se inserta el dataset completo (`load_recetas_peru.py`). No requiere paso manual en Render.
- **Recarga automática:** al actualizar el CSV y hacer deploy, el backend detecta el cambio por firma SHA-256 y recarga las 200 recetas.
- **Carga manual** (desde `backend/`):
  ```bash
  python3 load_recetas_peru.py
  ```

Otras fuentes históricas (no usadas en producción):
1. **Archive Dataset (Kaggle)** - 62,126 recetas, filtrado por términos peruanos (`load_archive.py`)
2. **Extended Recipes Dataset (Kaggle)** - Dataset extendido

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
- `GET /recipes/search?q=` - Buscar platos por nombre (ignora mayúsculas y tildes)
- `GET /recipes/ingredients/categorized` - Ingredientes únicos por categoría
- `GET /recipes/{id}` - Detalle de receta (incluye datos detallados para "A cocinar")

## Frontend

- **index.html**: búsqueda por ingredientes, panel "Mis Ingredientes", buscador de platos, tarjetas de resultados.
- **recipe.html**: vista detallada **"A cocinar"** (se abre en otra pestaña). Muestra ingredientes con cantidades (`ingredientes_con_cantidades`), preparación detallada (`preparacion_detallada`), consejos del chef e info nutricional. Incluye checklist de ingredientes y botón de impresión.

## Tracking

Evento `recipe_steps_viewed` se dispara cuando:
- Usuario ingresa ≥ 3 ingredientes
- Abre la página **"A cocinar"** de una receta

Props: `user_id`, `ingredient_count`, `recipe_matched`, `time_to_match`

## Variables de Entorno

| Variable | Descripción | Default |
|----------|-------------|---------|
| `DATABASE_URL` | URL de base de datos (Postgres en producción). Si no se define, usa SQLite local (`backend/mealmatch.db`). Render entrega `postgres://...` y se convierte automáticamente a `postgresql://...`. | SQLite local |
| `PORT` | Puerto inyectado por Render (Docker). El contenedor escucha en `$PORT` (fallback 8000). | `8000` |
| `CORS_ORIGINS` | Orígenes permitidos | `*` |
| `MIXPANEL_TOKEN` | Token de Mixpanel | vacío |

## Despliegue en Render

1. **Web Service (Backend API)** — New Web Service con:
   - **Language:** Docker
   - **Root Directory:** (vacío)
   - **Dockerfile Path:** `./backend/Dockerfile`
   - **Branch:** `render`
   - **Instance Type:** Free
2. **PostgreSQL** — crea un PostgreSQL en Render y vincúlalo al Web Service. Render inyecta automáticamente la variable `DATABASE_URL`.
 3. **Auto-seed:** al arrancar, si la base está vacía se carga el dataset completo `Recetas_Peru_200` (`load_recetas_peru.py`). No se requiere paso manual.
4. **Frontend:** el `index.html` de `frontend/` es estático; despliégalo como **Static Site** aparte apuntando a `frontend/`.
