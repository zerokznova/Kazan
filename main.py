import os
import json
import requests
from datetime import datetime
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
BASES_VIP = ["rg", "placa", "chassi", "renavam", "motor", "email", "pis", "titulo"]
BASES = BASES_BASICAS + BASES_VIP

def calcular_idade(data_nascimento):
    try:
        nasc = datetime.strptime(data_nascimento.split()[0], "%Y-%m-%d")
        hoje = datetime.now()
        return hoje.year - nasc.year - ((hoje.month, hoje.day) < (nasc.month, nasc.day))
    except:
        return ""

async def formatar_resposta_cpf_free(dados):
    """Formata a resposta de CPF para grupos grátis"""
    if not dados.get("data"):
        return "⚠️ Dados não encontrados"
    
    basicos = dados["data"].get("dadosBasicos", {})
    idade = calcular_idade(basicos.get("nasc", ""))
    
    return (
        f"🔍 CONSULTA CPF: {basicos.get('cpf', '')[:3]}.XXX.{basicos.get('cpf', '')[5:8]}-{basicos.get('cpf', '')[9:]}\n"
        f"Status: ✅ Regular (atualizado em {datetime.now().strftime('%d/%m/%Y')}\n\n"
        f"📌 DADOS PESSOAIS\n"
        f"- Nome: {basicos.get('nome', 'NÃO ENCONTRADO')}\n"
        f"- Nascimento: {basicos.get('nasc', '').split()[0]} ({idade} anos)\n"
        f"- Sexo: {basicos.get('sexo', '').capitalize()}\n"
        f"- Raça/Cor: {basicos.get('racaCor', '').split('(')[0]}\n"
        f"- Filiação:\n"
        f"  - Mãe: {basicos.get('filiacao', {}).get('nomeMae', 'NÃO ENCONTRADO')}\n"
        f"  - Pai: {basicos.get('filiacao', {}).get('nomePai', 'NÃO ENCONTRADO')}\n\n"
        f"📄 DOCUMENTOS\n"
        f"- RG: Disponível para assinantes\n"
        f"- CNS: Disponível para assinantes\n\n"
        f"📍 ENDEREÇO\n"
        f"- Logradouro: Disponível para assinantes\n"
        f"- Número: Disponível para assinantes\n"
        f"- Bairro: Disponível para assinantes\n"
        f"- Cidade/UF: {dados['data']['enderecos'][0]['cidade'] if dados['data'].get('enderecos') else ''}\n"
        f"- CEP: {dados['data']['enderecos'][0]['cep'][:5] + '-' + dados['data']['enderecos'][0]['cep'][5:] if dados['data'].get('enderecos') else ''}\n\n"
        f"🏥 SAÚDE SUPLEMENTAR\n"
        f"- Plano de Saúde: Disponível para assinantes\n"
        f"- Valor: Disponível para assinantes\n"
        f"- Contrato desde: Disponível para assinantes"
    )

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
    is_vip = chat_id == GRUPO_VIP_ID

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

        # Verifica se é base VIP em grupo free
        if comando in BASES_VIP and not is_vip:
            return await update.message.reply_text(
                "🔒 Esta base é exclusiva para assinantes VIP",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💎 Assinar Agora", url=PLAN_LINK)]
                ])
            )
        
        # Resposta especial para CPF em grupos free
        if comando == "cpf" and not is_vip:
            resposta = await formatar_resposta_cpf_free(dados)
            return await update.message.reply_text(
                resposta,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💎 Assinar VIP", url=PLAN_LINK)]
                ])
            )
        
        # Para outras bases ou VIPs - envia TXT
        nome_arquivo = f"{comando}_{argumento.replace(' ', '_')}.txt"
        caminho = f"/data/data/com.termux/files/home/Kazan/{nome_arquivo}"
        
        with open(caminho, "w", encoding="utf-8") as f:
            f.write("🔎 CONSULTA COMPLETA\n\n")
            f.write(f"• Base: {comando}\n")
            f.write(f"• Dado pesquisado: {argumento}\n\n")
            f.write(json.dumps(dados, indent=4, ensure_ascii=False))
        
        with open(caminho, "rb") as f:
            await update.message.reply_document(
                document=InputFile(f, filename=nome_arquivo),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💎 Assinar VIP", url=PLAN_LINK)]
                ]) if not is_vip else None
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
