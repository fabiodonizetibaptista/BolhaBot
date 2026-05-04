# Migração para PythonAnywhere

## Arquivos necessários para upload:
- app.py
- config.py
- requirements.txt
- database/supabase_client.py
- services/agendamento_service.py
- utils/date_parser.py
- utils/formatters.py
- static/index.html
- templates/index.html
- .env (com as variáveis de produção)

## Passos para migração:

### 1. Criar conta no PythonAnywhere
- Acesse https://www.pythonanywhere.com
- Crie uma conta gratuita

### 2. Criar novo web app
- Dashboard > Web > Add a new web app
- Escolha "Flask" como framework
- Selecione Python 3.10 (ou versão compatível)
- Defina o caminho do app como `/home/seu_usuario/BolhaBot/app.py`

### 3. Upload dos arquivos
- Use o Files tab para fazer upload dos arquivos
- OU use Git: `git clone https://github.com/seu_usuario/BolhaBot.git`

### 4. Instalar dependências
- Abra um Bash console
- Navegue para o diretório do projeto: `cd BolhaBot`
- Instale as dependências: `pip install -r requirements.txt`

### 5. Configurar variáveis de ambiente
- No Web tab > Environment variables
- Adicione todas as variáveis do seu .env:
  - SUPABASE_URL
  - SUPABASE_KEY
  - DIALOGFLOW_AGENT_ID
  - DIALOGFLOW_CHAT_TITLE
  - DIALOGFLOW_LANGUAGE_CODE
  - TELEGRAM_BOT_TOKEN

### 6. Configurar webhook do Telegram
- Execute o script de configuração do webhook:
  ```bash
  cd BolhaBot
  export PYTHONANYWHERE_URL=https://seu_usuario.pythonanywhere.com
  python setup_webhook.py
  ```
- OU configure manualmente via API do Telegram

### 7. Reload do web app
- No Web tab, clique em "Reload"

## Comandos importantes no PythonAnywhere:
```bash
# Instalar dependências
pip install -r requirements.txt

# Ver logs
tail -f /var/log/webapps/seu_usuario_pythonanywhere_com.log

# Reload app
touch /var/www/seu_usuario_pythonanywhere_com_wsgi.py
```

## URLs importantes:
- App: https://seu_usuario.pythonanywhere.com
- Webhook: https://seu_usuario.pythonanywhere.com/telegram
- Health check: https://seu_usuario.pythonanywhere.com/health