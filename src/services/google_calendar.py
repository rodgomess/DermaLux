import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from googleapiclient.errors import HttpError

from zoneinfo import ZoneInfo
from datetime import datetime, timedelta

import logging

logging.basicConfig(level=logging.INFO)

class GoogleCalendar():
    def __init__(self):
        self.creds = self.check_token_file()
        self.service = build("calendar", "v3", credentials=self.creds, cache_discovery=False)

    def check_token_file(self):
        # If modifying these scopes, delete the file token.json.
        SCOPES = ["https://www.googleapis.com/auth/calendar"]
        creds = None

        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
        return creds
    
    def parse_brasilia_datetime(self, iso_string: str) -> datetime:
        """
        Converte uma string ISO para datetime com timezone fixo em Brasília (UTC-3).
        Se a string não tiver fuso, assume automaticamente America/Sao_Paulo.
        """
        dt = iso_string+"-03:00"
        dt = datetime.fromisoformat(iso_string)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("America/Sao_Paulo"))
        return dt

    def list_events(self, start, end, text_filter=''):
        # Call the Calendar API
        dt_start = self.parse_brasilia_datetime(start)
        dt_end = self.parse_brasilia_datetime(end)

        events_result = (
            self.service.events()
            .list(
                calendarId="primary",
                q=text_filter,
                timeMin=dt_start.isoformat(),
                timeMax=dt_end.isoformat(),
                maxResults=100,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])
        
        return events

    def create_event(self, service_name, client_name, phone_number, start, minutes):
        # garante datetime com timezone
        dt_start = self.parse_brasilia_datetime(start)
        dt_end = dt_start + timedelta(minutes=minutes)

        if len(self.list_events(start, dt_end.strftime('%Y-%m-%dT%H:%M:%S'))) > 0:
            return {
            "ok": False,
            "message": "Já existe um evento neste horario, selecione outro"
            }
        
        description = f"""Cliente: {client_name}\nServiço: {service_name}\nTelefone: {phone_number}\nFollowUp: False"""
        
        summary = f"{service_name}, {client_name}"
        event = {
            "summary": summary,
            "description": description,
            "start": {
                "dateTime": dt_start.isoformat(),
                "timeZone": "America/Sao_Paulo",
            },
            "end": {
                "dateTime": dt_end.isoformat(),
                "timeZone": "America/Sao_Paulo",
            },
        }

        created = self.service.events().insert(calendarId="primary", body=event).execute()

        # return created
        return {
            "ok": True,
            "link_event": str(created.get('htmlLink')),
            "message": "Evento criado com sucesso",
            "id_event": created.get('id')
        }
    
    def modify_follow_up_event(self, id_event):
        
        data_event = self.search_event_by_id(id_event)
        new_description = data_event['description'].replace("FollowUp: False", "FollowUp: True")
        self.service.events().patch(
            calendarId="primary",
            eventId=id_event,
            body={
                "description": new_description
            }
        ).execute()

        return "Event description modified"

    def search_event_by_id(self, id_event):
        return self.service.events().get(calendarId="primary", eventId=id_event).execute()
    
    def delete_event(self, id_event, phone_number):
             
        try:
            if phone_number not in self.search_event_by_id(id_event)['description']:
                return {
                    "ok": False,
                    "message": "Somente o numero que solicitou a consulta pode fazer o cancelamento"
                }
        
            self.service.events().delete(calendarId="primary", eventId=id_event).execute()

            return {
                "ok": True, 
                "message": "Evento deletado", 
                "event_id": id_event
            }
        
        except HttpError as e:
            status = getattr(getattr(e, "resp", None), "status", None)
            if status in (404, 410):
                return {
                    "ok": True,
                    "message": "Evento já estava deletado ou não existe",
                    "event_id": id_event
                }
            
            raise RuntimeError(f"Falha ao deletar evento ({status}).") from e