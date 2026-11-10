import os
import logging
from typing import Optional, Any
from dotenv import load_dotenv

load_dotenv()

registro = logging.getLogger("delux.bd")

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://gfhbmqpdxrsaueggnfhb.supabase.co").strip()
SUPABASE_KEY = os.getenv(
    "SUPABASE_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdmaGJtcXBkeHJzYXVlZ2duZmhiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTQxOTE4MDYsImV4cCI6MjEwOTc2NzgwNn0.FgMxP_DA5-kHkzrEJEXffbObP21EgEIKvqeuBMmWV04"
).strip()

cliente_supabase: Optional[Any] = None

try:
    from supabase import create_client
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            cliente_supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            registro.info("Supabase conectado")
        except Exception as e:
            registro.error(f"Error al conectar con Supabase: {e}")
            cliente_supabase = None
    else:
        registro.warning("Faltan SUPABASE_URL o SUPABASE_KEY: modo demostración")
except ImportError:
    registro.warning("Librería 'supabase' no instalada: modo demostración")
    create_client = None


def obtener_supabase() -> Optional[Any]:
    """Devuelve el cliente compartido de Supabase (o None en modo demo)."""
    return cliente_supabase


def crear_cliente_auth() -> Optional[Any]:
    """Cliente nuevo por solicitud, para que el login no altere la sesión del compartido."""
    if create_client is None or not (SUPABASE_URL and SUPABASE_KEY):
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)
