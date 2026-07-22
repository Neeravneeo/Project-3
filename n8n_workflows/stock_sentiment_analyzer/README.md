# n8n Stock Sentiment Analyzer Workflow System

A production-grade, automated n8n workflow system for real-time Stock Sentiment and Financial Health Analysis. This system ingests equity stock tickers (e.g. `AAPL`, `NVDA`, `MSFT`), fetches live financial news and earnings press releases via RSS, aggregates and sanitizes news context, evaluates fundamental metrics with an LLM Financial Analyst persona, and outputs a 4-section GitHub-flavored Markdown report.

---

## Target Directory Layout

```
d:\trading\n8n_workflows\stock_sentiment_analyzer\
├── workflow.json         # Exportable n8n workflow definition
├── docker-compose.yml    # Docker Desktop container orchestration setup
├── .env.example          # Environment variable template with API key placeholders
├── README.md             # Instructions for setup, execution, and testing
└── test_workflow.py      # Verification test suite with mock server daemon support
```

---

## 1. Prerequisites

- **Docker Desktop** (with WSL2 engine on Windows or native Docker on Linux/macOS)
- **Python 3.8+** (for running automated verification tests)
- **OpenAI API Key** (or compatible LLM provider key)

---

## 2. Environment Setup & Container Launch

1. Navigate to the workflow directory:
   ```bash
   cd d:\trading\n8n_workflows\stock_sentiment_analyzer
   ```

2. Copy `.env.example` to `.env` and fill in your API credentials:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` to configure your `OPENAI_API_KEY` and optional `FINNHUB_API_KEY`.

3. Launch the n8n Docker container:
   ```bash
   docker compose up -d
   ```

4. Verify container health status:
   ```bash
   docker compose ps
   curl -i http://localhost:5678/healthz
   ```
   The health check should return `HTTP 200 OK`.

---

## 3. Importing the Workflow into n8n

1. Open your browser and navigate to `http://localhost:5678`.
2. Complete initial account registration (if launching for the first time).
3. In the n8n navigation menu, click **Workflows** -> **Import from File**.
4. Select `d:\trading\n8n_workflows\stock_sentiment_analyzer\workflow.json`.
5. Open the **Financial Analyst LLM Node** and select or add your **OpenAI Credentials** (`OpenAI Account`).
6. Save the workflow and toggle the workflow switch to **Active**.

---

## 4. Triggering the Workflow

### Method A: HTTP POST Webhook Request
```bash
curl -X POST http://localhost:5678/webhook/stock-sentiment \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL"}'
```

### Method B: HTTP GET Webhook Request
```bash
curl "http://localhost:5678/webhook/stock-sentiment?ticker=NVDA"
```

Supported stock tickers include `AAPL`, `NVDA`, `MSFT`, or any valid US equity ticker symbol.

---

## 5. Report Output Format

The workflow outputs a 4-section GitHub-flavored Markdown report adhering strictly to the required schema:

1. `## Executive Summary & Overall News Sentiment`
2. `## Profitability & Financial Health Analysis`
3. `## Financial Metrics Spotlight Table`
4. `## Investment Potential & Profitability Score` (including `**Profitability Score: X/10**`)

The report evaluates:
- **Revenue Growth Trajectory**
- **Profit Margins**
- **Cost Structure & Operational Efficiency**
- **Competitive Moat & Market Position**
- **Positive Catalysts vs Profitability Risks**

---

## 6. Automated Verification Testing

The system includes a verification test suite in `test_workflow.py` supporting live container testing as well as offline execution using an embedded `LocalMockServer` daemon.

### Run in Offline Mock Mode (Zero-Dependency)
```bash
python d:\trading\n8n_workflows\stock_sentiment_analyzer\test_workflow.py --mock
```

### Run via Pytest
```bash
pytest d:\trading\n8n_workflows\stock_sentiment_analyzer\test_workflow.py
```

### Run Live Against Container
```bash
python d:\trading\n8n_workflows\stock_sentiment_analyzer\test_workflow.py --url http://localhost:5678/webhook/stock-sentiment
```

---

## 7. Container Lifecycle Management

- **View Container Logs**:
  ```bash
  docker compose logs -f
  ```
- **Restart Container**:
  ```bash
  docker compose restart
  ```
- **Stop and Remove Container**:
  ```bash
  docker compose down
  ```
  *(Data is safely persisted in the named volume `n8n_data`).*
