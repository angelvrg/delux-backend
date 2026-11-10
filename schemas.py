from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Any


def volcar_modelo(modelo: BaseModel) -> dict:
    """Convierte un modelo a diccionario (Pydantic v1 o v2)."""
    if hasattr(modelo, "model_dump"):
        return modelo.model_dump()
    return modelo.dict()


# ==================== AUTENTICACIÓN ====================

class RegistroSolicitud(BaseModel):
    correo: EmailStr
    password: str = Field(..., min_length=6)
    nombre: str = Field(..., min_length=2)


class LoginSolicitud(BaseModel):
    correo: EmailStr
    password: str


# ==================== MATERIALES ====================

class MaterialBase(BaseModel):
    nombre: str = Field(..., description="Nombre del material")
    descripcion: Optional[str] = Field(None, description="Acabado o descripción")
    foto_url: str = Field(..., description="URL de la foto en Supabase Storage")
    largo: float = Field(..., gt=0, description="Largo en metros")
    ancho: float = Field(..., gt=0, description="Ancho en metros")
    espesor: float = Field(..., gt=0, description="Espesor en centímetros")
    precio_m2: float = Field(..., gt=0, description="Precio por metro cuadrado")


class MaterialCrear(MaterialBase):
    pass


class MaterialRespuesta(MaterialBase):
    id: int
    creado_en: Optional[Any] = None

    class Config:
        orm_mode = True
        from_attributes = True


# ==================== COTIZACIONES ====================

class CotizacionCrear(BaseModel):
    material_id: int
    usuario_id: Optional[str] = None
    nombre_cliente: str = Field(..., min_length=2)
    telefono_cliente: str = Field(..., min_length=7)
    metros_cuadrados: float = Field(..., gt=0)
    precio_m2_registrado: Optional[float] = None
    total_estimado: Optional[float] = None
    mensaje: Optional[str] = None


class EstadoCotizacionSolicitud(BaseModel):
    estado: str  # Ej: "Pendiente", "Aprobada", "Rechazada"


class CotizacionRespuesta(BaseModel):
    id: int
    material_id: int
    nombre_cliente: str
    telefono_cliente: str
    metros_cuadrados: float
    precio_m2_registrado: float
    total_estimado: float
    mensaje: Optional[str] = None
    estado: str = "Pendiente"
    creado_en: Optional[Any] = None
    material: Optional[MaterialRespuesta] = None

    class Config:
        orm_mode = True
        from_attributes = True
