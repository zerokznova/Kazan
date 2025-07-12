import requests from telegram import Bot, ParseMode from telegram.ext import Updater, CommandHandler import html from datetime import datetime import os

TOKEN = '7727164066:AAFZmMo0RSI7RqwwLKa1aTKl50nSMr2bYoI' BASE_URL = 'https://voidsearch.localto.net/api/search' API_KEY = 'WM3t-Av5u-thfP-GiBV-sM3B'

bot = Bot(TOKEN) updater = Updater(bot=bot, use_context=True) dispatcher = updater.dispatcher

def format_error(error): return f"⚠️ {error}"

def format_date(date_str): try: return datetime.strptime(date_str[:10], "%Y-%m-%d").strftime("%d/%m/%Y") except: return date_str

def format_response_txt(base, data): base = base.lower() lines = [] lines.append(f"📌 Kazanova Buscas - Resultado ({base.upper()})") lines.append("=" * 40)

try:
    d = data.get("data", {})
    if base == "cpf":
        b = d.get("dadosBasicos", {})
        lines.append(f"👤 Nome: {b.get('nome', '')}")
        lines.append(f"🆔 CPF: {b.get('cpf', '')}")
        lines.append(f"📅 Nascimento: {format_date(b.get('nasc', ''))}")
        lines.append(f"⚧ Sexo: {b.get('sexo', '')}")
        lines.append(f"🔢 Signo: {b.get('signo', '')}")
        lines.append(f"🧬 Raça/Cor: {b.get('racaCor', '')}")
        lines.append(f"✅ Situação Cadastral: {b.get('situacaoCadastral', {}).get('descricao', '')}")

        filiacao = b.get('filiacao', {})
        lines.append(f"👩‍👧 Mãe: {filiacao.get('mae', '')}")
        lines.append(f"👨‍👦 Pai: {filiacao.get('pai', '')}")

        lines.append(f"📈 Score: {b.get('scoreFaixa', '')}")
        lines.append(f"💳 Score SPC: {d.get('serasaAnalytics', {}).get('score', '')}")
        lines.append(f"💸 Renda: R$ {b.get('rendaAtual', '')}")

        aq = d.get('poderAquisitivo', {})
        lines.append(f"💰 Poder aquisitivo: {aq.get('poderAquisitivo', '')}")
        lines.append(f"🏷️ Faixa de renda: {aq.get('faixaRenda', '')}")

        if d.get("telefones"):
            lines.append("\n📞 Telefones:")
            for t in d["telefones"]:
                lines.append(f"- {t}")

        if d.get("enderecos"):
            lines.append("\n🏠 Endereços:")
            for e in d["enderecos"]:
                end = f"{e.get('logradouro', '')}, {e.get('numero', '')} - {e.get('bairro', '')}, {e.get('cidade', '')} - {e.get('uf', '')} CEP: {e.get('cep', '')}"
                lines.append(f"- {end}")

        aux = d.get("beneficios", {}).get("auxilioBrasil", {})
        if aux and aux.get("totalRecebido") != "0":
            lines.append(f"\n🆘 Auxílio Brasil - Total Recebido: R$ {aux.get('totalRecebido')}")
            for p in aux.get("parcelasRecebidas", [])[:5]:
                valor = p.get("valor", "R$ 0")
                data = format_date(p.get("dataRecebimento", ""))
                lines.append(f"- {valor} em {data}")

        bf = d.get("beneficios", {}).get("bolsaFamilia", {})
        dependentes = bf.get("detalhamentoDependentes", [])
        if dependentes:
            lines.append("\n👨‍👧 Dependentes Bolsa Família:")
            for dep in dependentes:
                nome = dep.get("nome", "")
                nasc = format_date(dep.get("nasc", ""))
                lines.append(f"- {nome}, nasc. {nasc}")

        if d.get("compras"):
            lines.append("\n🛒 Compras Registradas:")
            for c in d["compras"][:5]:
                desc = c.get("descricao", "")
                valor = c.get("valor", "")
                tel = c.get("telefone", "")
                lines.append(f"- {desc} ({tel}) - R$ {valor}")

        if d.get("parentes"):
            lines.append("\n👨‍👩‍👧 Parentes:")
            for p in d["parentes"]:
                lines.append(f"- {p.get('nome', '')} ({p.get('parentesco', '')})")

        if d.get("interesses"):
            lines.append("\n📌 Interesses e Comportamento:")
            interesses = d["interesses"]
            for k, v in interesses.items():
                status = "✅ Possui" if v else "❌ Não possui"
                k_label = k.replace("_", " ").capitalize()
                lines.append(f"- {status}: {k_label}")

    else:
        lines.append(str(d))

except Exception as e:
    lines.append(format_error(f"Erro ao formatar resposta: {e}"))
return '\n'.join(lines)

def make_request(base, info): url = f"{BASE_URL}?Access-Key={API_KEY}&Base={base}&Info={info}" response = requests.get(url) return response.json()

def save_txt_file(base, info, content): filename = f"resposta_{base}{info}{datetime.now().strftime('%Y%m%d%H%M%S')}.txt" path = f"/tmp/{filename}" with open(path, "w", encoding="utf-8") as f: f.write(content) return path

def create_handler(base): def handler(update, context): try: info = ' '.join(context.args) if not info: raise Exception("Informe o dado para consulta.") data = make_request(base, info) if 'error' in data: raise Exception(data['error']) formatted = format_response_txt(base, data) filepath = save_txt_file(base, info.replace(" ", "_"), formatted) with open(filepath, 'rb') as doc: context.bot.send_document(chat_id=update.effective_chat.id, document=doc, filename=os.path.basename(filepath), caption=f"📎 Resultado: {base.upper()}") os.remove(filepath) except Exception as e: context.bot.send_message(chat_id=update.effective_chat.id, text=format_error(str(e)), parse_mode=ParseMode.HTML) return handler

comandos_bases = [ 'cpf', 'cnpj', 'rg', 'cpfsimpl', 'rgsimpl', 'nome', 'pis', 'titulo', 'telefone', 'email', 'cns', 'mae', 'pai', 'placa', 'chassi', 'renavam', 'motor', 'fotorj', 'fotosp', 'funcionarios', 'razao' ]

for comando in comandos_bases: handler = CommandHandler(comando, create_handler(comando)) dispatcher.add_handler(handler)

def start(update, context): comandos = '\n'.join([f"/{cmd}" for cmd in comandos_bases]) msg = f"<b>🧠 BOT DE CONSULTAS - VOIDSEARCH</b>\n\n<b>Comandos disponíveis:</b>\n{comandos}" context.bot.send_message(chat_id=update.effective_chat.id, text=msg, parse_mode=ParseMode.HTML)

dispatcher.add_handler(CommandHandler('start', start))

updater.start_polling() updater.idle()

