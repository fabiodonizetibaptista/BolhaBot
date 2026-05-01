"""
Módulo para parsing de datas em linguagem natural (português brasileiro)
"""
import re
from datetime import datetime, timedelta


DIAS_SEMANA = {
    "domingo": 6,
    "segunda": 0,
    "segunda-feira": 0,
    "terca": 1,
    "terça": 1,
    "terca-feira": 1,
    "terça-feira": 1,
    "quarta": 2,
    "quarta-feira": 2,
    "quinta": 3,
    "quinta-feira": 3,
    "sexta": 4,
    "sexta-feira": 4,
    "sabado": 5,
    "sábado": 5,
}

MESES = {
    "janeiro": 1,
    "fevereiro": 2,
    "março": 3,
    "marco": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}


def extrair_numero(texto):
    """Extrai o primeiro número encontrado no texto"""
    match = re.search(r'\d+', texto)
    return int(match.group()) if match else None


def calcular_proximo_dia_semana(dia_semana_alvo):
    """
    Calcula a data do próximo dia da semana especificado
    dia_semana_alvo: 0=segunda, 1=terça, ..., 6=domingo
    """
    hoje = datetime.now()
    dia_atual = hoje.weekday()
    
    # Calcula quantos dias faltam para o dia desejado
    dias_ate = (dia_semana_alvo - dia_atual) % 7
    
    # Se for 0, significa que é hoje, então pega a próxima semana
    if dias_ate == 0:
        dias_ate = 7
    
    return hoje + timedelta(days=dias_ate)


def parsear_data_natural(texto):
    """
    Converte texto em linguagem natural para data no formato YYYY-MM-DD
    
    Exemplos suportados:
    - "amanhã", "amanha"
    - "hoje"
    - "segunda", "terça", etc (próximo dia da semana)
    - "semana que vem" (pergunta qual dia)
    - "mês que vem", "mes que vem" (pergunta qual dia)
    - "daqui a 3 dias"
    - "15 de maio"
    - "15/05/2026"
    - "2026-05-15"
    
    Retorna:
    - (data_str, precisa_mais_info, mensagem) onde:
      - data_str: string no formato YYYY-MM-DD ou None
      - precisa_mais_info: bool indicando se precisa perguntar mais
      - mensagem: string com pergunta adicional se necessário
    """
    if not texto:
        return None, False, None
    
    texto_original = texto
    texto = texto.lower().strip()
    
    # Remove acentos comuns para facilitar matching
    texto = (texto
        .replace('ã', 'a')
        .replace('á', 'a')
        .replace('é', 'e')
        .replace('ê', 'e')
        .replace('í', 'i')
        .replace('ó', 'o')
        .replace('ô', 'o')
        .replace('ú', 'u')
    )
    
    hoje = datetime.now()
    
    # Caso 1: "hoje"
    if "hoje" in texto:
        return hoje.strftime("%Y-%m-%d"), False, None
    
    # Caso 2: "amanhã"
    if "amanha" in texto or "amanhã" in texto:
        amanha = hoje + timedelta(days=1)
        return amanha.strftime("%Y-%m-%d"), False, None
    
    # Caso 3: "depois de amanhã"
    if "depois de amanha" in texto or "depois de amanhã" in texto:
        depois = hoje + timedelta(days=2)
        return depois.strftime("%Y-%m-%d"), False, None
    
    # Caso 4: Dias da semana (segunda, terça, etc)
    for dia_nome, dia_num in DIAS_SEMANA.items():
        if dia_nome in texto:
            data = calcular_proximo_dia_semana(dia_num)
            return data.strftime("%Y-%m-%d"), False, None
    
    # Caso 5: "daqui a X dias"
    if "daqui a" in texto and "dia" in texto:
        numero = extrair_numero(texto)
        if numero:
            data = hoje + timedelta(days=numero)
            return data.strftime("%Y-%m-%d"), False, None
    
    # Caso 6: "semana que vem" - precisa saber qual dia
    if "semana que vem" in texto or "proxima semana" in texto:
        return None, True, "Qual dia da semana que vem? (segunda, terça, quarta, etc)"
    
    # Caso 7: "mês que vem" - precisa saber qual dia
    if "mes que vem" in texto or "mês que vem" in texto or "proximo mes" in texto:
        return None, True, "Qual dia do mês que vem? (exemplo: dia 15)"
    
    # Caso 8: "dia X" (assume mês atual ou próximo)
    match = re.search(r'\bdia\s+(\d+)', texto)
    if match:
        dia = int(match.group(1))
        try:
            # Tenta no mês atual
            data = datetime(hoje.year, hoje.month, dia)
            # Se a data já passou, usa o próximo mês
            if data < hoje:
                if hoje.month == 12:
                    data = datetime(hoje.year + 1, 1, dia)
                else:
                    data = datetime(hoje.year, hoje.month + 1, dia)
            return data.strftime("%Y-%m-%d"), False, None
        except ValueError:
            pass
    
    # Caso 9: "X de [mês]" (exemplo: "15 de maio")
    for mes_nome, mes_num in MESES.items():
        if mes_nome in texto:
            numero = extrair_numero(texto)
            if numero and 1 <= numero <= 31:
                try:
                    # Determina o ano (atual ou próximo)
                    ano = hoje.year
                    data = datetime(ano, mes_num, numero)
                    # Se a data já passou, usa o próximo ano
                    if data < hoje:
                        data = datetime(ano + 1, mes_num, numero)
                    return data.strftime("%Y-%m-%d"), False, None
                except ValueError:
                    pass
    
    # Caso 10: Formato DD/MM/YYYY ou DD/MM/YY
    match = re.search(r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})', texto_original)
    if match:
        dia, mes, ano = match.groups()
        dia, mes, ano = int(dia), int(mes), int(ano)
        
        # Ajusta ano de 2 dígitos
        if ano < 100:
            if ano < 50:
                ano += 2000
            else:
                ano += 1900
        
        try:
            data = datetime(ano, mes, dia)
            return data.strftime("%Y-%m-%d"), False, None
        except ValueError:
            return None, False, None
    
    # Caso 11: Formato YYYY-MM-DD
    match = re.search(r'(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})', texto_original)
    if match:
        ano, mes, dia = match.groups()
        try:
            data = datetime(int(ano), int(mes), int(dia))
            return data.strftime("%Y-%m-%d"), False, None
        except ValueError:
            return None, False, None
    
    # Caso 12: Formato ISO do Dialogflow
    if "T" in texto_original:
        try:
            data = datetime.fromisoformat(texto_original)
            return data.strftime("%Y-%m-%d"), False, None
        except ValueError:
            pass
    
    return None, False, None


def validar_data_futura(data_str):
    """
    Valida se a data está no futuro (ou é hoje)
    
    Retorna:
    - (valida, mensagem_erro) onde:
      - valida: bool
      - mensagem_erro: string ou None
    """
    if not data_str:
        return False, "Data inválida."
    
    try:
        data = datetime.strptime(data_str, "%Y-%m-%d")
        hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        if data < hoje:
            data_formatada = data.strftime("%d/%m/%Y")
            return False, f"A data {data_formatada} já passou. Por favor, escolha uma data futura."
        
        return True, None
    except ValueError:
        return False, "Data inválida."


def validar_horario_futuro(data_str, horario_str):
    """
    Valida se o horário está no futuro (considerando data e hora)
    
    Retorna:
    - (valido, mensagem_erro) onde:
      - valido: bool
      - mensagem_erro: string ou None
    """
    if not data_str or not horario_str:
        return False, "Data ou horário inválido."
    
    try:
        data = datetime.strptime(data_str, "%Y-%m-%d")
        hora, minuto = map(int, horario_str.split(":"))
        data_hora = data.replace(hour=hora, minute=minuto)
        
        agora = datetime.now()
        
        if data_hora < agora:
            data_formatada = data.strftime("%d/%m/%Y")
            return False, f"O horário {horario_str} do dia {data_formatada} já passou. Por favor, escolha um horário futuro."
        
        return True, None
    except (ValueError, AttributeError):
        return False, "Data ou horário inválido."
