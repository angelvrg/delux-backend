import uuid
from typing import List
from datetime import datetime
from fastapi import FastAPI, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from database import obtener_supabase, crear_cliente_auth
from schemas import (
    volcar_modelo,
    RegistroSolicitud,
    LoginSolicitud,
    MaterialCrear,
    MaterialRespuesta,
    CotizacionCrear,
    CotizacionRespuesta,
    EstadoCotizacionSolicitud
)

NOMBRE_BUCKET = "fotos-materiales"
ENLACE_VERIFICACION = "deluxapp://verificado"

app = FastAPI(
    title="DE LUX - API de Mármoles y Piedras Finas",
    description="API REST para el catálogo de materiales, cotizaciones y usuarios.",
    version="1.1.0"
)

# Permite peticiones desde la app Android y navegadores
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Datos de respaldo cuando Supabase no está configurado
_MATERIALES_DEMO = [
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
_COTIZACIONES_DEMO = []


@app.get("/", tags=["Estado"])
def estado_api():
    supabase = obtener_supabase()
    return {
        "sistema": "DE LUX API",
        "estado": "operativo",
        "modo_base_datos": "Supabase PostgreSQL" if supabase else "Modo demostración (sin Supabase)",
        "documentacion": "/docs"
    }


# ========================================================
# AUTENTICACIÓN Y ROLES
# ========================================================

@app.post("/api/auth/registro", tags=["Autenticación"])
def registrar_usuario(datos: RegistroSolicitud):
    cliente = crear_cliente_auth()
    if not cliente:
        raise HTTPException(status_code=503, detail="Supabase no está configurado.")
    try:
        res = cliente.auth.sign_up({
            "email": datos.correo,
            "password": datos.password,
            "options": {
                "data": {"nombre": datos.nombre},
                "email_redirect_to": ENLACE_VERIFICACION
            }
        })
        if not res.user:
            raise HTTPException(status_code=400, detail="No se pudo registrar el usuario.")
        return {
            "mensaje": "Te enviamos un enlace de confirmación a tu correo. Revisa tu bandeja de entrada.",
            "user_id": res.user.id,
            "correo": res.user.email
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error en el registro: {str(e)}")


@app.post("/api/auth/login", tags=["Autenticación"])
def iniciar_sesion(datos: LoginSolicitud):
    cliente = crear_cliente_auth()
    if not cliente:
        raise HTTPException(status_code=503, detail="Supabase no está configurado.")
    try:
        res = cliente.auth.sign_in_with_password({
            "email": datos.correo,
            "password": datos.password
        })
        if not res.user or not res.session:
            raise HTTPException(status_code=401, detail="Credenciales inválidas o correo sin verificar.")

        # El rol lo asigna un trigger en la tabla 'perfiles'
        perfil = cliente.table("perfiles").select("*").eq("id", res.user.id).single().execute()
        return {
            "mensaje": "Inicio de sesión exitoso",
            "access_token": res.session.access_token,
            "usuario": {
                "id": res.user.id,
                "correo": res.user.email,
                "nombre": perfil.data.get("nombre", ""),
                "rol": perfil.data.get("rol", "cliente")
            }
        }
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Credenciales incorrectas o aún no has verificado tu correo electrónico."
        )


# ========================================================
# MATERIALES
# ========================================================

@app.get("/api/materiales", response_model=List[MaterialRespuesta], tags=["Materiales"])
def listar_materiales():
    supabase = obtener_supabase()
    if supabase:
        try:
            res = supabase.table("materiales").select("*").order("creado_en", desc=True).execute()
            return res.data
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error consultando Supabase: {str(e)}")
    return _MATERIALES_DEMO


@app.get("/api/materiales/{id}", response_model=MaterialRespuesta, tags=["Materiales"])
def obtener_material(id: int):
    supabase = obtener_supabase()
    if supabase:
        try:
            res = supabase.table("materiales").select("*").eq("id", id).single().execute()
            if not res.data:
                raise HTTPException(status_code=404, detail="Material no encontrado")
            return res.data
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Material no encontrado: {str(e)}")

    for material in _MATERIALES_DEMO:
        if material["id"] == id:
            return material
    raise HTTPException(status_code=404, detail="Material no encontrado")


@app.post("/api/materiales", response_model=MaterialRespuesta, status_code=status.HTTP_201_CREATED, tags=["Materiales"])
def registrar_material(material: MaterialCrear):
    supabase = obtener_supabase()
    datos = volcar_modelo(material)

    if supabase:
        try:
            res = supabase.table("materiales").insert(datos).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
            raise HTTPException(status_code=500, detail="No se pudo registrar el material")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error insertando en Supabase: {str(e)}")

    # Respaldo en memoria
    nuevo_id = max([m["id"] for m in _MATERIALES_DEMO], default=0) + 1
    registro = {"id": nuevo_id, "creado_en": datetime.utcnow(), **datos}
    _MATERIALES_DEMO.append(registro)
    return registro


@app.delete("/api/materiales/{id}", tags=["Materiales"])
def eliminar_material(id: int):
    supabase = obtener_supabase()
    if supabase:
        try:
            supabase.table("materiales").delete().eq("id", id).execute()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error eliminando material: {str(e)}")
    else:
        _MATERIALES_DEMO[:] = [m for m in _MATERIALES_DEMO if m["id"] != id]
    return {"mensaje": "Material eliminado correctamente"}


# ========================================================
# COTIZACIONES
# ========================================================

@app.post("/api/cotizaciones", response_model=CotizacionRespuesta, status_code=status.HTTP_201_CREATED, tags=["Cotizaciones"])
def crear_cotizacion(cotizacion: CotizacionCrear):
    supabase = obtener_supabase()
    datos_material = None

    # Se consulta el material para usar su precio real
    if supabase:
        try:
            res_material = supabase.table("materiales").select("*").eq("id", cotizacion.material_id).single().execute()
            if not res_material.data:
                raise HTTPException(status_code=404, detail="El material indicado no existe")
            datos_material = res_material.data
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Error validando material: {str(e)}")
    else:
        for material in _MATERIALES_DEMO:
            if material["id"] == cotizacion.material_id:
                datos_material = material
                break
        if not datos_material:
            raise HTTPException(status_code=404, detail="El material indicado no existe")

    precio_vigente = float(datos_material["precio_m2"])
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
    if cotizacion.usuario_id:
        datos["usuario_id"] = cotizacion.usuario_id

    if supabase:
        try:
            res = supabase.table("cotizaciones").insert(datos).execute()
            if res.data and len(res.data) > 0:
                item = res.data[0]
                item["material"] = datos_material
                return item
            raise HTTPException(status_code=500, detail="No se pudo registrar la cotización")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error guardando cotización: {str(e)}")

    registro = {
        "id": len(_COTIZACIONES_DEMO) + 1,
        "creado_en": datetime.utcnow(),
        "material": datos_material,
        **datos
    }
    _COTIZACIONES_DEMO.append(registro)
    return registro


@app.get("/api/cotizaciones", response_model=List[CotizacionRespuesta], tags=["Cotizaciones"])
def listar_cotizaciones():
    supabase = obtener_supabase()
    if supabase:
        try:
            # Incluye los datos del material relacionado
            res = supabase.table("cotizaciones").select("*, material:materiales(*)").order("creado_en", desc=True).execute()
            return res.data
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error consultando cotizaciones: {str(e)}")
    return _COTIZACIONES_DEMO


@app.patch("/api/cotizaciones/{cotizacion_id}/estado", tags=["Cotizaciones"])
def actualizar_estado_cotizacion(cotizacion_id: int, datos: EstadoCotizacionSolicitud):
    supabase = obtener_supabase()
    if supabase:
        try:
            res = supabase.table("cotizaciones").update({"estado": datos.estado}).eq("id", cotizacion_id).execute()
            return {"mensaje": "Estado actualizado", "datos": res.data}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error actualizando estado: {str(e)}")

    for cotizacion in _COTIZACIONES_DEMO:
        if cotizacion["id"] == cotizacion_id:
            cotizacion["estado"] = datos.estado
            return {"mensaje": "Estado actualizado", "datos": [cotizacion]}
    raise HTTPException(status_code=404, detail="Cotización no encontrada")


# ========================================================
# SUBIDA DE FOTOS (SUPABASE STORAGE)
# ========================================================

@app.post(
    "/api/upload",
    tags=["Almacenamiento"],
    summary="Sube la foto de una placa",
    description="Recibe la foto tomada con la cámara, la guarda en el bucket fotos-materiales y devuelve su URL pública."
)
async def subir_imagen(file: UploadFile = File(...)):
    supabase = obtener_supabase()
    nombre_archivo = f"{uuid.uuid4().hex}_{file.filename or 'foto.jpg'}"
    contenido = await file.read()

    if supabase:
        try:
            supabase.storage.from_(NOMBRE_BUCKET).upload(
                file=contenido,
                path=nombre_archivo,
                file_options={"content-type": file.content_type or "image/jpeg"}
            )
            url_publica = supabase.storage.from_(NOMBRE_BUCKET).get_public_url(nombre_archivo)
            return {"foto_url": url_publica, "archivo": nombre_archivo}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al subir la foto: {str(e)}")

    # Sin Supabase se devuelve una imagen de muestra
    return {
        "foto_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1000&q=80",
        "archivo": nombre_archivo,
        "nota": "Modo demostración: URL de muestra."
    }
