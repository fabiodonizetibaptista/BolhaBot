#!/usr/bin/env python3
"""
Script para configurar o webhook do Telegram
Execute este script após fazer deploy no PythonAnywhere
"""

import os
import requests
from config import TELEGRAM_BOT_TOKEN

def set_webhook():
    """Configura o webhook do Telegram para o URL do PythonAnywhere"""

    # URL do seu app no PythonAnywhere (substitua pelo seu username)
    # Exemplo: https://seu_usuario.pythonanywhere.com
    PYTHONANYWHERE_URL = os.getenv("PYTHONANYWHERE_URL")

    if not PYTHONANYWHERE_URL:
        print("❌ Defina PYTHONANYWHERE_URL no ambiente")
        print("Exemplo: export PYTHONANYWHERE_URL=https://seu_usuario.pythonanywhere.com")
        return False

    webhook_url = f"{PYTHONANYWHERE_URL}/telegram"

    print(f"🔧 Configurando webhook para: {webhook_url}")

    try:
        # Remove webhook atual
        requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook")

        # Define novo webhook
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook",
            json={"url": webhook_url}
        )

        if response.status_code == 200 and response.json().get("ok"):
            print("✅ Webhook configurado com sucesso!")
            return True
        else:
            print(f"❌ Erro ao configurar webhook: {response.json()}")
            return False

    except Exception as e:
        print(f"💥 Erro: {e}")
        return False

def check_webhook():
    """Verifica se o webhook está configurado corretamente"""

    try:
        response = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getWebhookInfo")
        webhook_info = response.json()

        if response.status_code == 200 and webhook_info.get("ok"):
            result = webhook_info["result"]
            print(f"📡 Webhook URL: {result.get('url', 'Não definido')}")
            print(f"📊 Updates pendentes: {result.get('pending_update_count', 0)}")

            if result.get("url"):
                print("✅ Webhook está ativo!")
                return True
            else:
                print("⚠️ Webhook não está configurado")
                return False
        else:
            print(f"❌ Erro ao verificar webhook: {webhook_info}")
            return False

    except Exception as e:
        print(f"💥 Erro: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Configurando webhook do Telegram...")
    print()

    if set_webhook():
        print()
        check_webhook()
    else:
        print("❌ Falha na configuração do webhook")