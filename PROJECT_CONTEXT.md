# PROJECT_CONTEXT.md — BolhaBot 🚗

> Contexto completo do projeto para assistentes de IA (Copilot, Cursor, etc.)

---

## 1. Visão Geral

**BolhaBot** é um chatbot para uma empresa de lava-rápido chamada **Carro Limpo**.
Permite que clientes agendem serviços diretamente via chat, consultando horários disponíveis e registrando agendamentos com placa e nome do responsável.

### Stack principal
| Camada | Tecnologia |
|--------|-----------|
| NLP / Intents | Google Dialogflow Essentials |
| Backend / Webhook | Python 3 + Flask |
| Banco de dados | Supabase (PostgreSQL) |
| Deploy previsto | PythonAnywhere |

---

## 2. Estrutura de Pastas

```
BOLHABOT/
├── app.py                          # Entrypoint Flask + roteador de intents
├── config.py                       # Credenciais Supabase (URL + KEY)
├── requirements.txt
├── database/
│   └── supabase_client.py          # Instância do cliente Supabase
├── services/
│   └── agendamento_service.py      # CRUD de agendamentos no Supabase
├── utils/
│   └── formatters.py               # Normalização de horários
└── templates/
    └── index.html                  # (Previsto) Página web da Carro Limpo
```

---

## 3. Arquivos e Responsabilidades

### `app.py`
- Servidor Flask com rota `GET /` (healthcheck) e `POST /webhook` (Dialogflow).
- Mantém sessões em memória (`dict sessoes`) por `session_id` do Dialogflow.
- Roteamento por `intent.displayName`:
  - `"agendar"` → coleta nome, placa, data, horário; salva no Supabase.
  - `"consultar_agendamento"` → busca agendamentos por placa.
- Evita sobrescrever campos já preenchidos na sessão (só atualiza se o parâmetro vir não-vazio).
- Antes de pedir horário, consulta horários já ocupados na data e exibe apenas os livres.

**Fluxo da intent `agendar`:**
```
nome? → placa? → data? → [card com horários livres] → confirma → salva → limpa sessão
```

**Horários válidos:** 08:00 a 18:00 (de hora em hora).

---

### `config.py`
- Exporta `SUPABASE_URL` e `SUPABASE_KEY` (anon key).
- ⚠️ **Não versionar em produção** — migrar para variáveis de ambiente / `.env`.

---

### `database/supabase_client.py`
- Cria e exporta a instância `supabase` via `create_client(SUPABASE_URL, SUPABASE_KEY)`.

---

### `services/agendamento_service.py`

| Função | Descrição |
|--------|-----------|
| `salvar_agendamento(dados)` | `INSERT` na tabela `agendamentos` |
| `consultar_agendamento(placa)` | `SELECT * WHERE placa = ?` |
| `consultar_agendamento_por_data(data)` | `SELECT * WHERE data = ?` (usado para checar horários ocupados) |

---

### `utils/formatters.py`

**`normalizar_horario(valor)`** — normaliza a string de horário recebida do Dialogflow para `"HH:MM"`:
- ISO 8601 (ex: `"2024-01-15T11:00:00"`) → extrai hora com `strftime`.
- Número puro (ex: `"11"`) → `"11:00"`.
- Formato com `h` (ex: `"11h"`) → `"11:00"`.
- Formato `"11:00"` → mantém, zero-padding garantido.

---

### `requirements.txt`
```
flask==3.0.0
supabase==1.0.3
httpx==0.23.3
python-dotenv==1.0.1
```

---

## 4. Banco de Dados (Supabase)

**Tabela:** `agendamentos`

| Coluna | Tipo | Observação |
|--------|------|-----------|
| `id` | uuid / serial | PK gerada pelo Supabase |
| `nome` | text | Nome do responsável |
| `placa` | text | Placa em maiúsculo (ex: `"ABC1234"`) |
| `data` | text / date | Data do agendamento |
| `horario` | text | Horário no formato `"HH:MM"` |

> Os campos `data` e `horario` são armazenados e consultados como texto/ISO — a conversão para exibição é feita no `app.py`.

---

## 5. Intents do Dialogflow

### `agendar`
- **Webhook:** habilitado **apenas no fulfillment final** (não usar "slot filling com webhook" — causa chamada prematura antes dos parâmetros serem preenchidos).
- **Parâmetros coletados:** `nome`, `placa`, `data`, `horario`.
- O controle de quais parâmetros já foram preenchidos é feito **na sessão em memória do Flask**, não nos parâmetros obrigatórios do Dialogflow.

### `consultar_agendamento`
- **Parâmetro:** `placa`.
- Retorna nome + data + horário do agendamento encontrado, ou mensagem de não encontrado.

### (Planejado) Intent de encerramento
- Frases de saída (ex: "tchau", "sair", "encerrar") + botão no card.

---

## 6. Decisões de Design / Problemas Conhecidos

| # | Situação | Detalhe |
|---|----------|---------|
| 1 | **Slot filling com webhook** | Se ativar "Enable webhook call for slot filling" no Dialogflow, o webhook é chamado a cada mensagem, antes dos parâmetros serem todos preenchidos. A solução adotada foi controlar o fluxo manualmente no Flask via sessões em memória. |
| 2 | **Sessão em memória** | `sessoes = {}` não persiste entre reinicializações do servidor. Para produção, considerar Redis ou Supabase como armazenamento de sessão. |
| 3 | **Credenciais hardcoded** | `config.py` contém URL e KEY literais. Usar `python-dotenv` com `.env` (já está no requirements). |
| 4 | **Formato de data/hora** | O Dialogflow envia horários em ISO 8601. O `normalizar_horario()` trata isso, mas há código redundante em `app.py` que também tenta converter — pode ser unificado. |

---

## 7. Roadmap / Partes Previstas

| Parte | Descrição | Status |
|-------|-----------|--------|
| 1 | Agendamento via chatbot (nome, placa, data, horário) | ✅ Implementado |
| 2 | Consulta de agendamento por placa | ✅ Implementado |
| 3 | Intent de encerramento de conversa + botão no card | 🔲 Planejado |
| 4 | Página HTML da Carro Limpo com botão do chatbot (canto inferior direito) | 🔲 Planejado |
| 5 | Integração com Telegram | 🔲 Planejado |

---

## 8. Como Rodar Localmente

```bash
# 1. Criar e ativar venv
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Rodar
python app.py
# Servidor em http://localhost:5000

# 4. Expor para o Dialogflow (ex: ngrok)
ngrok http 5000
# Copiar a URL HTTPS gerada e configurar como webhook no Dialogflow
```

---

## 9. Variáveis de Ambiente (Recomendado para Produção)

Criar arquivo `.env` na raiz:
```
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=eyJ...
```

E atualizar `config.py`:
```python
import os
from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
```

ligar Ngrok: C:\Users\Fabio\AppData\Local\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe http 5000

Rodar app: python app.py
