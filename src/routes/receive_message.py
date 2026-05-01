from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
import os 

from src.services.zapi import ZApi
from src.services.message_buffer import MessageBuffer
from src.services.chatgpt import ChatGpt
from src.services.supabase import SupabaseClient
from src.services.google_calendar import GoogleCalendar
from src.services.logging_config import setup_logger, logger

from src.routes.utils import convert_unix_epoch
from datetime import datetime, timezone, timedelta

load_dotenv()
setup_logger()

receive_mensage_bp = Blueprint("receive_mensage", __name__)

supabase = SupabaseClient()
agent = ChatGpt()
zapi = ZApi()
buffer = MessageBuffer()
google_calendar = GoogleCalendar()

MY_CHAT_LID = os.getenv('MY_CHAT_LID')

def process_follow_up(phone_number, button_msg):

    # Armazena a resposta do usuario
    supabase.insert_msg(phone_number, "user", button_msg['message'])

    # Confirmar consulta
    if button_msg['message'].upper() == "CONFIRMAR":

        response_msg = "Consulta confirmada, Obrigado!"
        zapi.send_message(phone_number, response_msg)

        # Armazena a resposta no historico
        supabase.insert_msg(phone_number, "assistant", response_msg)

    # Cancelar consulta
    if button_msg['message'].upper() == "CANCELAR":
        # Exclui o evento do calendario
        google_calendar.delete_event(button_msg['buttonId'], phone_number)

        response_msg = "Consulta cancelada, caso queira remarcar basta me pedir, Obrigado!"

        # Armazena a resposta no historico
        supabase.insert_msg(phone_number, "assistant", response_msg)

        # Envia resposta para o cliente
        zapi.send_message(phone_number, response_msg)


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

        logger.info('Consultando agente')
        # Envia o historico e a requisicao atual para o agente
        response = agent.request(request_user, history_msgs)

        # Armazena a resposta do agente
        supabase.insert_msg(phone_number, "assistant", response.output_text)

        response_api = zapi.send_message(phone_number, response.output_text)
        logger.info("ZAPI status=%s body=%s", response_api.status_code, response_api.text)
        logger.info(f'Enviando respota para telefone {phone_number}')


@receive_mensage_bp.route("/receive_mensage", methods=["POST"])
def receive_mensage():
    logger.info('Recebendo mensagem')
    data = request.json
    
    hour_message = convert_unix_epoch(data['momment'])
    if data['phone'] == MY_CHAT_LID:
        phone_number = data['connectedPhone']
        
    else:
        phone_number = data['phone']

    brasilia_tz = timezone(timedelta(hours=-3))
    
    seconds_since = (datetime.now(brasilia_tz) - hour_message).total_seconds()

    customer = supabase.search_block_bot(phone_number)
    if len(customer) > 0:
        bot_blocked = customer[0]['bot_blocked']
    else:
        bot_blocked = True

    is_my_own_chat = (data['chatLid'] == MY_CHAT_LID and data['fromApi'] == False)

    # Verificando se msg é valida para resposta
    recent_msg = seconds_since < 300
    is_not_group = data['isGroup'] == False
    bot_blocked_in_user = bot_blocked == False
    msg_from_me = data['fromMe'] == False

    is_text_msg = "text" in data
    is_button_response_msg = "buttonsResponseMessage" in data

    msg_valid = recent_msg and is_not_group and bot_blocked_in_user and ((msg_from_me) or is_my_own_chat)

    # Confirmação Follow Up
    if is_button_response_msg and msg_valid:
        logger.info('Enviando resposta ao fallow up')
        process_follow_up(phone_number, data['buttonsResponseMessage'])

    # Assistente Inteligente
    if  is_text_msg and msg_valid:
        logger.info('Mensagem de texto valida, enviando resposta do agente')
        message = data['text']['message']
        buffer.add(phone_number, message, process_request)

    return jsonify({"status": "ok"}), 200