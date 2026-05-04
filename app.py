import os
from datetime import datetime
import traceback
import requests
import logging

from flask import Flask, jsonify, render_template, request

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
from config import (
    DIALOGFLOW_AGENT_ID,
    DIALOGFLOW_CHAT_TITLE,
    DIALOGFLOW_LANGUAGE_CODE,
    TELEGRAM_BOT_TOKEN,
)

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("Defina TELEGRAM_BOT_TOKEN no ambiente ou no arquivo .env.")
from services.agendamento_service import (
    consultar_agendamento,
    consultar_agendamento_por_data,
    salvar_agendamento,
)
from utils.formatters import (
    normalizar_data,
    normalizar_horario,
    normalizar_horario_texto,
    normalizar_placa,
)
from utils.date_parser import validar_data_futura, validar_horario_futuro

app = Flask(__name__)

def send_telegram_message(chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        logger.info(f"📤 Enviando para Telegram chat_id={chat_id}: {text[:50]}...")
        response = requests.post(url, json=payload)
        logger.info(f"📥 Resposta Telegram: {response.status_code} - {response.json()}")
        return response.json()
    except Exception as e:
        logger.error(f"❌ Erro ao enviar para Telegram: {e}")
        logger.error(traceback.format_exc())
        return {"ok": False, "error": str(e)}

# print(app.url_map)

sessoes = {}
HORARIOS_VALIDOS = [
    "08:00",
    "09:00",
    "10:00",
    "11:00",
    "12:00",
    "13:00",
    "14:00",
    "15:00",
    "16:00",
    "17:00",
    "18:00",
]
FRASES_SAIDA = {"sair", "encerrar", "finalizar", "tchau", "ate logo", "ate mais"}
FRASES_AGENDAR = {"agendar", "agendamento", "marcar", "marcar horario", "quero agendar"}
FRASES_CONSULTAR = {"consultar", "consulta", "ver agendamento", "buscar agendamento"}


def sessao_padrao():
    return {
        "nome": "",
        "placa": "",
        "data": "",
        "horario": "",
        "modo": "",
    }


def get_sessao(session_id):
    if session_id not in sessoes:
        sessoes[session_id] = sessao_padrao()
    return sessoes[session_id]


def limpar_sessao(session_id):
    sessoes[session_id] = sessao_padrao()


def sessao_tem_dados(dados):
    return any(dados[campo] for campo in ("nome", "placa", "data", "horario"))


def buscar_horarios_ocupados(data):
    agendamentos = consultar_agendamento_por_data(data)
    ocupados = set()

    for agendamento in agendamentos:
        horario = normalizar_horario(agendamento.get("horario"))
        if horario:
            ocupados.add(horario)

    return ocupados


def formatar_data_exibicao(valor):
    try:
        return datetime.fromisoformat(valor).strftime("%d/%m/%Y")
    except (TypeError, ValueError):
        return valor


def formatar_horarios_em_linhas(horarios):
    return "\n".join(horarios)


def encerrar_conversa(session_id):
    limpar_sessao(session_id)
    return "Conversa encerrada. Obrigado por usar o BolhaBot!"


def texto_indica_agendamento(texto):
    return any(frase in texto for frase in FRASES_AGENDAR)


def texto_indica_consulta(texto):
    return any(frase in texto for frase in FRASES_CONSULTAR) or "placa" in texto


def texto_indica_saida(texto):
    return texto in FRASES_SAIDA or any(texto.startswith(frase) for frase in FRASES_SAIDA)


def salvar_agendamento_fluxo(session_id, dados):
    try:
        salvar_agendamento(
            {
                "nome": dados["nome"],
                "placa": dados["placa"],
                "data": dados["data"],
                "horario": dados["horario"],
            }
        )
    except Exception as exc:
        print("ERRO AO SALVAR AGENDAMENTO:", exc)
        traceback.print_exc()
        dados["horario"] = ""
        return "Tive um problema interno ao salvar o agendamento. Pode tentar novamente?"

    data_exibicao = formatar_data_exibicao(dados["data"])
    horario_confirmado = dados["horario"]
    mensagem = (
        f"Perfeito, {dados['nome']}! Seu veiculo de placa {dados['placa']} "
        f"foi agendado para {data_exibicao} as {horario_confirmado}."
    )
    limpar_sessao(session_id)
    return mensagem


def responder_consulta_por_placa(placa):
    resultado = consultar_agendamento(placa)

    if resultado:
        agendamento = resultado[0]
        try:
            data_str = agendamento["data"]
            data_obj = datetime.fromisoformat(data_str)
            data_formatada = data_obj.strftime("%d/%m/%Y")
        except (TypeError, ValueError, KeyError):
            data_formatada = agendamento.get("data", "")
            data_str = None

        hora = normalizar_horario(agendamento.get("horario")) or agendamento.get("horario", "")
        
        # Verifica se o agendamento é do passado
        if data_str and hora:
            horario_valido, _ = validar_horario_futuro(data_str, hora)
            if not horario_valido:
                return (
                    f"Voce tinha um agendamento em {data_formatada} as {hora} (horario ja encerrado). "
                    f"Se precisar, posso ajudar a agendar um novo horario."
                )
        
        return (
            f"Encontrei seu agendamento. Veiculo {agendamento.get('placa', '')} "
            f"marcado para {data_formatada} as {hora}."
        )

    return f"Nao encontrei agendamento para a placa {placa}."


def processar_fluxo_agendamento(session_id, texto):
    dados = get_sessao(session_id)
    dados["modo"] = "agendar"

    # Passo 1: Coletar nome
    if not dados["nome"]:
        if texto_indica_agendamento(texto) or texto in {"oi", "ola", "olá"}:
            return "Vamos agendar. Qual e o seu nome?"
        dados["nome"] = texto.strip().title()
        return "Qual e a placa do veiculo?"

    # Passo 2: Coletar placa
    if not dados["placa"]:
        placa = normalizar_placa(texto)
        if not placa:
            return "Informe a placa do veiculo. Exemplo: ABC1234."
        dados["placa"] = placa
        return "Para qual data deseja agendar?"

    # Passo 3: Coletar data
    if not dados["data"]:
        data_str, precisa_mais_info, mensagem_extra = normalizar_data(texto)
        
        # Se precisa de mais informações (ex: "semana que vem" - qual dia?)
        if precisa_mais_info:
            return mensagem_extra
        
        if not data_str:
            return "Nao consegui entender a data. Tente novamente (exemplo: 'amanha', 'segunda', '15/05/2026')."
        
        # Valida se a data não é do passado
        data_valida, mensagem_erro = validar_data_futura(data_str)
        if not data_valida:
            return mensagem_erro
        
        dados["data"] = data_str
        
        # Mostra horários disponíveis
        ocupados = buscar_horarios_ocupados(dados["data"])
        livres = [h for h in HORARIOS_VALIDOS if h not in ocupados]
        if not livres:
            dados["data"] = ""
            return "Nao ha horarios disponiveis para esse dia. Tente outra data."
        return (
            f"Escolha um horario disponivel para {formatar_data_exibicao(dados['data'])}:\n"
            f"{formatar_horarios_em_linhas(livres)}"
        )

    # Passo 4: Coletar horário
    if not dados["horario"]:
        horario = normalizar_horario_texto(texto) or normalizar_horario(texto)
        if not horario:
            ocupados = buscar_horarios_ocupados(dados["data"])
            livres = [h for h in HORARIOS_VALIDOS if h not in ocupados]
            if not livres:
                dados["data"] = ""
                return "Nao ha horarios disponiveis para esse dia. Tente outra data."
            return (
                f"Escolha um horario disponivel para {formatar_data_exibicao(dados['data'])}:\n"
                f"{formatar_horarios_em_linhas(livres)}"
            )
        
        # Valida se o horário é válido
        if horario not in HORARIOS_VALIDOS:
            return "Escolha um horario valido entre 08:00 e 18:00."
        
        # Valida se o horário não é do passado
        horario_valido, mensagem_erro = validar_horario_futuro(dados["data"], horario)
        if not horario_valido:
            dados["horario"] = ""
            dados["data"] = ""
            return f"{mensagem_erro} Vamos tentar novamente. Para qual data deseja agendar?"
        
        # Valida se o horário está disponível
        ocupados = buscar_horarios_ocupados(dados["data"])
        if horario in ocupados:
            livres = [h for h in HORARIOS_VALIDOS if h not in ocupados]
            if not livres:
                dados["data"] = ""
                return "Esse horario nao esta mais disponivel. Informe outra data."
            return (
                "Esse horario nao esta mais disponivel. Escolha outro:\n"
                f"{formatar_horarios_em_linhas(livres)}"
            )
        
        dados["horario"] = horario
        return salvar_agendamento_fluxo(session_id, dados)

    # Não deveria chegar aqui, mas por segurança
    return salvar_agendamento_fluxo(session_id, dados)


def processar_chat_web(session_id, mensagem):
    texto_original = (mensagem or "").strip()
    texto = texto_original.lower()
    dados = get_sessao(session_id)

    if not texto_original:
        return "Escreva sua mensagem para eu continuar."

    if texto_indica_saida(texto):
        return encerrar_conversa(session_id)

    if dados["modo"] == "consultar":
        placa = normalizar_placa(texto_original)
        if not placa:
            return "Informe a placa para consultar o agendamento."
        limpar_sessao(session_id)
        return responder_consulta_por_placa(placa)

    if texto_indica_consulta(texto) and not sessao_tem_dados(dados):
        dados["modo"] = "consultar"
        return "Informe a placa do veiculo para consultar."

    if dados["modo"] == "agendar" or sessao_tem_dados(dados) or texto_indica_agendamento(texto):
        return processar_fluxo_agendamento(session_id, texto_original)

    placa = normalizar_placa(texto_original)
    if placa:
        return responder_consulta_por_placa(placa)

    return (
        "Oi! Eu posso agendar lavagem ou consultar um agendamento. "
        "Digite 'agendar' para marcar um horario ou 'consultar' para buscar pela placa."
    )


@app.route("/")
def home():
    return render_template(
        "index.html",
        dialogflow_agent_id=DIALOGFLOW_AGENT_ID,
        dialogflow_chat_title=DIALOGFLOW_CHAT_TITLE,
        dialogflow_language_code=DIALOGFLOW_LANGUAGE_CODE,
    )


@app.route("/chat", methods=["POST"])
def chat():
    try:
        payload = request.get_json() or {}
        session_id = payload.get("session_id") or "web-default"
        mensagem = payload.get("message", "")
        resposta_texto = processar_chat_web(session_id, mensagem)
        return jsonify({"reply": resposta_texto})
    except Exception as exc:
        print("ERRO CHAT:", exc)
        traceback.print_exc()
        return jsonify({"reply": "Tive um problema interno. Tente novamente."}), 500


@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        payload = request.get_json() or {}
        query_result = payload.get("queryResult", {})

        intent = query_result.get("intent", {}).get("displayName")
        parametros = query_result.get("parameters", {})
        query_text = (query_result.get("queryText") or "").strip().lower()
        session_id = payload.get("session")
        dados = get_sessao(session_id)

        if intent == "agendar":
            if query_text in {"agendar", "quero agendar", "fazer agendamento", "marcar horario"}:
                limpar_sessao(session_id)
                dados = get_sessao(session_id)
                dados["modo"] = "agendar"

            if parametros.get("nome"):
                dados["nome"] = parametros["nome"].strip()

            if parametros.get("placa"):
                placa = normalizar_placa(parametros["placa"])
                if placa:
                    dados["placa"] = placa

            if parametros.get("data"):
                data_formatada = normalizar_data(parametros["data"])
                if data_formatada:
                    dados["data"] = data_formatada

            if parametros.get("horario"):
                horario_formatado = normalizar_horario_texto(query_text) or normalizar_horario(parametros["horario"])
                if horario_formatado:
                    dados["horario"] = horario_formatado

            resposta_fluxo = processar_fluxo_agendamento(session_id, query_text or "agendar")
            return resposta(resposta_fluxo)

        if intent == "consultar_agendamento":
            placa = normalizar_placa(parametros.get("placa") or "")
            if not placa:
                return resposta("Por favor, informe a placa.")
            return resposta(responder_consulta_por_placa(placa))

        if intent == "finalizar_conversa":
            return resposta(encerrar_conversa(session_id))

        return resposta("Desculpe, nao entendi sua mensagem. Quer tentar novamente?")

    except Exception as exc:
        print("ERRO:", exc)
        traceback.print_exc()
        return jsonify(
            {
                "fulfillmentText": "Tive um problema interno. Quer tentar novamente?"
            }
        )


def resposta(msg):
    return jsonify({"fulfillmentText": msg})


@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    try:
        data = request.get_json()
        logger.info(f"🔥 TELEGRAM CHEGOU: {data}")

        if data and "message" in data:
            logger.info("✅ Campo 'message' encontrado")
            
            try:
                chat_id = data["message"]["chat"]["id"]
                logger.info(f"✅ Chat ID extraído: {chat_id}")
            except Exception as e:
                logger.error(f"❌ Erro ao extrair chat_id: {e}")
                return jsonify({"status": "erro", "error": "chat_id"}), 500
            
            try:
                text = data["message"].get("text", "")
                logger.info(f"✅ Texto extraído: '{text}'")
            except Exception as e:
                logger.error(f"❌ Erro ao extrair text: {e}")
                return jsonify({"status": "erro", "error": "text"}), 500
            
            logger.info(f"💬 Processando mensagem do chat {chat_id}: {text}")

            try:
                resposta_texto = processar_chat_web(str(chat_id), text)
                logger.info(f"✅ Resposta gerada: {resposta_texto[:50]}...")
            except Exception as e:
                logger.error(f"❌ Erro ao processar mensagem: {e}")
                logger.error(traceback.format_exc())
                resposta_texto = "Desculpe, tive um erro ao processar sua mensagem."

            logger.info(f"📤 Enviando resposta para Telegram...")
            send_telegram_message(chat_id, resposta_texto)
        else:
            logger.warning("⚠️ 'message' não encontrado em data")

        return jsonify({"status": "ok"})
    
    except Exception as e:
        logger.error(f"💥 ERRO TELEGRAM: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"status": "erro", "error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "BolhaBot"})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    logger.info(f"🚀 Iniciando BolhaBot na porta {port}")
    app.run(host="0.0.0.0", port=port)
