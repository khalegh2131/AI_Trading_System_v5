# AI Trading System v5 - Usage Examples

## Quick Start

### 1. Basic Trading System
Run the main trading system with the orchestrator:
```bash
python app.py
```

### 2. Interactive Dashboard
Launch the interactive CLI dashboard:
```bash
python app.py --mode dashboard
```

### 3. API Server
Start the REST API server:
```bash
python app.py --mode api --port 8000
```

Access API documentation at: http://localhost:8000/docs

### 4. Run Backtest
Execute a backtest for a strategy:
```bash
python app.py --mode backtest --strategy rsi_strategy --symbol BTC/USDT --days 30
```

## API Examples

### Start Trading System
```bash
curl -X POST http://localhost:8000/trading/start
```

### Get System Status
```bash
curl http://localhost:8000/trading/status
```

### List Available Strategies
```bash
curl http://localhost:8000/strategies
```

### Health Check
```bash
curl http://localhost:8000/health
```

## Data Download Examples

### Download data for a specific symbol
```bash
python scripts/download_klines.py --symbol BTC/USDT --exchange binance --interval 1m --days 30
```

### Download data for all configured assets
```bash
python scripts/download_klines.py --all --days 30
```

## Python API Examples

### Running a Backtest
```python
import asyncio
import pandas as pd
from core import Backtester
import json

async def run_backtest():
    # Load configuration
    with open('personal_config.json', 'r') as f:
        config = json.load(f)
    
    # Load historical data
    data = pd.read_csv('data/BTC_USDT_1m_binance.csv', index_col=0)
    
    # Create strategy
    class MyStrategy:
        def __init__(self, config):
            self.config = config
        
        async def generate_signal(self, data):
            # Your strategy logic here
            return 'hold'
    
    # Run backtest
    backtester = Backtester(config)
    strategy = MyStrategy(config)
    results = await backtester.run(strategy, data, initial_capital=10000.0, timeframe='1m')
    
    print(f"Total Return: {results['total_return_pct']:.2f}%")
    print(f"Sharpe Ratio: {results['sharpe_ratio']:.4f}")
    print(f"Max Drawdown: {results['max_drawdown_pct']:.2f}%")

asyncio.run(run_backtest())
```

### Optimizing Strategy Parameters
```python
import asyncio
from core import StrategyOptimizer
import json

async def optimize_strategy():
    # Load configuration
    with open('personal_config.json', 'r') as f:
        config = json.load(f)
    
    # Define parameter grid
    param_grid = {
        'rsi_period': [10, 14, 20],
        'rsi_overbought': [65, 70, 75],
        'rsi_oversold': [25, 30, 35]
    }
    
    # Run optimization
    optimizer = StrategyOptimizer(config)
    best_params, best_score = await optimizer.optimize(
        MyStrategy,
        data,
        param_grid,
        metric='sharpe_ratio'
    )
    
    print(f"Best Parameters: {best_params}")
    print(f"Best Sharpe Ratio: {best_score:.4f}")

asyncio.run(optimize_strategy())
```

### Using the Dashboard Programmatically
```python
import asyncio
from ui import Dashboard

async def main():
    dashboard = Dashboard()
    await dashboard.run()

asyncio.run(main())
```

## Configuration

Edit `personal_config.json` to configure your system:

```json
{
    "assets": ["BTC/USDT", "EUR/USD"],
    "oanda_account": "your_account",
    "modules": {
        "utils": ["data_patch_final", "ml_patch_final", "recovery_patch_final"],
        "strategies": ["rsi_strategy"]
    },
    "v2ray": {
        "backup_servers": ["server1:443", "server2:443"]
    }
}
```

## Environment Variables

Create a `.env` file for API keys and secrets:

```
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret
OANDA_API_KEY=your_oanda_api_key
OANDA_ACCOUNT_ID=your_oanda_account_id
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

## Advanced Usage

### Custom Strategy Development
Create a new strategy in `strategies/`:

```python
# strategies/my_custom_strategy.py
import asyncio

class MyCustomStrategy:
    def __init__(self, config, **params):
        self.config = config
        self.params = params
    
    async def generate_signal(self, data):
        # Implement your strategy logic
        # Return 'buy', 'sell', or 'hold'
        return 'hold'
```

### Running Multiple Modes Simultaneously
You can run multiple instances:

```bash
# Terminal 1: API Server
python app.py --mode api --port 8000

# Terminal 2: Trading System
python app.py --mode trading

# Terminal 3: Dashboard
python app.py --mode dashboard
```

## Troubleshooting

### Check Logs
```bash
tail -f logs/trading_system.log
```

### Test API Connection
```bash
curl http://localhost:8000/health
```

### Verify Configuration
```bash
python -c "import json; print(json.dumps(json.load(open('personal_config.json')), indent=2))"
```

## Support

For more information, see:
- README.md - Project overview and installation
- docs/README_FINAL.md - Detailed documentation
- API documentation at http://localhost:8000/docs when API server is running
