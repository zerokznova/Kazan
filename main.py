# coding: utf-8
import os
import json
import time
import requests
from telegram import (
    Update, InputFile,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler,
    ContextTypes, CallbackQueryHandler
)

# 🔐 Configurações
TOKEN = "7727164066:AAFZmMo0RSI7RqwwLKa1aTKl50nSMr2bYoI"
API_KEY = "WM3t-Av5u-thfP-GiBV-sM3B"
API_URL = "https://voidsearch.localto.net/api/search"
ASSINANTES_FILE = "assinantes.json"
ADMIN_ID = 7889164760

# 💳 Links de planos
PLAN_LINKS = {
    "2h":    "https://p.hoopay.com.br/v/e3edbe70-468f-46f9-8af1-e167d929575a",
    "diario": "https://p.hoopay.com.br/v/b6c7ed80-b1e5-436f-ba43-9a955088d801",
    "semanal": "https://p.hoopay.com.br/v/70000bfc-474f-4bb1-ac45-ea6c2c621db2",
    "mensal": "https://p.hoopay.com.br/v/a0713b5b-ed8c-4c84-b0be-f4861a61177b"
}

# 📚 Bases
BASES = [
    "cpf", "cpfsimpl", "cnpj", "rg", "rgsimpl", "nome", "pis", "titulo",
    "telefone", "email", "cns", "mae", "pai", "placa", "chassi", "renavam",
    "motor", "fotorj", "fotosp", "funcionarios", "razao"
]
BASES_LIVRES = ["cpf", "nome", "telefone", "mae", "pai"]

# 📂 Utilitários
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
    expira = assinantes.get(str(user_id), {}).get("expira", 0)
    return time.time() < expira

# ▶️ /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ Adicionar bot ao grupo", url="https://t.me/Kazanovabuscas_bot?startgroup=true")],
        [InlineKeyboardButton("💬 Suporte 24h", url="https://t.me/pixxain")],
        [InlineKeyboardButton("💳 Adquirir plano", callback_data="show_plans")],
        [InlineKeyboardButton("🧾 Comandos", callback_data="show_commands")]
    ]
    await update.message.reply_text(
        "👋 *Bem-vindo ao Kazanova Bot!*\n\n"
        "Digite `/comando <dado>` para buscar.\n"
        "Ex: `/cpf 12345678900`\n\n"
        "Comandos disponíveis:\n" + ", ".join(f"/{b}" for b in BASES),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# 🔘 Callback buttons
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "show_plans":
        keyboard = [
            [InlineKeyboardButton("🧪 Teste 2h (R$1)", callback_data="plan_2h")],
            [InlineKeyboardButton("📅 Diário (R$9,90)", callback_data="plan_diario")],
            [InlineKeyboardButton("🗓️ Semanal (R$24,90)", callback_data="plan_semanal")],
            [InlineKeyboardButton("📆 Mensal (R$29,90)", callback_data="plan_mensal")],
        ]
        await query.message.reply_text(
            "🌟 *Você selecionou um dos planos:*\n\nEscolha abaixo:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if data.startswith("plan_"):
        _, plano = data.split("_", 1)
        link = PLAN_LINKS.get(plano)
        valor = {
            "2h": "R$1,00", "diario": "R$9,90",
            "semanal": "R$24,90", "mensal": "R$29,90"
        }.get(plano, "")
        suporte = "https://t.me/pixxain?text=acabei%20de%20adquirir%20o%20bot%2Clibere%20meu%20acesso"
        texto = (
            f"🌟 *Você selecionou o seguinte plano:*\n\n"
            f"🎁 *Plano:* ✨ *{plano.upper()}*\n"
            f"💰 *Valor:* {valor}\n\n"
            f"💠 *Pague via Pix:*\n{link}\n\n"
            f"Após pagar, clique abaixo para verificar com o suporte:"
        )
        await query.message.reply_text(
            texto,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Verificar status ✅", url=suporte)]
            ])
        )

    elif data == "show_commands":
        await query.message.reply_text(
            "🧾 *Comandos e exemplos:*\n\n"
            "`/cpf 14043672764`\n"
            "`/cnpj 31499929000130`\n"
            "`/nome Jair Messias Bolsonaro`\n"
            "`/telefone 21992305416`\n"
            "`/placa NCF5440`\n"
            "`/titulo 057921670698`\n"
            "`/email maria@gmail.com`\n"
            "`/funcionarios 12345678000123`\n"
            "`/rg 1234567`\n"
            "`/cns 705005484822659`\n"
            "`/chassi 9BWAA05Z8A4073612`\n"
            "`/renavam 173908462`\n"
            "`/mae Maria de Lourdes`\n"
            "`/pai José Vieira`\n",
            parse_mode="Markdown"
        )

# 🔎 Busca de dados
async def handle_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    comando = update.message.text.split()[0][1:]
    argumento = " ".join(context.args)
    user = update.effective_user
    user_id = user.id
    username = user.username or "usuário_desconhecido"
    chat_type = update.message.chat.type

    if comando not in BASES:
        return await update.message.reply_text("❌ Base inválida.")
    if not argumento:
        return await update.message.reply_text(f"⚠️ Uso correto: /{comando} <dado>")
    if chat_type != "private" and comando not in BASES_LIVRES:
        return await update.message.reply_text("🔒 Base disponível somente no privado com plano ativo.")
    if chat_type == "private" and comando not in BASES_LIVRES and not tem_assinatura(user_id):
        return await update.message.reply_text("🔒 Você precisa de um plano ativo.")

    await update.message.reply_text("🔎 Buscando dados, por favor aguarde...")

    try:
        url = f"{API_URL}?Access-Key={API_KEY}&Base={comando}&Info={argumento}"
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            return await update.message.reply_text("❌ Erro na API.")
        resposta_api = r.text.strip()
        if not resposta_api or "error" in resposta_api.lower():
            return await update.message.reply_text("⚠️ Nenhum dado encontrado.")

        texto = (
            "🔎 Consulta completa dentro do arquivo\n\n"
            f"• Base: {comando}\n"
            f"• Dado pesquisado: {argumento}\n\n"
            f"Bot: @Kazanovabuscas_bot\n"
            f"Usuário: @{username}\n\n"
            f"{resposta_api}"
        )

        nome_arquivo = f"{comando}_{argumento.replace(' ', '_')}.txt"
        caminho = f"/data/data/com.termux/files/home/Kazan/{nome_arquivo}"

        with open(caminho, "w", encoding="utf-8") as f:
            f.write(texto)

        reply_markup = None
        if chat_type != "private":
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 Buscas Avançadas", url="https://t.me/Kazanovabuscas_bot")]
            ])

        with open(caminho, "rb") as f:
            await update.message.reply_document(
                InputFile(f, filename=nome_arquivo),
                reply_markup=reply_markup
            )
        os.remove(caminho)

    except requests.exceptions.Timeout:
        await update.message.reply_text("⏳ Tempo esgotado tentando acessar a API.")
    except Exception as e:
        print("Erro:", e)
        await update.message.reply_text("❌ Ocorreu um erro inesperado.")

# 🔓 Liberar manual
async def liberar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        user_id = context.args[0]
        dias = int(context.args[1])
        assinantes = carregar_assinantes()
        assinantes[user_id] = {"expira": time.time() + dias * 86400}
        salvar_assinantes(assinantes)
        await update.message.reply_text(f"✅ Usuário {user_id} liberado por {dias} dias.")
    except:
        await update.message.reply_text("Uso: /liberar <user_id> <dias>")

# ▶️ Iniciar bot
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(CommandHandler("liberar", liberar))
    for b in BASES:
        app.add_handler(CommandHandler(b, handle_comando))
    print("🤖 Bot rodando...")
    app.run_polling()

if __name__ == "__main__":
    main()
