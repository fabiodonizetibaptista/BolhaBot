import requests
from config import TELEGRAM_BOT_TOKEN

# Teste 1: Verificar token
print("✅ Token carregado:", TELEGRAM_BOT_TOKEN[:15] + "...")

# Teste 2: Testar rota local
print("\n⏳ Testando rota /telegram localmente...")
try:
    r = requests.post('http://localhost:5000/telegram', 
                      json={'message': {'chat': {'id': 999}, 'text': 'teste'}},
                      timeout=3)
    print(f"✅ Rota respondeu: {r.status_code} - {r.json()}")
except requests.exceptions.ConnectionError:
    print("❌ Flask não está rodando em http://localhost:5000")
except Exception as e:
    print(f"❌ Erro: {e}")

# Teste 3: Verificar webhook
print("\n⏳ Verificando webhook no Telegram...")
r = requests.get(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getWebhookInfo')
webhook = r.json()['result']
print(f"✅ Webhook URL: {webhook['url']}")
print(f"✅ Updates pendentes: {webhook['pending_update_count']}")
