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
BASES_BASICAS = ["nome", "telefone", "cnpj"]
BASES_VIP = ["rg", "rgsimpl", "pis", "titulo", "email", "cns", "mae", "pai", "placa", "chassi", "renavam", "motor", "fotorj", "fotosp", "funcionarios", "razao"]
BASES = ["cpf"] + BASES_BASICAS + BASES_VIP  # CPF agora é universal

def calcular_idade(data_nascimento):
    if not data_nascimento:
        return ""
    try:
        nasc = datetime.strptime(data_nascimento.split()[0], "%Y-%m-%d")
        hoje = datetime.now()
        return hoje.year - nasc.year - ((hoje.month, hoje.day) < (nasc.month, nasc.day))
    except:
        return ""

def formatar_resposta_cpf(dados):
    basicos = dados.get("data", {}).get("dadosBasicos", {})
    enderecos = dados.get("data", {}).get("enderecos", [{}])[0]
    telefones = dados.get("data", {}).get("telefones", [])
    idade = calcular_idade(basicos.get("nasc", ""))

    cpf = basicos.get("cpf", "")
    cpf_formatado = f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}" if len(cpf) == 11 else cpf

    tels_formatados = []
    for tel in telefones:
        numero = tel.get("numero", "")
        if len(numero) == 11:
            tels_formatados.append(f"({numero[:2]}) {numero[2:7]}-{numero[7:]}")
        else:
            tels_formatados.append(numero)

    resposta = (
        f"🔍 *CONSULTA CPF COMPLETA*\n\n"
        f"📌 *DADOS PESSOAIS*\n"
        f"• 🆔 CPF: `{cpf_formatado}`\n"
        f"• 📛 Nome: `{basicos.get('nome', 'NÃO ENCONTRADO')}`\n"
        f"• 🎂 Data Nasc.: `{basicos.get('nasc', '').split()[0] if basicos.get('nasc') else 'NÃO ENCONTRADO'}` ({idade} anos)\n"
        f"• ⚤ Sexo: `{basicos.get('sexo', '').capitalize()}`\n\n"
        f"👪 *FILIAÇÃO*\n"
        f"• 👩 Mãe: `{basicos.get('filiacao', {}).get('nomeMae', 'NÃO ENCONTRADO')}`\n"
        f"• 👨 Pai: `{basicos.get('filiacao', {}).get('nomePai', 'NÃO ENCONTRADO')}`\n\n"
        f"📍 *ENDEREÇO*\n"
        f"• 🏙️ Cidade/UF: `{enderecos.get('cidade', '')}/{enderecos.get('siglaUf', '')}`\n"
        f"• 📮 CEP: `{enderecos.get('cep', '')[:5]}-{enderecos.get('cep', '')[5:] if len(enderecos.get('cep', '')) > 5 else ''}`\n"
        f"• 🏡 Logradouro: `{enderecos.get('logradouro', '')}, {enderecos.get('numero', '')} - {enderecos.get('bairro', '')}`\n\n"
        f"📞 *TELEFONES* ({len(tels_formatados)})\n" + "\n".join([f"• 📱 `{tel}`" for tel in tels_formatados]) + "\n\n"
        f"⚙️ *DADOS ADICIONAIS*\n"
        f"• 📝 Situação Cadastral: `{basicos.get('situacaoCadastral', 'NÃO INFORMADA')}`\n"
        f"• 🏛️ Origem dos Dados: `{dados.get('data', {}).get('fonte', 'NÃO INFORMADA')}`\n\n"
        f"🔄 Atualizado em: `{datetime.now().strftime('%d/%m/%Y %H:%M')}`"
    )

    return resposta

def formatar_resposta_telefone(dados):
    if not dados.get("success", False) or not dados.get("data"):
        return "⚠️ Nenhum dado encontrado para este telefone"

    primeiro_registro = dados["data"][0]
    endereco = primeiro_registro.get("endereco", {})

    telefone = primeiro_registro.get("telefone", "N/D")
    telefone_formatado = f"({telefone[:2]}) {telefone[2:7]}-{telefone[7:]}" if len(telefone) == 11 else telefone

    cep = endereco.get("cep", "N/D")
    cep_formatado = f"{cep[:5]}-{cep[5:]}" if cep and len(cep) == 8 else cep

    resposta = (
        f"📞 *TELEFONE LOCALIZADO*\n\n"
        f"• 📱 Número: `{telefone_formatado}`\n"
        f"• 📡 Operadora: `{primeiro_registro.get('operadora', 'N/D')}`\n\n"
        f"👤 *PROPRIETÁRIO*\n"
        f"• 🏷️ Nome: `{primeiro_registro.get('nome', 'N/D')}`\n"
        f"• 🪪 Documento: `{primeiro_registro.get('cpfCnpj', 'N/D')}`\n"
        f"• 📧 E-mail: `{primeiro_registro.get('email', 'N/D')}`\n\n"
        f"📍 *ENDEREÇO*\n"
        f"• 🏙️ Cidade/UF: `{endereco.get('cidade', 'N/D')}/{endereco.get('siglaUf', 'N/D')}`\n"
        f"• 📮 CEP: `{cep_formatado}`\n"
        f"• 🏡 Logradouro: `{endereco.get('logradouro', 'N/D')}, {endereco.get('numero', 'N/D')} - {endereco.get('bairro', 'N/D')}`\n\n"
        f"📅 *CADASTRO*\n"
        f"• 🗓️ Data: `{dados.get('query_date', 'N/D').split('T')[0] if dados.get('query_date') else 'N/D'}`\n"
        f"• 🔍 Status: `{'Ativo' if dados.get('success') else 'Inativo'}`\n\n"
        f"🔄 Atualizado em: `{datetime.now().strftime('%d/%m/%Y %H:%M')}`"
    )

    return resposta

async def enviar_resposta_cpf(update: Update, argumento: str):
    try:
        url = f"{API_URL}?Access-Key={API_KEY}&Base=cpf&Info={argumento}"
        r = requests.get(url, timeout=15)

        if r.status_code != 200 or not r.text.strip():
            return await update.message.reply_text("⚠️ CPF não encontrado ou inválido.")

        dados = r.json()
        resposta = formatar_resposta_cpf(dados)

        keyboard = [
            [InlineKeyboardButton("💎 Outras Bases VIP", url=PLAN_LINK),
             InlineKeyboardButton("🗣️ Suporte", url=SUPORTE_LINK)]
        ]

        await update.message.reply_text(resposta, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        print(f"Erro: {e}")
        await update.message.reply_text("❌ Erro na consulta do CPF")

async def enviar_resposta_telefone(update: Update, argumento: str):
    try:
        url = f"{API_URL}?Access-Key={API_KEY}&Base=telefone&Info={argumento}"
        r = requests.get(url, timeout=15)

        if r.status_code != 200 or not r.text.strip():
            return await update.message.reply_text("⚠️ Telefone não encontrado ou inválido.")

        dados = r.json()
        resposta = formatar_resposta_telefone(dados)

        keyboard = [
            [InlineKeyboardButton("💎 Outras Bases VIP", url=PLAN_LINK),
             InlineKeyboardButton("🗣️ Suporte", url=SUPORTE_LINK)]
        ]

        await update.message.reply_text(resposta, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        print(f"Erro: {e}")
        await update.message.reply_text("❌ Erro na consulta do telefone")

async def enviar_resposta_completa(update: Update, comando: str, argumento: str, is_vip: bool):
    try:
        url = f"{API_URL}?Access-Key={API_KEY}&Base={comando}&Info={argumento}"
        r = requests.get(url, timeout=15)

        if r.status_code != 200 or not r.text.strip():
            return await update.message.reply_text("⚠️ Nenhum dado encontrado.")

        dados = r.json()
        nome_arquivo = f"{comando}_{argumento.replace(' ', '_')}.txt"
        caminho = f"/data/data/com.termux/files/home/Kazan/{nome_arquivo}"
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

        keyboard = [[
            InlineKeyboardButton("💎 Assinar VIP", url=PLAN_LINK),
            InlineKeyboardButton("🗣️ Suporte", url=f"{SUPORTE_LINK}?start=Olá,pixxain, gostaria de iniciar meu atendimento!")
        ]]

        await update.message.reply_text(mensagem, reply_markup=InlineKeyboardMarkup(keyboard))

        with open(caminho, "rb") as f:
            await update.message.reply_document(document=InputFile(f, filename=nome_arquivo),
                                                reply_markup=InlineKeyboardMarkup(keyboard) if not is_vip else None)

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
        [InlineKeyboardButton("🗣️ Suporte", url=f"{SUPORTE_LINK}?start=Olá,pixxain, gostaria de iniciar meu atendimento!"),
         InlineKeyboardButton("📚 Comandos", callback_data="show_commands")],
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
            "📚 *COMANDOS DISPONÍVEIS*\n\n"
            "🔍 *BASES GRÁTIS*\n"
            "• /cpf [número] - Consulta completa de CPF\n"
            "• /telefone [número] - Consulta de telefone\n"
            "• /nome [nome] - Busca por nome\n"
            "• /cnpj [número] - Consulta CNPJ\n\n"
            "💎 *BASES VIP*\n" + "\n".join([f"• /{base}" for base in BASES_VIP])
        )
        await query.message.reply_text(mensagem, parse_mode="Markdown")

async def handle_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    comando = update.message.text.split()[0][1:].lower()
    argumento = " ".join(context.args)
    chat_id = update.message.chat_id
    is_vip = chat_id == GRUPO_VIP_ID

    if comando == "cpf":
        if not argumento:
            return await update.message.reply_text("⚠️ Uso: /cpf <número>\nEx: /cpf 12345678901")
        return await enviar_resposta_cpf(update, argumento)

    if comando == "telefone":
        if not argumento:
            return await update.message.reply_text("⚠️ Uso: /telefone <número>\nEx: /telefone 11987654321")
        return await enviar_resposta_telefone(update, argumento)

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
        return await update.message.reply_text(f"⚠️ Uso: /{comando} <dado>\nEx: /{comando} {'12345678901' if comando in ['cnpj'] else 'dado'}")

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
