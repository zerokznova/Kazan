import requests
from telegram import Bot, ParseMode
from telegram.ext import Updater, CommandHandler
import html
from datetime import datetime

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

def format_date(date_str):
    try:
        return datetime.strptime(date_str[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except:
        return date_str

def format_response(base, data):
    base = base.lower()
    msg = f"<b>📌 Kazanova buscas:</b>\n<b>RESULTADO ({base.upper()}):</b>\n\n"
    try:
        d = data.get("data", {})
        if base == "cpf":
            nome = d.get("dadosBasicos", {}).get("nome", "")
            cpf = d.get("dadosBasicos", {}).get("cpf", "")
            nasc = format_date(d.get("dadosBasicos", {}).get("nasc", ""))
            score = d.get("dadosBasicos", {}).get("scoreFaixa", "")
            poder = d.get("poderAquisitivo", {}).get("poderAquisitivo", "")
            vacina = ""
            if d.get("vacinas"):
                v = d["vacinas"][0]
                vacina = f"{v.get('vacinaNome', '')} ({v.get('descricao', '')} em {format_date(v.get('dataAplicacao', ''))})"
            msg += f"👤 Nome: {nome}\n🆔 CPF: {cpf}\n📅 Nascimento: {nasc}\n📈 Score: {score}\n💰 Poder aquisitivo: {poder}"
            if vacina:
                msg += f"\n💉 Vacina: {vacina}"
        elif base == "telefone":
            if isinstance(d, list) and d:
                item = d[0]
                msg += f"📞 Telefone: {item.get('telefone', '')}\n👤 Nome: {item.get('nome', '')}\n🆔 CPF/CNPJ: {item.get('cpfCnpj', '')}"
                end = item.get("endereco", {})
                if end:
                    endereco = f"{end.get('logradouro', '')}, {end.get('numero', '')} - {end.get('bairro', '')}"
                    cidade = f"{end.get('cidade', '')} - {end.get('siglaUf', '')}, CEP: {end.get('cep', '')}"
                    msg += f"\n📍 Endereço: {endereco}\n🏙️ Cidade: {cidade}"
        elif base == "nome":
            if isinstance(d, list):
                for pessoa in d[:5]:
                    msg += f"👤 Nome: {pessoa.get('nome', '')}\n🆔 CPF: {pessoa.get('cpf', '')}\n📅 Nascimento: {format_date(pessoa.get('nasc', ''))}\n👩‍👧 Mãe: {pessoa.get('nomeMae', '')}\n---\n"
        elif base == "placa":
            msg += f"🚘 Placa: {d.get('placaMercosul', '')}\n🔧 Motor: {d.get('motor', '')}\n🧾 Chassi: {d.get('chassi', '')}\n🚗 Modelo: {d.get('caracteristicas', {}).get('marcaModelo', '')}\n🎨 Cor: {d.get('caracteristicas', {}).get('corVeiculo', '')}\n🛑 Situação: {d.get('circulacao', {}).get('situacaoVeiculo', '')}"
        else:
            msg += html.escape(str(d))
    except Exception as e:
        msg = format_error(f"Erro ao formatar resposta: {e}")
    return msg

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
            resultado = format_response(base, data)
            context.bot.send_message(chat_id=update.effective_chat.id, text=resultado, parse_mode=ParseMode.HTML)
        except Exception as e:
            context.bot.send_message(chat_id=update.effective_chat.id, text=format_error(str(e)), parse_mode=ParseMode.HTML)
    return handler

comandos_bases = [
    'cpf', 'cnpj', 'rg', 'cpfsimpl', 'rgsimpl', 'nome', 'pis', 'titulo', 'telefone', 'email',
    'cns', 'mae', 'pai', 'placa', 'chassi', 'renavam', 'motor', 'fotorj', 'fotosp',
    'funcionarios', 'razao'
]

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
