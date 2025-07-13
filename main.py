import os
import json
import time
import requests
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

TOKEN = "7727164066:AAFZmMo0RSI7RqwwLKa1aTKl50nSMr2bYoI"
API_KEY = "WM3t-Av5u-thfP-GiBV-sM3B"
API_URL = "https://voidsearch.localto.net/api/search"
ASSINANTES_FILE = "assinantes.json"
ADMIN_ID = 7889164760

BASES = [
    "cpf", "cpfsimpl", "cnpj", "rg", "rgsimpl", "nome", "pis", "titulo",
    "telefone", "email", "cns", "mae", "pai", "placa", "chassi", "renavam",
    "motor", "fotorj", "fotosp", "funcionarios", "razao"
]

BASES_LIVRES = ["cpf", "nome", "telefone", "mae", "pai"]

# Utilitários
def carregar_assinantes():
    if os.path.exists(ASSINANTES_FILE):
        with open(ASSINANTES_FILE, "r") as f:
            return json.load(f)
    return {}

def salvar_assinantes(assinantes):
    with open(ASSINANTES_FILE, "w") as f:
        json.dump(assinantes, f)

def tem_assinatura(user_id):
    assinantes = carregar_assinantes()
    expira_em = assinantes.get(str(user_id))
    return expira_em and time.time() < expira_em

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ Adicionar bot ao grupo", url="https://t.me/Kazanovabuscas_bot?startgroup=true")],
        [InlineKeyboardButton("💬 Suporte 24h", url="https://t.me/pixxain")],
        [InlineKeyboardButton("💳 Adquirir plano", url="https://t.me/Kazanovabuscas_bot")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Bem-vindo ao *Black Consultas!*\n\n"
        "Digite /comando <dado>\nEx: /cpf 12345678900\n\n"
        "Comandos disponíveis:\n" + ", ".join(f"/{b}" for b in BASES),
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

# Consulta
async def handle_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    comando = update.message.text.split()[0][1:]
    argumento = " ".join(context.args)
    user_id = update.effective_user.id

    if comando not in BASES:
        await update.message.reply_text("❌ Base inválida.")
        return

    if not argumento:
        await update.message.reply_text(f"⚠️ Uso correto: /{comando} <dado>")
        return

    if update.message.chat.type != "private" and comando not in BASES_LIVRES:
        await update.message.reply_text("🔒 Essa base só está disponível no privado para usuários com plano ativo.")
        return

    if update.message.chat.type == "private" and not tem_assinatura(user_id) and comando not in BASES_LIVRES:
        await update.message.reply_text("🔒 Você precisa de um plano ativo para usar essa base.")
        return

    url = f"{API_URL}?Access-Key={API_KEY}&Base={comando}&Info={argumento}"

    try:
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            await update.message.reply_text("❌ Erro na API.")
            return

        data = response.text.strip()
        if not data or "error" in data.lower():
            await update.message.reply_text("⚠️ Nenhum dado encontrado.")
            return

        temp_file = f"/data/data/com.termux/files/home/Kazan/{comando}_{argumento}.txt"
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(data)

        if update.message.chat.type == "private":
            with open(temp_file, "rb") as f:
                await update.message.reply_document(InputFile(f, filename=f.name))
        else:
            keyboard = [
                [InlineKeyboardButton("💳 Adquirir plano", url="https://t.me/Kazanovabuscas_bot")],
                [InlineKeyboardButton("❌ Apagar consulta", callback_data=f"apagar|{update.message.chat.id}|{update.message.message_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            with open(temp_file, "rb") as f:
                await update.message.reply_document(InputFile(f, filename=f.name), reply_markup=reply_markup)

        os.remove(temp_file)

    except Exception as e:
        await update.message.reply_text("❌ Ocorreu um erro inesperado.")
        print(f"Erro: {e}")

# Callback: apagar consulta
async def callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data.startswith("apagar"):
        try:
            _, chat_id, msg_id = query.data.split("|")
            await context.bot.delete_message(chat_id=int(chat_id), message_id=int(msg_id))
            await context.bot.delete_message(chat_id=int(chat_id), message_id=query.message.message_id)
        except Exception as e:
            print("Erro ao apagar mensagem:", e)

# Admin: /liberar <id> <dias>
async def liberar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        user_id = context.args[0]
        dias = int(context.args[1])
        expira_em = time.time() + dias * 86400
        assinantes = carregar_assinantes()
        assinantes[user_id] = expira_em
        salvar_assinantes(assinantes)
        await update.message.reply_text(f"✅ Usuário {user_id} liberado por {dias} dias.")
    except:
        await update.message.reply_text("Uso correto: /liberar <id> <dias>")

# Admin: /planos
async def planos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    assinantes = carregar_assinantes()
    msg = "📋 *Planos Ativos:*\n\n"
    for uid, ts in assinantes.items():
        if time.time() < ts:
            data = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))
            msg += f"👤 ID: {uid}\n📆 Expira em: {data}\n\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

# Admin: /cancelar <id>
async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        user_id = context.args[0]
        assinantes = carregar_assinantes()
        if user_id in assinantes:
            del assinantes[user_id]
            salvar_assinantes(assinantes)
            await update.message.reply_text(f"❌ Plano do usuário {user_id} cancelado.")
        else:
            await update.message.reply_text("Usuário não encontrado.")
    except:
        await update.message.reply_text("Uso correto: /cancelar <id>")

# Inicialização
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("liberar", liberar))
    app.add_handler(CommandHandler("planos", planos))
    app.add_handler(CommandHandler("cancelar", cancelar))
    app.add_handler(CallbackQueryHandler(callback_query))

    for base in BASES:
        app.add_handler(CommandHandler(base, handle_comando))

    print("Bot rodando...")
    app.run_polling()

if __name__ == "__main__":
    main()
