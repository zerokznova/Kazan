
import requests
from telegram import Bot, ParseMode
from telegram.ext import Updater, CommandHandler
import html

# Token do seu bot
TOKEN = '7727164066:AAFZmMo0RSI7RqwwLKa1aTKl50nSMr2bYoI'
BASE_URL = 'https://voidsearch.localto.net/api/search'
API_KEY = 'WM3t-Av5u-thfP-GiBV-sM3B'

bot = Bot(TOKEN)
updater = Updater(bot=bot, use_context=True)
dispatcher = updater.dispatcher

def format_bold(text):
    return f"<b>{text}</b>"

def format_error(error):
    return f"⚠️ {error}"

def make_request(base, info):
    url = f"{BASE_URL}?Access-Key={API_KEY}&Base={base}&Info={info}"
    response = requests.get(url)
    return response.json()

def create_handler(base):
    def handler(update, context):
        try:
            info = ' '.join(context.args)
            if not info:
                raise Exception("Informe o dado para consulta.")
            data = make_request(base, info)
            if 'error' in data:
                raise Exception(data['error'])
            result = f"<b>RESULTADO ({base.upper()}):</b>\n" + html.escape(str(data))
            context.bot.send_message(chat_id=update.effective_chat.id, text=result, parse_mode=ParseMode.HTML)
        except Exception as e:
            context.bot.send_message(chat_id=update.effective_chat.id, text=format_error(str(e)), parse_mode=ParseMode.HTML)
    return handler

# Lista de comandos e suas respectivas bases
comandos_bases = [
    'cpf', 'cnpj', 'rg', 'cpfsimpl', 'rgsimpl', 'nome', 'pis', 'titulo', 'telefone', 'email',
    'cns', 'mae', 'pai', 'placa', 'chassi', 'renavam', 'motor', 'fotorj', 'fotosp',
    'funcionarios', 'razao'
]

# Registrar todos os comandos dinamicamente
for comando in comandos_bases:
    handler = CommandHandler(comando, create_handler(comando))
    dispatcher.add_handler(handler)

def start(update, context):
    comandos = '\n'.join([f"/{cmd}" for cmd in comandos_bases])
    msg = f"<b>🧠 BOT DE CONSULTAS - VOIDSEARCH</b>\n\n<b>Comandos disponíveis:</b>\n{comandos}"
    context.bot.send_message(chat_id=update.effective_chat.id, text=msg, parse_mode=ParseMode.HTML)

dispatcher.add_handler(CommandHandler('start', start))

updater.start_polling()
updater.idle()
