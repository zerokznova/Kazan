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
SUPORTE_LINK = "https://t.me/pixxain"

# Bases disponíveis
BASES_BASICAS = ["cpf", "nome", "telefone", "cnpj"]
BASES_VIP = ["rg", "rgsimpl", "pis", "titulo", "email", "cns", "mae", "pai", "placa", "chassi", "renavam", "motor", "fotorj", "fotosp", "funcionarios", "razao"]
BASES = BASES_BASICAS + BASES_VIP

def calcular_idade(data_nascimento):
    if not data_nascimento:
        return ""
    try:
        nasc = datetime.strptime(data_nascimento.split()[0], "%Y-%m-%d")
        hoje = datetime.now()
        return hoje.year - nasc.year - ((hoje.month, hoje.day) < (nasc.month, nasc.day))
    except:
        return ""

def formatar_txt_cpf_free(dados):
    basicos = dados.get("data", {}).get("dadosBasicos", {})
    endereco = dados.get("data", {}).get("enderecos", [{}])[0]
    idade = calcular_idade(basicos.get("nasc", ""))
    
    conteudo = (
        f"🔍 CONSULTA CPF: {basicos.get('cpf', '')[:3]}.XXX.{basicos.get('cpf', '')[-3:]}-{basicos.get('cpf', '')[-2:]}\n"
        f"Status: ✅ Regular (atualizado em {datetime.now().strftime('%d/%m/%Y')})\n\n"
        f"📌 DADOS PESSOAIS\n"
        f"- Nome: {basicos.get('nome', 'NÃO ENCONTRADO')}\n"
        f"- Nascimento: {basicos.get('nasc', '').split()[0] if basicos.get('nasc') else ''} ({idade} anos)\n"
        f"- Sexo: {basicos.get('sexo', '').capitalize()}\n"
        f"- Filiação:\n"
        f"  - Mãe: {basicos.get('filiacao', {}).get('nomeMae', 'NÃO ENCONTRADO')}\n"
        f"  - Pai: {basicos.get('filiacao', {}).get('nomePai', 'NÃO ENCONTRADO')}\n\n"
        f"📍 CIDADE/UF: {endereco.get('cidade', '')}/{endereco.get('siglaUf', '')}\n\n"
        f"🔒 Dados completos disponíveis para assinantes VIP\n"
        f"💎 Acesse com /vip"
    )
    return conteudo

def formatar_txt_telefone_free(dados):
    telefone = dados.get("telefone", "NÃO ENCONTRADO")
    operadora = dados.get("operadora", "NÃO ENCONTRADA")
    proprietario = dados.get("proprietario", {}).get("nome", "NÃO ENCONTRADO")
    documento = dados.get("proprietario", {}).get("documento", "NÃO ENCONTRADO")
    endereco = dados.get("endereco", {})
    
    conteudo = (
        f"📞 TELEFONE: {telefone}\n\n"
        f"📡 OPERADORA: {operadora}\n\n"
        f"🏢 PROPRIETÁRIO/NOME: {proprietario}\n\n"
        f"🔢 CNPJ/CPF: {documento}\n\n"
        f"📍 CIDADE/UF: {endereco.get('cidade', '')}/{endereco.get('uf', '')}\n"
        f"📮 CEP: {endereco.get('cep', '')[:5]}-{endereco.get('cep', '')[5:] if len(endereco.get('cep', '')) > 5 else ''}\n\n"
        f"🔒 Endereço completo disponível para VIP\n"
        f"💎 Acesse com /vip"
    )
    return conteudo

async def enviar_resposta_completa(update: Update, comando: str, argumento: str, is_vip: bool):
    try:
        url = f"{API_URL}?Access-Key={API_KEY}&Base={comando}&Info={argumento}"
        r = requests.get(url, timeout=15)
        
        if r.status_code != 200 or not r.text.strip():
            return await update.message.reply_text("⚠️ Nenhum dado encontrado.")
        
        dados = r.json()
        nome_arquivo = f"{comando}_{argumento.replace(' ', '_')}.txt"
        caminho = f"/data/data/com.termux/files/home/Kazan/{nome_arquivo}"
        
        if not is_vip:
            if comando == "cpf":
                conteudo = formatar_txt_cpf_free(dados)
            elif comando == "telefone":
                conteudo = formatar_txt_telefone_free(dados)
            else:
                conteudo = json.dumps(dados, indent=4, ensure_ascii=False)
        else:
            conteudo = json.dumps(dados, indent=4, ensure_ascii=False)
        
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(conteudo)
        
        username = f"@{update.message.from_user.username}" if update.message.from_user.username else "Usuário"
        mensagem = (
            f"🔎 Consulta completa dentro do arquivo!\n\n"
            f"• BASE: {comando.upper()}\n"
            f"• PESQUISA: {argumento}\n\n"
            f"🤖 Bot: @Kazanovabuscas_bot\n"
            f"👤 Usuário: {username}"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("💎 Assinar VIP", url=PLAN_LINK),
                InlineKeyboardButton("🗣️ Suporte", url=f"{SUPORTE_LINK}?start=Olá,pixxain, gostaria de iniciar meu atendimento!")
            ]
        ]
        
        await update.message.reply_text(
            mensagem,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        with open(caminho, "rb") as f:
            await update.message.reply_document(
                document=InputFile(f, filename=nome_arquivo),
                reply_markup=InlineKeyboardMarkup(keyboard) if not is_vip else None
            )
        
        os.remove(caminho)

    except Exception as e:
        print(f"Erro: {e}")
        await update.message.reply_text("❌ Erro na consulta")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        return
    
    user = update.message.from_user
    username = f"@{user.username}" if user.username else user.first_name
    
    keyboard = [
        [InlineKeyboardButton("➕ Adicionar bot ao grupo", url="https://t.me/Kazanovabuscas_bot?startgroup=true")],
        [
            InlineKeyboardButton("🗣️ Suporte", url=f"{SUPORTE_LINK}?start=Olá,pixxain, gostaria de iniciar meu atendimento!"),
            InlineKeyboardButton("📚 Comandos", callback_data="show_commands")
        ],
        [InlineKeyboardButton("💎 Adquirir assinatura", url=PLAN_LINK)]
    ]
    
    await update.message.reply_text(
        f"👋 Olá, {username}, Bem-vindo ao nosso sistema de buscas avançadas!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "show_commands":
        mensagem = (
            "📚 COMANDOS DISPONÍVEIS:\n\n"
            "🔍 BASES GRÁTIS:\n"
            "/cpf [número] - Ex: /cpf 12345678901\n"
            "/telefone [número] - Ex: /telefone 11987654321\n"
            "/nome [nome] - Ex: /nome João Silva\n"
            "/cnpj [número] - Ex: /cnpj 12345678000101\n\n"
            "💎 BASES VIP:\n" + " | ".join([f"/{base}" for base in BASES_VIP])
        )
        await query.message.reply_text(mensagem)

async def handle_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    
    comando = update.message.text.split()[0][1:].lower()
    argumento = " ".join(context.args)
    chat_id = update.message.chat_id
    is_vip = chat_id == GRUPO_VIP_ID

    if comando in BASES_VIP and not is_vip:
        return await update.message.reply_text(
            "🔒 Esta base é exclusiva para assinantes VIP",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💎 Assinar Agora", url=PLAN_LINK)]
            ])
        )
    
    if comando not in BASES:
        return await update.message.reply_text("❌ Base inválida. Use /start para ver comandos.")
    
    if not argumento:
        return await update.message.reply_text(f"⚠️ Uso: /{comando} <dado>\nEx: /{comando} {'12345678901' if comando in ['cpf','cnpj'] else 'dado'}")
    
    await update.message.reply_text("🔎 Buscando dados...")
    await enviar_resposta_completa(update, comando, argumento, is_vip)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    for base in BASES:
        app.add_handler(CommandHandler(base, handle_comando))
    
    print("🤖 Bot rodando!")
    app.run_polling()

if __name__ == "__main__":
    main()
