# DE LUX - Backend FastAPI

API REST para el catálogo de mármoles y piedras finas, sistema de cotizaciones y almacenamiento multimedia de la empresa **DE LUX**.
Preparada para despliegue inmediato en **Render** y conectada a **Supabase (PostgreSQL + Storage)**.

---

## 🚀 Endpoints Principales

- `GET /`: Estado operativo del servicio y confirmación de conexión a base de datos.
- `GET /api/materiales`: Listado de placas de mármol y piedra disponibles.
- `GET /api/materiales/{id}`: Detalle de un material específico por su ID.
- `POST /api/materiales`: Registro de una nueva placa de material con dimensiones y precio/m².
- `GET /api/cotizaciones`: Listado de solicitudes de cotización generadas por clientes.
- `POST /api/cotizaciones`: Cálculo automático y guardado de una nueva cotización.
- `POST /api/upload`: **Flujo de subida de fotos:** Cuando la app toma la foto de la placa con la cámara, envía el archivo al backend. La API genera un identificador único (UUID), sube el archivo binario al bucket `fotos-materiales` de Supabase Storage y retorna la URL pública para asociarla automáticamente al registrar el material.
- `GET /docs`: Documentación Swagger interactiva.
- `GET /redoc`: Documentación técnica alternativa ReDoc.

---

## 🛠️ Puesta en marcha rápida en local

```bash
# 1. Crear y activar entorno virtual
python -m venv venv
venv\Scripts\activate      # En Windows
# source venv/bin/activate  # En Linux / macOS

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Las credenciales de Supabase ya se encuentran preconfiguradas en el archivo .env

# 4. Iniciar el servidor de desarrollo
uvicorn main:app --reload --port 8000
```

Visita en tu navegador:
- Documentación interactiva Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)
- Verificación de estado: [http://localhost:8000/](http://localhost:8000/)

---

## 🗄️ Base de Datos y Storage en Supabase

- **URL del Proyecto:** `https://gfhbmqpdxrsaueggnfhb.supabase.co`
- **Tablas:** Gestionadas mediante PostgreSQL (`materiales` y `cotizaciones`). Esquema completo disponible en `schema.sql`.
- **Storage Bucket:** `fotos-materiales` (Público) para almacenar las fotografías de placas capturadas por los asesores.

---

## ☁️ Despliegue en Render

El repositorio incluye el archivo `render.yaml` (Blueprint) para despliegue automático:

1. Ve a [Render Dashboard](https://dashboard.render.com/).
2. Haz clic en **New +** -> **Blueprint** (o **Web Service** seleccionando este repositorio).
3. Selecciona tu repositorio `delux-backend`.
4. Render configurará automáticamente el servicio web con Python, `requirements.txt`, comando de inicio y las variables de entorno de Supabase.
5. Presiona **Apply** / **Deploy**. Render generará tu URL pública (ejemplo: `https://delux-api.onrender.com`).
