import os
import uuid
from typing import List
from datetime import datetime
from fastapi import FastAPI, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from database import get_supabase, SUPABASE_URL
from schemas import (
    dump_model,
    MaterialCrear,
    MaterialRespuesta,
    CotizacionCrear,
    CotizacionRespuesta
)

app = FastAPI(
    title="DE LUX - API de Mármoles y Piedras Finas",
    description="API REST para la gestión de catálogo de materiales y cotizaciones en tiempo real.",
    version="1.0.0"
)

# Permitir CORS para Android Studio (emuladores y dispositivos físicos) y navegadores
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Memoria de respaldo si aún no se han configurado credenciales de Supabase
_DEMO_MATERIALES = [
    {
        "id": 1,
        "nombre": "Mármol Blanco Carrara",
        "descripcion": "Acabado pulido brillante de primera calidad, origen Italia.",
        "foto_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1000&q=80",
        "largo": 2.80,
        "ancho": 1.60,
        "espesor": 2.00,
        "precio_m2": 1850.00,
        "creado_en": datetime.utcnow()
    },
    {
        "id": 2,
        "nombre": "Granito Negro San Gabriel",
        "descripcion": "Negro profundo de alta dureza y máxima resistencia al rayado.",
        "foto_url": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?auto=format&fit=crop&w=1000&q=80",
        "largo": 3.00,
        "ancho": 1.85,
        "espesor": 2.00,
        "precio_m2": 1420.00,
        "creado_en": datetime.utcnow()
    },
    {
        "id": 3,
        "nombre": "Cuarcita Taj Mahal",
        "descripcion": "Elegancia translúcida beige con vetas doradas naturales.",
        "foto_url": "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1000&q=80",
        "largo": 2.95,
        "ancho": 1.75,
        "espesor": 2.00,
        "precio_m2": 2900.00,
        "creado_en": datetime.utcnow()
    }
]
_DEMO_COTIZACIONES = []


@app.get("/", tags=["Estado"])
def estado_api():
    supabase = get_supabase()
    return {
        "sistema": "DE LUX API",
        "estado": "operativo",
        "modo_base_datos": "Supabase PostgreSQL" if supabase else "Modo local / demostración (esperando variables de Supabase)",
        "documentacion": "/docs"
    }


# ========================================================
# ENDPOINTS DE MATERIALES
# ========================================================

@app.get("/api/materiales", response_model=List[MaterialRespuesta], tags=["Materiales"])
def listar_materiales():
    supabase = get_supabase()
    if supabase:
        try:
            res = supabase.table("materiales").select("*").order("creado_en", desc=True).execute()
            return res.data
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error consultando Supabase: {str(e)}")
    return _DEMO_MATERIALES


@app.get("/api/materiales/{id}", response_model=MaterialRespuesta, tags=["Materiales"])
def obtener_material(id: int):
    supabase = get_supabase()
    if supabase:
        try:
            res = supabase.table("materiales").select("*").eq("id", id).single().execute()
            if not res.data:
                raise HTTPException(status_code=404, detail="Material no encontrado")
            return res.data
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Material no encontrado: {str(e)}")

    for mat in _DEMO_MATERIALES:
        if mat["id"] == id:
            return mat
    raise HTTPException(status_code=404, detail="Material no encontrado")


@app.post("/api/materiales", response_model=MaterialRespuesta, status_code=status.HTTP_201_CREATED, tags=["Materiales"])
def registrar_material(material: MaterialCrear):
    supabase = get_supabase()
    datos = dump_model(material)

    if supabase:
        try:
            res = supabase.table("materiales").insert(datos).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
            raise HTTPException(status_code=500, detail="No se pudo registrar el material en Supabase")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error insertando en Supabase: {str(e)}")

    # Fallback local
    nuevo_id = max([m["id"] for m in _DEMO_MATERIALES], default=0) + 1
    registro = {
        "id": nuevo_id,
        "creado_en": datetime.utcnow(),
        **datos
    }
    _DEMO_MATERIALES.append(registro)
    return registro


# ========================================================
# ENDPOINTS DE COTIZACIONES
# ========================================================

@app.post("/api/cotizaciones", response_model=CotizacionRespuesta, status_code=status.HTTP_201_CREATED, tags=["Cotizaciones"])
def crear_cotizacion(cotizacion: CotizacionCrear):
    supabase = get_supabase()
    material_data = None

    # Obtener el precio por m2 del material para garantizar la integridad
    if supabase:
        try:
            res_mat = supabase.table("materiales").select("*").eq("id", cotizacion.material_id).single().execute()
            if not res_mat.data:
                raise HTTPException(status_code=404, detail="El material indicado no existe")
            material_data = res_mat.data
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Error validando material: {str(e)}")
    else:
        for mat in _DEMO_MATERIALES:
            if mat["id"] == cotizacion.material_id:
                material_data = mat
                break
        if not material_data:
            raise HTTPException(status_code=404, detail="El material indicado no existe")

    precio_vigente = float(material_data["precio_m2"])
    precio_m2_registrado = cotizacion.precio_m2_registrado or precio_vigente
    total_estimado = round(cotizacion.metros_cuadrados * precio_m2_registrado, 2)

    datos = {
        "material_id": cotizacion.material_id,
        "nombre_cliente": cotizacion.nombre_cliente,
        "telefono_cliente": cotizacion.telefono_cliente,
        "metros_cuadrados": cotizacion.metros_cuadrados,
        "precio_m2_registrado": precio_m2_registrado,
        "total_estimado": total_estimado,
        "mensaje": cotizacion.mensaje,
        "estado": "Pendiente"
    }

    if supabase:
        try:
            res = supabase.table("cotizaciones").insert(datos).execute()
            if res.data and len(res.data) > 0:
                item = res.data[0]
                item["material"] = material_data
                return item
            raise HTTPException(status_code=500, detail="No se pudo registrar la cotización")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error guardando cotización en Supabase: {str(e)}")

    nuevo_id = len(_DEMO_COTIZACIONES) + 1
    registro = {
        "id": nuevo_id,
        "creado_en": datetime.utcnow(),
        "material": material_data,
        **datos
    }
    _DEMO_COTIZACIONES.append(registro)
    return registro


@app.get("/api/cotizaciones", response_model=List[CotizacionRespuesta], tags=["Cotizaciones"])
def listar_cotizaciones():
    supabase = get_supabase()
    if supabase:
        try:
            # Traer cotización con datos del material relacionado
            res = supabase.table("cotizaciones").select("*, material:materiales(*)").order("creado_en", desc=True).execute()
            return res.data
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error consultando cotizaciones: {str(e)}")

    return _DEMO_COTIZACIONES


# ========================================================
# ENDPOINT DE SUBIDA A SUPABASE STORAGE
# ========================================================

@app.post(
    "/api/upload",
    tags=["Almacenamiento"],
    summary="Subida de foto de placa a Supabase Storage",
    description="Cuando la app toma la foto de la placa con la cámara, envía el archivo al backend. La API genera un identificador único (UUID), sube el archivo binario al bucket fotos-materiales y retorna la URL pública para asociarla automáticamente al registrar el material."
)
async def subir_imagen(file: UploadFile = File(...)):
    supabase = get_supabase()
    nombre_archivo = f"{uuid.uuid4().hex}_{file.filename}"
    contenido = await file.read()

    if supabase:
        try:
            # Subir al bucket público 'fotos-materiales'
            bucket_nombre = "fotos-materiales"
            supabase.storage.from_(bucket_nombre).upload(
                file=contenido,
                path=nombre_archivo,
                file_options={"content-type": file.content_type or "image/jpeg"}
            )
            public_url = supabase.storage.from_(bucket_nombre).get_public_url(nombre_archivo)
            return {"foto_url": public_url, "archivo": nombre_archivo}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al subir archivo a Supabase Storage: {str(e)}")

    # En modo demo sin Supabase, retornamos una imagen representativa
    return {
        "foto_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1000&q=80",
        "archivo": nombre_archivo,
        "nota": "Modo local: se retornó URL de muestra. Configura SUPABASE_URL y SUPABASE_KEY para almacenamiento real."
    }
