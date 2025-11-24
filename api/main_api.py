"""Core API functionality for the trading system."""

import asyncio
import logging
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from pathlib import Path


# Initialize FastAPI app
app = FastAPI(
    title="AI Trading System API",
    description="API for AI-powered trading system with backtesting and live trading",
    version="5.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TradingAPI:
    """Main API class for trading system operations."""
    
    def __init__(self, config_path: str = "personal_config.json"):
        """Initialize Trading API.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.logger = logging.getLogger(__name__)
        self.orchestrator = None
        self.orchestrator_task = None
        self.is_running = False
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from file.
        
        Args:
            config_path: Path to config file
            
        Returns:
            Configuration dictionary
        """
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return {}
    
    async def start_trading(self):
        """Start the trading system."""
        try:
            if self.is_running:
                self.logger.warning("Trading system is already running")
                return
            
            self.logger.info("Starting trading system...")
            
            # Import and initialize orchestrator
            from utils.Orchestrator_zero_gap import OrchestratorZeroGap
            self.orchestrator = OrchestratorZeroGap(self.config)
            
            # Start orchestrator and store task reference
            self.orchestrator_task = asyncio.create_task(self.orchestrator.run())
            self.is_running = True
            
            self.logger.info("Trading system started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start trading system: {e}")
            raise
    
    async def stop_trading(self):
        """Stop the trading system."""
        try:
            if not self.is_running:
                self.logger.warning("Trading system is not running")
                return
            
            self.logger.info("Stopping trading system...")
            self.is_running = False
            
            # Cleanup would go here
            
            self.logger.info("Trading system stopped")
            
        except Exception as e:
            self.logger.error(f"Failed to stop trading system: {e}")
            raise


# Create global API instance
trading_api = TradingAPI()


@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logging.info("API server starting up")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "AI Trading System API",
        "version": "5.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "trading_active": trading_api.is_running
    }


@app.post("/trading/start")
async def start_trading_endpoint(background_tasks: BackgroundTasks):
    """Start the trading system."""
    try:
        background_tasks.add_task(trading_api.start_trading)
        return {
            "message": "Trading system starting",
            "status": "initiated"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/trading/stop")
async def stop_trading_endpoint():
    """Stop the trading system."""
    try:
        await trading_api.stop_trading()
        return {
            "message": "Trading system stopped",
            "status": "stopped"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/trading/status")
async def get_trading_status():
    """Get trading system status."""
    return {
        "is_running": trading_api.is_running,
        "config": {
            "assets": trading_api.config.get("assets", []),
            "modules": trading_api.config.get("modules", {})
        }
    }


@app.get("/strategies")
async def list_strategies():
    """List available trading strategies."""
    strategies_path = Path("strategies")
    strategies = []
    
    if strategies_path.exists():
        for file in strategies_path.glob("*.py"):
            if file.name != "__init__.py":
                strategies.append(file.stem)
    
    return {
        "strategies": strategies,
        "count": len(strategies)
    }


@app.post("/backtest")
async def run_backtest(
    strategy: str,
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Run backtest for a strategy."""
    try:
        # This would integrate with the backtesting engine
        return {
            "message": "Backtest initiated",
            "strategy": strategy,
            "symbol": symbol,
            "status": "processing"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/positions")
async def get_positions():
    """Get current trading positions."""
    return {
        "positions": [],
        "total_value": 0.0
    }


def run_api(host: str = "0.0.0.0", port: int = 8000):
    """Run the API server.
    
    Args:
        host: Host address to bind to
        port: Port number to listen on
    """
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_api()
