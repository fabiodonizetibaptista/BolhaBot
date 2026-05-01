import os

from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DIALOGFLOW_AGENT_ID = os.getenv("DIALOGFLOW_AGENT_ID")
DIALOGFLOW_CHAT_TITLE = os.getenv("DIALOGFLOW_CHAT_TITLE", "BolhaBot")
DIALOGFLOW_LANGUAGE_CODE = os.getenv("DIALOGFLOW_LANGUAGE_CODE", "pt-br")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Defina SUPABASE_URL e SUPABASE_KEY no ambiente ou no arquivo .env.")
