from apscheduler.schedulers.blocking import BlockingScheduler

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.services.supabase import SupabaseClient
from src.services.zapi import ZApi
from src.services.google_calendar import GoogleCalendar
from src.services.logging_config import setup_logger, logger

setup_logger()

class FollowUp():
    def __init__(self):
        self.scheduler = BlockingScheduler()
        self.zapi = ZApi()
        self.google_calendar = GoogleCalendar()
        self.supabase = SupabaseClient()

    def get_data_event(self, event):
        data_event = {}
        for linha in event['description'].splitlines():
                key, value = linha.split(":", 1)
                data_event[key.strip()] = value.strip()

        date_time = datetime.fromisoformat(event['start']['dateTime'])
        data_event['Date'] = date_time.strftime("%d/%m/%Y")
        data_event['Hour'] = date_time.strftime("%H:%M")

        return data_event

    def process_message(self, event, data_event, buttons_dict):
        msg = f"Olá {data_event['Cliente']}, confirma sua consulta {data_event['Serviço']} dia {data_event['Date']} ás {data_event['Hour']}"
        self.zapi.send_button_message(data_event["Telefone"], msg, buttons_dict)
        
        # Armazena a resposta no historico
        self.supabase.insert_msg(data_event['Telefone'], "assistant", msg)

        self.google_calendar.modify_follow_up_event(event['id'])

        logger.info(msg)

    def workflow(self):

        # Data de procura dos eventos
        tomorrow = (datetime.now(ZoneInfo("America/Sao_Paulo")) + timedelta(days=1))
        start_date = tomorrow.strftime("%Y-%m-%dT00:00:00")
        end_date = tomorrow.strftime("%Y-%m-%dT23:59:00")

        events = self.google_calendar.list_events(start_date, end_date)

        for event in events:
            data_event = self.get_data_event(event)
            buttons_dict = {
                "buttons": [
                    {
                        "id": 'confirm',
                        "label": "Confirmar"
                    },
                    {
                        "id": event['id'],
                        "label": "Cancelar"
                    }
                ]
            }

        if data_event['FollowUp'] == "False":
            self.process_message(event, data_event, buttons_dict)
            
            
            

    