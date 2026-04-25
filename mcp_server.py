from fastmcp import FastMCP
import time
import json
import functools
import inspect
import uuid
from datetime import datetime
import os

from src.services.google_calendar import GoogleCalendar
from src.services.supabase import SupabaseClient

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger("mcp.tools")

def scrub_args(kwargs: dict) -> dict:
    """Remove/mascara campos sensíveis dos argumentos."""
    SENSITIVE = {"token", "authorization", "password", "secret", "api_key"}
    clean = {}
    for k, v in kwargs.items():
        if k.lower() in SENSITIVE:
            clean[k] = "***"
        else:
            # evita logar payloads gigantes
            try:
                s = json.dumps(v, ensure_ascii=False)
                clean[k] = s if len(s) <= 500 else f"{s[:500]}... (+{len(s)-500} chars)"
            except Exception:
                clean[k] = str(v)
    return clean

def summarize_result(res):
    """Gera um resumo curto do retorno para o log."""
    try:
        s = json.dumps(res, ensure_ascii=False)
    except Exception:
        s = str(res)
    # limite pra não floodar
    return s if len(s) <= 500 else f"{s[:500]}... (+{len(s)-500} chars)"

def logged_tool(mcp, *, name: str | None = None):
    """
    Decorator que registra a função como tool MCP e adiciona logs de start/end/erro.
    Uso: @logged_tool(mcp, name="delete_calendar_event")
    """
    def outer(func):
        is_async = inspect.iscoroutinefunction(func)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            iid = uuid.uuid4().hex[:8]  # invocation id para correlacionar
            t0 = time.monotonic()
            logger.info(f"[{iid}] START tool={name or func.__name__} args={scrub_args(kwargs)}")
            try:
                result = await func(*args, **kwargs)
                dt = time.monotonic() - t0
                logger.info(f"[{iid}] END   tool={name or func.__name__} dt={dt:.3f}s result={summarize_result(result)}")
                return result
            except Exception:
                dt = time.monotonic() - t0
                logger.exception(f"[{iid}] ERROR tool={name or func.__name__} dt={dt:.3f}s")
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            iid = uuid.uuid4().hex[:8]
            t0 = time.monotonic()
            logger.info(f"[{iid}] START tool={name or func.__name__} args={scrub_args(kwargs)}")
            try:
                result = func(*args, **kwargs)
                dt = time.monotonic() - t0
                logger.info(f"[{iid}] END   tool={name or func.__name__} dt={dt:.3f}s result={summarize_result(result)}")
                return result
            except Exception:
                dt = time.monotonic() - t0
                logger.exception(f"[{iid}] ERROR tool={name or func.__name__} dt={dt:.3f}s")
                raise

        wrapper = async_wrapper if is_async else sync_wrapper
        # registra como tool MCP
        return mcp.tool(name=name)(wrapper)
    return outer


logging.basicConfig(level=logging.INFO)
mcp = FastMCP(name="Tools DermaLux")
google_calendar = GoogleCalendar()
supabase = SupabaseClient()

@logged_tool(mcp, name="create_calendar_event")
async def create_calendar_event(
    service_name:str,
    client_name:str,
    phone_number:str,
    start:str,
    minutes:int=30
) -> str:
    """
    Cria um evento no Goole Calendar usando a função já existente

    Paramtros:
    - start: data/hora de inicio em ISO 8601 (ex.: '2025-09-27T11:30:00') (obrigatorio)
    - service_name: nome do serviço (obrigatorio)
    - client_name: nome do cliente (obrigatorio)
    - phone_number: telefone do cliente (ex.: '5511988888888') (obrigatorio)
    - minutes: duração do evento em minutos (padrao: 30)

    Retorno
    - string informando se foi criado o evento
    """
    
    result = google_calendar.create_event(
        service_name=service_name,
        client_name=client_name,
        phone_number=phone_number,
        start=start,
        minutes=minutes
    )

    # return "Evento Criado"
    return result


@logged_tool(mcp, name="delete_calendar_event")
async def delete_calendar_event(
    id_event:str,
    phone_number:str
) -> dict:
    """
    Delta um evento do Google Calendar

    Paramtros:
    - id_event: ID unico do evento a ser deletado (obrigatorio)
    - phone_number: Numero de telefone do cliente (obrigatorio)

    Retorno
    - Um json com informacoe sobre o evento deletado
    """

    if not id_event:
        raise ValueError('id do evento é obrigatorio')
    
    result = google_calendar.delete_event(id_event, phone_number)

    return result


@logged_tool(mcp, name="list_calendar_events")
async def list_calendar_events(
    start:str,
    end:str,
    filter:str=''
) -> list:
    """
    Lista os eventos existentes do Google calendar, entre as datas passadas

    Paramtros:
    - start: data/hora de inicio em ISO 8601 (ex.: '2025-09-27T11:30:00')
    - end: data/hora de inicio em ISO 8601 (ex.: '2025-09-27T11:30:00')
    - filter: palavra-chave usada para filtrar os eventos, os filtros aplica-se aos campos de titulo, descrição e localizacao (Opcional)

    Retorno
    - Uma lista com todos os eventos existentes
    """

    if not start:
        raise ValueError("start é obrigatório (ex.: 2025-09-27T11:30:00).")
    if not end:
        raise ValueError("end é obrigatório (ex.: 2025-09-27T11:30:00).")
    
    result = google_calendar.list_events(start, end, filter)

    return result


@logged_tool(mcp, name="date_now")
async def date_now() -> str:
    """
    Obtem a data e hora atual
    Sempre use essa função para pegar a data e hora atual

    Retorno
    - Uma string com a data e hora atual
    """

    return f"Data e hora atual: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"

@logged_tool(mcp, name="load_services")
async def load_services() -> list:
    """
    Busca no banco de dados os serviços disponiveis

    Retorno
    - Uma lista de dicionarios contendo a category, service, duration, cost e description
    """

    return supabase.load_services()

@logged_tool(mcp, name="call_attendant")
async def call_attendant(
    phone_number:str
    ) -> str:
    """
    Função que executa a chamada de um atendente
    
    Paramtros:
    - phone_numer: telefone do cliente (obrigatorio) 

    Retorno
    - Uma string informando a chamada do atendente
    """
    supabase.update_fallback_customer(phone_number, False)
    
    return "Chamando atendente"


if __name__ == "__main__":
    mcp.run(
        transport="http", 
        host="0.0.0.0", 
        port=int(os.getenv("PORT", 8000)),
        stateless_http=True
    )