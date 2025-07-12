import os
import requests
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "7727164066:AAFZmMo0RSI7RqwwLKa1aTKl50nSMr2bYoI"
API_KEY = "WM3t-Av5u-thfP-GiBV-sM3B"
API_URL = "https://voidsearch.localto.net/api/search"

BASES = [
    "cpf", "cpfsimpl", "cnpj", "rg", "rgsimpl", "nome", "pis", "titulo",
    "telefone", "email", "cns", "mae", "pai", "placa", "chassi", "renavam",
    "motor", "fotorj", "fotosp", "funcionarios", "razao"
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bem-vindo ao *Kazanova Bot*!\n\n"
        "Digite /comando <dado>\n\n"
        "Ex: /cpf 12345678900\n\n"
        "Comandos disponíveis:\n" + ", ".join(f"/{b}" for b in BASES),
        parse_mode="Markdown"
    )

async def handle_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    comando = update.message.text.split()[0][1:]  # Remove a barra /
    argumento = " ".join(context.args)

    if comando not in BASES:
        await update.message.reply_text("❌ Base inválida.")
        return

    if not argumento:
        await update.message.reply_text(f"⚠️ Uso correto: /{comando} <dado>")
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

        with open(temp_file, "rb") as f:
            await update.message.reply_document(InputFile(f, filename=f"{comando}_{argumento}.txt"))

        os.remove(temp_file)

    except Exception as e:
        await update.message.reply_text("❌ Ocorreu um erro inesperado.")
        print(f"Erro: {e}")

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    for base in BASES:
        app.add_handler(CommandHandler(base, handle_comando))

    print("Bot rodando...")
    app.run_polling()

if __name__ == "__main__":
    main()
