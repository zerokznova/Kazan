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

# 🔐 Configurações gerais
TOKEN = "7727164066:AAFZmMo0RSI7RqwwLKa1aTKl50nSMr2bYoI"
API_KEY = "WM3t-Av5u-thfP-GiBV-sM3B"
API_URL = "https://voidsearch.localto.net/api/search"
ASSINANTES_FILE = "assinantes.json"
ADMIN_ID = 7889164760

# 📦 Links de pagamento HooPay por plano
PLAN_LINKS = {
    "2h":    "https://p.hoopay.com.br/v/e3edbe70-468f-46f9-8af1-e167d929575a",
    "diario":"https://p.hoopay.com.br/v/b6c7ed80-b1e5-436f-ba43-9a955088d801",
    "semanal":"https://p.hoopay.com.br/v/70000bfc-474f-4bb1-ac45-ea6c2c621db2",
    "mensal":"https://p.hoopay.com.br/v/a0713b5b-ed8c-4c84-b0be-f4861a61177b"
}

# 🔍 Bases de consulta
BASES = [
    "cpf", "cpfsimpl", "cnpj", "rg", "rgsimpl", "nome", "pis", "titulo",
    "telefone", "email", "cns", "mae", "pai", "placa", "chassi", "renavam",
    "motor", "fotorj", "fotosp", "funcionarios", "razao"
]
BASES_LIVRES = ["cpf", "nome", "telefone", "mae", "pai"]

# ─── Helpers ──────────────────────────────────────────────────────────────────

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

# ─── Comando /start ──────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [ InlineKeyboardButton("➕ Adicionar bot ao grupo",
            url="https://t.me/Kazanovabuscas_bot?startgroup=true") ],
        [ InlineKeyboardButton("💬 Suporte 24h", url="https://t.me/pixxain") ],
        [ InlineKeyboardButton("💳 Adquirir plano", callback_data="show_plans") ],
    ]
    await update.message.reply_text(
        "👋 *Bem-vindo ao Kazanova Bot!*\n\n"
        "Digite `/comando <dado>` para buscar.\n"
        f"Ex: `/cpf 12345678900`\n\n"
        "Comandos disponíveis:\n" + ", ".join(f"/{b}" for b in BASES),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ─── Callback de Planos ──────────────────────────────────────────────────────

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "show_plans":
        keyboard = [
            [ InlineKeyboardButton("🧪 Teste 2h (R$1)", callback_data="plan_2h") ],
            [ InlineKeyboardButton("📅 Diário (R$9,90)", callback_data="plan_diario") ],
            [ InlineKeyboardButton("🗓️ Semanal (R$24,90)", callback_data="plan_semanal") ],
            [ InlineKeyboardButton("📆 Mensal (R$29,90)", callback_data="plan_mensal") ],
        ]
        await query.message.reply_text(
            "🌟 *Você selecionou um dos planos:*\n\n"
            "Escolha abaixo:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if data.startswith("plan_"):
        _, plano = data.split("_", 1)
        link = PLAN_LINKS.get(plano)
        valor = {
            "2h": "R$1,00",
            "diario": "R$9,90",
            "semanal": "R$24,90",
            "mensal": "R$29,90"
        }.get(plano, "")
        suporte_link = (
            "https://t.me/pixxain"
            "?text=acabei%20de%20adquirir%20o%20bot%2Clibere%20meu%20acesso"
        )
        text = (
            f"🌟 *Você selecionou o seguinte plano:*\n\n"
            f"🎁 *Plano:* ✨ *{plano.upper()}* ✨\n"
            f"💰 *Valor:* {valor}\n\n"
            f"💠 *Pague via Pix (Copia & Cola ou QR Code):*\n"
            f"{link}\n\n"
            f"👆 Clique no link acima para efetuar o pagamento.\n\n"
            f"‼️ Após o pagamento, clique no botão abaixo para verificar o status."
        )
        keyboard = [
            [ InlineKeyboardButton("Verificar status ✅", url=suporte_link) ]
        ]
        await query.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ─── Comando de Busca ────────────────────────────────────────────────────────

async def handle_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    comando = update.message.text.split()[0][1:]
    argumento = " ".join(context.args)
    user_id = update.effective_user.id

    if comando not in BASES:
        return await update.message.reply_text("❌ Base inválida.")
    if not argumento:
        return await update.message.reply_text(f"⚠️ Uso correto: /{comando} <dado>")
    if (update.message.chat.type != "private"
        and comando not in BASES_LIVRES):
        return await update.message.reply_text(
            "🔒 Base disponível somente no privado com plano ativo."
        )
    if (update.message.chat.type == "private"
        and comando not in BASES_LIVRES
        and not tem_assinatura(user_id)):
        return await update.message.reply_text(
            "🔒 Você precisa de um plano ativo."
        )

    await update.message.reply_text("🔎 Buscando dados, por favor aguarde...")
    url = f"{API_URL}?Access-Key={API_KEY}&Base={comando}&Info={argumento}"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            return await update.message.reply_text("❌ Erro na API.")
        data = r.text.strip()
        if not data or "error" in data.lower():
            return await update.message.reply_text("⚠️ Nenhum dado encontrado.")
        path = f"/data/data/com.termux/files/home/Kazan/{comando}_{argumento}.txt"
        with open(path, "w", encoding="utf-8") as f:
            f.write(data)
        with open(path, "rb") as f:
            await update.message.reply_document(
                InputFile(f, filename=os.path.basename(path))
            )
        os.remove(path)
    except requests.exceptions.Timeout:
        await update.message.reply_text("⏳ Tempo esgotado tentando acessar a API.")
    except Exception as e:
        print("Erro:", e)
        await update.message.reply_text("❌ Ocorreu um erro inesperado.")

# ─── Admin: /liberar manual ─────────────────────────────────────────────────

async def liberar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        user_id = context.args[0]
        dias = int(context.args[1])
        assinantes = carregar_assinantes()
        assinantes[user_id] = {"expira": time.time() + dias * 86400}
        salvar_assinantes(assinantes)
        await update.message.reply_text(
            f"✅ Usuário {user_id} liberado por {dias} dias."
        )
    except:
        await update.message.reply_text("Uso: /liberar <user_id> <dias>")

# ─── Main ───────────────────────────────────────────────────────────────────

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
