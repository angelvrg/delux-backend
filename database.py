import os
import logging
from typing import Optional, Any
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("delux.db")

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://gfhbmqpdxrsaueggnfhb.supabase.co").strip()
SUPABASE_KEY = os.getenv(
    "SUPABASE_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdmaGJtcXBkeHJzYXVlZ2duZmhiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTQxOTE4MDYsImV4cCI6MjEwOTc2NzgwNn0.FgMxP_DA5-kHkzrEJEXffbObP21EgEIKvqeuBMmWV04"
).strip()

supabase_client: Optional[Any] = None

try:
    from supabase import create_client, Client
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("Cliente de Supabase inicializado correctamente")
        except Exception as e:
            logger.error(f"Error conectando a Supabase: {e}")
            supabase_client = None
    else:
        logger.warning("SUPABASE_URL o SUPABASE_KEY no configuradas. La API operará en modo memoria/demo hasta configurar las variables de entorno.")
except ImportError:
    logger.warning("Librería 'supabase' no instalada en este entorno. Operando en modo memoria/demo.")
    supabase_client = None

def get_supabase() -> Optional[Any]:
    return supabase_client
