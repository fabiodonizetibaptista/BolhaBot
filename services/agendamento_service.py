from uuid import uuid4

from database.supabase_client import supabase

def salvar_agendamento(dados):
    dados_para_salvar = {"id": str(uuid4()), **dados}
    return supabase.table("agendamentos").insert(dados_para_salvar).execute()


def consultar_agendamento(placa):
    response = supabase.table("agendamentos").select("*").eq("placa", placa).execute()
    return response.data

def consultar_agendamento_por_data(data):
    response = supabase.table("agendamentos").select("*").eq("data", data).execute()
    return response.data
