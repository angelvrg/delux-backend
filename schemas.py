from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime

# Helper para volcar modelos en Pydantic v1 o v2
def dump_model(model: BaseModel) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


# ==================== MATERIALES ====================

class MaterialBase(BaseModel):
    nombre: str = Field(..., description="Nombre del material")
    descripcion: Optional[str] = Field(None, description="Acabado o descripción")
    foto_url: str = Field(..., description="URL de la imagen en Supabase Storage")
    largo: float = Field(..., gt=0, description="Largo en metros")
    ancho: float = Field(..., gt=0, description="Ancho en metros")
    espesor: float = Field(..., gt=0, description="Espesor en centímetros")
    precio_m2: float = Field(..., gt=0, description="Precio de lista por metro cuadrado")

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
    nombre_cliente: str = Field(..., min_length=2)
    telefono_cliente: str = Field(..., min_length=7)
    metros_cuadrados: float = Field(..., gt=0)
    precio_m2_registrado: Optional[float] = None
    total_estimado: Optional[float] = None
    mensaje: Optional[str] = None

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
