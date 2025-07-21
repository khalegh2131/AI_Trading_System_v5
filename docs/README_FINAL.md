# AI_Trading_System_v5 – Zero Defect
## Quick Start (30s)
```bash
cd D:\AI\AI_Trading_System_v5
cp .env.example .env  # Fill API keys
docker compose -f docker-compose.yml up -d --build
pytest tests/test_deploy.py
docker logs -f ai_trading_v5