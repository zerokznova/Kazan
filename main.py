import os
import json
import requests
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

# Configurações
TOKEN = "7727164066:AAFZmMo0RSI7RqwwLKa1aTKl50nSMr2bYoI"
API_KEY = "WM3t-Av5u-thfP-GiBV-sM3B"
API_URL = "https://voidsearch.localto.net/api/search"
GRUPO_VIP_ID = -1002281290193
PLAN_LINK = "https://t.me/assinaturakazanova_bot"

# Bases disponíveis
BASES_BASICAS = ["cpf", "nome", "telefone", "cnpj"]
BASES_VIP = ["rg", "rgsimpl", "pis", "titulo", "email", "cns", "mae", "pai", "placa", "chassi", "renavam", "motor", "fotorj", "fotosp", "funcionarios", "razao"]
BASES = BASES_BASICAS + BASES_VIP

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        return
    keyboard = [
        [InlineKeyboardButton("➕ Adicionar bot ao grupo", url="https://t.me/Kazanovabuscas_bot?startgroup=true")],
        [InlineKeyboardButton("💳 Adquirir assinatura", url=PLAN_LINK)]
    ]
    await update.message.reply_text(
        "Bem-vindo ao Kazanova Bot! Use os botões abaixo para adicionar ao grupo ou adquirir um plano.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    comando = update.message.text.split()[0][1:].lower()
    argumento = " ".join(context.args)
    chat_id = update.message.chat_id

    if comando not in BASES:
        return await update.message.reply_text("❌ Base inválida.")
    if not argumento:
        return await update.message.reply_text(f"Uso correto: /{comando} <dado>")

    await update.message.reply_text("🔎 Buscando dados, por favor aguarde...")

    try:
        url = f"{API_URL}?Access-Key={API_KEY}&Base={comando}&Info={argumento}"
        r = requests.get(url, timeout=15)
        if r.status_code != 200 or not r.text.strip() or "error" in r.text.lower():
            return await update.message.reply_text("⚠️ Nenhum dado encontrado.")

        dados = r.json()
        conteudo = json.dumps(dados, indent=4, ensure_ascii=False)

        # Se não for grupo VIP
        if chat_id != GRUPO_VIP_ID:
            if comando == "cpf":
                conteudo = conteudo.replace("\"logradouro\": \"", "\"logradouro\": \"🔒 Disponível para assinantes")
                conteudo = conteudo.replace("\"numero\": \"", "\"numero\": \"🔒 Disponível para assinantes")
                conteudo = conteudo.replace("\"bairro\": \"", "\"bairro\": \"🔒 Disponível para assinantes")
                conteudo = conteudo.replace("\"cep\": \"", "\"cep\": \"🔒 Disponível para assinantes")
                conteudo = conteudo.replace("\"telefones\": ", "\"telefones: 🔒 Disponível para assinantes\": ")
                conteudo = conteudo.replace("\"email\": ", "\"email: 🔒 Disponível para assinantes\": ")
                conteudo = conteudo.replace("\"vizinhos\": ", "\"vizinhos: 🔒 Disponível para assinantes\": ")
                conteudo = conteudo.replace("\"parentes\": ", "\"parentes: 🔒 Disponível para assinantes\": ")
            elif comando in BASES_VIP:
                return await update.message.reply_text(
                    "🔒 Essa base é exclusiva para assinantes. Clique abaixo para adquirir um plano:",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("💳 Adquirir assinatura", url=PLAN_LINK)]
                    ])
                )

        nome_arquivo = f"{comando}_{argumento.replace(' ', '_')}.txt"
        caminho = f"/data/data/com.termux/files/home/Kazan/{nome_arquivo}"

        with open(caminho, "w", encoding="utf-8") as f:
            f.write("🔎 CONSULTA COMPLETA\n\n")
            f.write(f"• Base: {comando}\n")
            f.write(f"• Dado pesquisado: {argumento}\n\n")
            f.write(conteudo)

        with open(caminho, "rb") as f:
            await update.message.reply_document(
                document=InputFile(f, filename=nome_arquivo),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💳 Adquirir assinatura", url=PLAN_LINK)]
                ]) if chat_id != GRUPO_VIP_ID else None
            )
        os.remove(caminho)

    except Exception as e:
        print("Erro:", e)
        await update.message.reply_text("❌ Erro inesperado durante a busca.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "show_commands":
        await query.message.reply_text(
            "Comandos Básicos:\n/cpf /cnpj /telefone /nome\n\nComandos VIP:\n" + " ".join(f"/{b}" for b in BASES_VIP)
        )

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    for base in BASES:
        app.add_handler(CommandHandler(base, handle_comando))
    print("🤖 Bot rodando...")
    app.run_polling()

if __name__ == "__main__":
    main()
