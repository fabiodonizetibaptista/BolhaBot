import re
from datetime import datetime
from utils.date_parser import parsear_data_natural

HORAS_POR_EXTENSO = {
    "oito": 8,
    "nove": 9,
    "dez": 10,
    "onze": 11,
    "doze": 12,
    "treze": 13,
    "catorze": 14,
    "quatorze": 14,
    "quinze": 15,
    "dezesseis": 16,
    "dezessete": 17,
    "dezoito": 18,
}


def normalizar_data(valor):
    """
    Normaliza data usando o parser de linguagem natural
    Retorna: (data_str, precisa_mais_info, mensagem)
    """
    if not valor:
        return None, False, None
    
    # Usa o parser de linguagem natural
    data_str, precisa_mais_info, mensagem = parsear_data_natural(str(valor))
    return data_str, precisa_mais_info, mensagem


def normalizar_horario_texto(texto):
    if not texto:
        return None

    texto = texto.lower().strip()

    for palavra, hora in sorted(HORAS_POR_EXTENSO.items(), key=lambda item: len(item[0]), reverse=True):
        if palavra in texto:
            return f"{hora:02d}:00"

    texto_limpo = (
        texto.replace("horas", "")
        .replace("hora", "")
        .replace("hrs", "")
        .replace("hr", "")
        .replace("h", ":00")
        .strip()
    )

    if texto_limpo.isdigit():
        return f"{int(texto_limpo):02d}:00"

    if ":" in texto_limpo:
        partes = texto_limpo.split(":")
        if len(partes) >= 2 and partes[0].isdigit() and partes[1].isdigit():
            return f"{int(partes[0]):02d}:{int(partes[1]):02d}"

    return None


def normalizar_placa(valor):
    if not valor:
        return None

    placa = re.sub(r"[^A-Za-z0-9]", "", str(valor)).upper()

    if re.fullmatch(r"[A-Z]{3}[0-9][A-Z0-9][0-9]{2}", placa):
        return placa

    if re.fullmatch(r"[A-Z]{3}[0-9]{4}", placa):
        return placa

    return None


def normalizar_horario(valor):
    if not valor:
        return None

    try:
        # Caso venha ISO do Dialogflow
        if "T" in valor:
            return datetime.fromisoformat(valor).strftime("%H:%M")

        valor = valor.lower().replace("h", "").strip()

        # só número → 11 → 11:00
        if valor.isdigit():
            return f"{int(valor):02d}:00"

        # formato 11:00
        if ":" in valor:
            h, m = valor.split(":")
            return f"{int(h):02d}:{int(m):02d}"

    except:
        return None

    return None
