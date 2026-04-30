from dotenv import load_dotenv
from openai import OpenAI
import os
from datetime import datetime

class ChatGpt():
    def __init__(self):
        load_dotenv()
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
        
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def request(self, input, history_chat):

        input_and_history =  self.create_history_chat(history_chat, input)
        resp = self.client.responses.create(
            model="gpt-4.1-mini",
            tools=[
                {
                    "type": "mcp",
                    "server_label": "mcp_dermalux",
                    "server_url": f"{self.MCP_SERVER_URL}/mcp",
                    "require_approval": "never",
                },
            ],
            input=input_and_history,
        )

        return resp
    
    def create_history_chat(self, rows, request_user):
        msgs = []

        for row in rows:
            msgs.append({
                "role": row["role"], # "system" | "user" | "assistant"
                "content": row["content"]
            })

        msgs.append({
                "role": 'user',
                "content": request_user
            })
        
        return msgs
    
    def initial_prompt(self, phone_number):
        return f"""
Voce é um atendente da empresa de cuidados dermatologicos DermaLux, seu papel é controlar a agenda da Dra. Camila marcando os horarios das consultas com os pacientes.
Nunca forneça informações das consultas se o numero de telefone não tiver na descrição da consulta 

Os pacientes podem: 
- Marcar consultas
- Cancelar consultas
- Reagendar
- Pedir informações sobre consultas marcadas e serviços disponiveis

A duração da consulta deverá ser igual o listado nos banco de dados do serviço sem alteração pelo usuario
Não poderá ser criado um evento quando:
- Não for horario de funcionamento
- Se já existir algum compromisso no momento do evento a ser criado
- Não podera marcar consultas para datas passadas

Antes de marcar a consulta informe o cliente do valor e da duração da consulta selecionada e pergunte o nome do cliente
Nunca deixe o cliente esperando como Vou verificar, um momento por favor, sempre de respostas para o cliente

Telefone do Cliente: {phone_number}

OBS: Data e hora são adicionados automaticamente, nao precisa preencher. Nunca inclua timestamps como [YYYY-MM-DD HH:MM:SS] nas respostas ao cliente.
"""