from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
import os 

from src.services.zapi import ZApi
from src.services.message_buffer import MessageBuffer
from src.services.chatgpt import ChatGpt
from src.services.supabase import SupabaseClient

from src.routes.utils import convert_unix_epoch
from datetime import datetime, timezone, timedelta

load_dotenv()

receive_mensage_bp = Blueprint("receive_mensage", __name__)

supabase = SupabaseClient()
agent = ChatGpt()
zapi = ZApi()
buffer = MessageBuffer()

MY_CHAT_LID = os.getenv('MY_CHAT_LID')

def process_request(phone_number: str, request_user):
    """
    
    """
    # Procura todoas as mensagens do usuario
    history_msgs = supabase.search_messages(phone_number)
    
    # Quando não existe conversa, cria a instrução inicial do agente
    if len(history_msgs) == 0:
        supabase.insert_msg(phone_number, "system", agent.initial_prompt(phone_number))
        supabase.update_fallback_customer(phone_number, True)
        # Atualiza a variavel msgs com a instrução do sistema
        history_msgs = supabase.search_messages(phone_number)

    if supabase.search_fallback_customer(phone_number):
        # Armazena a requisição atual do usuario
        supabase.insert_msg(phone_number, "user", request_user)

        # Envia o historico e a requisicao atual para o agente
        response = agent.request(request_user, history_msgs)

        # Armazena a resposta do agente
        supabase.insert_msg(phone_number, "assistant", response.output_text)

        zapi.send_message(phone_number, response.output_text)


@receive_mensage_bp.route("/receive_mensage", methods=["POST"])
def receive_mensage():
    data = request.json
    
    hour_message = convert_unix_epoch(data['momment'])
    phone_number = data['connectedPhone']

    brasilia_tz = timezone(timedelta(hours=-3))
    
    seconds_since = (datetime.now(brasilia_tz) - hour_message).total_seconds()

    # bot_blocked = True
    customer = supabase.search_block_bot(phone_number)
    if len(customer) > 0:
        bot_blocked = customer[0]['bot_blocked']

    # Recebendo as ultimas mensagens dentro de 5 minutos
    is_my_own_chat = (data['chatLid'] == MY_CHAT_LID and data['fromApi'] == False)

    valid_message = "text" in data and seconds_since < 300

    if  valid_message and data['isGroup'] == False and bot_blocked == False and ((data['fromMe'] == False) or is_my_own_chat):
        message = data['text']['message']
        buffer.add(phone_number, message, process_request)

    return jsonify({"status": "ok"}), 200