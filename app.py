"""Main application entry point for AI Trading System v5."""

import asyncio
import logging
import argparse
import sys
from pathlib import Path


def setup_logging(level: str = "INFO"):
    """Setup logging configuration.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/trading_system.log', mode='a')
        ]
    )


async def run_trading_system(config_path: str = "personal_config.json"):
    """Run the main trading system.
    
    Args:
        config_path: Path to configuration file
    """
    try:
        logger = logging.getLogger(__name__)
        logger.info("Starting AI Trading System v5...")
        
        # Initialize orchestrator
        from utils.Orchestrator_zero_gap import OrchestratorZeroGap
        import json
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        orchestrator = OrchestratorZeroGap(config)
        
        logger.info("Trading system initialized successfully")
        logger.info(f"Assets: {config.get('assets', [])}")
        logger.info(f"Modules: {list(config.get('modules', {}).keys())}")
        
        # Run orchestrator
        await orchestrator.run()
        
    except KeyboardInterrupt:
        logger.info("Trading system interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error in trading system: {e}", exc_info=True)
        raise


async def run_dashboard():
    """Run the interactive dashboard."""
    try:
        from ui.dashboard_main import Dashboard
        
        dashboard = Dashboard()
        await dashboard.run()
        
    except Exception as e:
        logging.error(f"Dashboard error: {e}", exc_info=True)
        raise


async def run_api_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the API server.
    
    Args:
        host: Host address to bind to
        port: Port number
    """
    try:
        from api.main_api import run_api
        
        logging.info(f"Starting API server on {host}:{port}")
        run_api(host, port)
        
    except Exception as e:
        logging.error(f"API server error: {e}", exc_info=True)
        raise


async def run_backtest(strategy: str, symbol: str, days: int = 30):
    """Run a backtest.
    
    Args:
        strategy: Strategy name
        symbol: Trading symbol
        days: Number of days of historical data
    """
    try:
        logger = logging.getLogger(__name__)
        logger.info(f"Running backtest: {strategy} on {symbol}")
        
        # Load configuration
        import json
        with open("personal_config.json", 'r') as f:
            config = json.load(f)
        
        # Initialize backtester
        from core.backtest import Backtester
        backtester = Backtester(config)
        
        # For now, create sample data
        import pandas as pd
        import numpy as np
        from datetime import datetime, timedelta
        
        dates = pd.date_range(
            end=datetime.now(),
            periods=days * 1440,  # 1 minute intervals
            freq='1min'
        )
        
        # Generate sample price data
        prices = 100 + np.cumsum(np.random.randn(len(dates)) * 0.1)
        
        data = pd.DataFrame({
            'open': prices,
            'high': prices * 1.01,
            'low': prices * 0.99,
            'close': prices,
            'volume': np.random.randint(1000, 10000, len(dates))
        }, index=dates)
        
        logger.info(f"Generated sample data: {len(data)} rows")
        
        # TODO: Load actual strategy and run backtest
        # results = await backtester.run(strategy_instance, data)
        
        logger.info("Backtest completed (sample data used)")
        print("\n" + "="*60)
        print("BACKTEST RESULTS")
        print("="*60)
        print(f"Strategy: {strategy}")
        print(f"Symbol: {symbol}")
        print(f"Period: {days} days")
        print("Note: Full integration pending")
        print("="*60 + "\n")
        
    except Exception as e:
        logging.error(f"Backtest error: {e}", exc_info=True)
        raise


def main():
    """Main entry point with command-line interface."""
    parser = argparse.ArgumentParser(
        description='AI Trading System v5',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run the main trading system
  python app.py
  
  # Run the interactive dashboard
  python app.py --mode dashboard
  
  # Run the API server
  python app.py --mode api --port 8000
  
  # Run a backtest
  python app.py --mode backtest --strategy rsi_strategy --symbol BTC/USDT
  
  # Show version
  python app.py --version
        """
    )
    
    parser.add_argument(
        '--mode',
        type=str,
        default='trading',
        choices=['trading', 'dashboard', 'api', 'backtest'],
        help='Operating mode (default: trading)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='personal_config.json',
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='API server host (for api mode)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='API server port (for api mode)'
    )
    
    parser.add_argument(
        '--strategy',
        type=str,
        help='Strategy name (for backtest mode)'
    )
    
    parser.add_argument(
        '--symbol',
        type=str,
        help='Trading symbol (for backtest mode)'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Number of days for backtest'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='AI Trading System v5.0.0'
    )
    
    args = parser.parse_args()
    
    # Create logs directory if it doesn't exist
    Path('logs').mkdir(exist_ok=True)
    
    # Setup logging
    setup_logging(args.log_level)
    
    logger = logging.getLogger(__name__)
    logger.info("="*60)
    logger.info("AI Trading System v5.0.0")
    logger.info("="*60)
    
    # Run in selected mode
    try:
        if args.mode == 'trading':
            logger.info("Mode: Trading System")
            asyncio.run(run_trading_system(args.config))
            
        elif args.mode == 'dashboard':
            logger.info("Mode: Interactive Dashboard")
            asyncio.run(run_dashboard())
            
        elif args.mode == 'api':
            logger.info(f"Mode: API Server ({args.host}:{args.port})")
            asyncio.run(run_api_server(args.host, args.port))
            
        elif args.mode == 'backtest':
            if not args.strategy or not args.symbol:
                parser.error("--strategy and --symbol are required for backtest mode")
            logger.info(f"Mode: Backtest ({args.strategy} on {args.symbol})")
            asyncio.run(run_backtest(args.strategy, args.symbol, args.days))
            
    except KeyboardInterrupt:
        logger.info("\nShutdown initiated by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
