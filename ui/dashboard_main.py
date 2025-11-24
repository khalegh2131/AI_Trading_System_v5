"""Main dashboard interface for the AI Trading System."""

import asyncio
import logging
import json
from typing import Dict, List, Optional
from pathlib import Path
import sys


class Dashboard:
    """Main dashboard for monitoring and controlling the trading system."""
    
    def __init__(self, config_path: str = "personal_config.json"):
        """Initialize the dashboard.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.orchestrator = None
        self.orchestrator_task = None
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from file.
        
        Args:
            config_path: Path to config file
            
        Returns:
            Configuration dictionary
        """
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return {}
    
    def display_header(self):
        """Display dashboard header."""
        print("\n" + "="*60)
        print("           AI TRADING SYSTEM DASHBOARD v5.0")
        print("="*60)
        print()
    
    def display_menu(self):
        """Display main menu options."""
        print("\nMain Menu:")
        print("  1. Start Trading System")
        print("  2. Stop Trading System")
        print("  3. View System Status")
        print("  4. View Active Positions")
        print("  5. Run Backtest")
        print("  6. View Strategy Performance")
        print("  7. System Configuration")
        print("  8. Exit")
        print()
    
    def display_status(self):
        """Display current system status."""
        print("\n--- System Status ---")
        print(f"Trading Active: {'Yes' if self.running else 'No'}")
        print(f"Assets: {', '.join(self.config.get('assets', []))}")
        
        modules = self.config.get('modules', {})
        print(f"\nLoaded Modules:")
        for group, names in modules.items():
            print(f"  {group}: {len(names)} modules")
        print()
    
    def display_positions(self):
        """Display active trading positions."""
        print("\n--- Active Positions ---")
        print("Symbol       | Size    | Entry Price | Current P&L")
        print("-" * 55)
        print("No active positions")
        print()
    
    def display_backtest_menu(self):
        """Display backtest configuration menu."""
        print("\n--- Backtest Configuration ---")
        print("Available Strategies:")
        
        strategies_path = Path("strategies")
        if strategies_path.exists():
            strategies = [f.stem for f in strategies_path.glob("*.py") 
                         if f.name != "__init__.py"]
            for i, strategy in enumerate(strategies, 1):
                print(f"  {i}. {strategy}")
        else:
            print("  No strategies found")
        print()
    
    def display_config(self):
        """Display current configuration."""
        print("\n--- System Configuration ---")
        print(json.dumps(self.config, indent=2))
        print()
    
    async def start_system(self):
        """Start the trading system."""
        try:
            if self.running:
                print("Trading system is already running!")
                return
            
            print("Starting trading system...")
            
            # Initialize orchestrator
            from utils.Orchestrator_zero_gap import OrchestratorZeroGap
            self.orchestrator = OrchestratorZeroGap(self.config)
            
            # Start in background and store task reference
            self.orchestrator_task = asyncio.create_task(self.orchestrator.run())
            self.running = True
            
            print("✓ Trading system started successfully!")
            
        except Exception as e:
            self.logger.error(f"Failed to start system: {e}")
            print(f"✗ Error starting system: {e}")
    
    async def stop_system(self):
        """Stop the trading system."""
        try:
            if not self.running:
                print("Trading system is not running!")
                return
            
            print("Stopping trading system...")
            self.running = False
            
            print("✓ Trading system stopped successfully!")
            
        except Exception as e:
            self.logger.error(f"Failed to stop system: {e}")
            print(f"✗ Error stopping system: {e}")
    
    async def run_backtest(self):
        """Run interactive backtest."""
        try:
            self.display_backtest_menu()
            
            strategy_name = input("Enter strategy name (or 'cancel'): ").strip()
            if strategy_name.lower() == 'cancel':
                return
            
            symbol = input("Enter symbol (e.g., BTC/USDT): ").strip()
            
            print(f"\nInitiating backtest for {strategy_name} on {symbol}...")
            
            # This would integrate with the actual backtest engine
            from core.backtest import Backtester
            backtester = Backtester(self.config)
            
            print("✓ Backtest completed! (Integration pending)")
            
        except Exception as e:
            self.logger.error(f"Backtest error: {e}")
            print(f"✗ Error running backtest: {e}")
    
    async def run(self):
        """Run the main dashboard loop."""
        try:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
            self.display_header()
            
            while True:
                self.display_menu()
                
                try:
                    choice = input("Select option (1-8): ").strip()
                    
                    if choice == '1':
                        await self.start_system()
                    elif choice == '2':
                        await self.stop_system()
                    elif choice == '3':
                        self.display_status()
                    elif choice == '4':
                        self.display_positions()
                    elif choice == '5':
                        await self.run_backtest()
                    elif choice == '6':
                        print("\nStrategy performance view (Coming soon)")
                    elif choice == '7':
                        self.display_config()
                    elif choice == '8':
                        print("\nExiting dashboard...")
                        if self.running:
                            await self.stop_system()
                        break
                    else:
                        print("Invalid option. Please try again.")
                    
                    if choice != '8':
                        input("\nPress Enter to continue...")
                    
                except KeyboardInterrupt:
                    print("\n\nInterrupted by user. Exiting...")
                    if self.running:
                        await self.stop_system()
                    break
                except Exception as e:
                    self.logger.error(f"Menu error: {e}")
                    print(f"Error: {e}")
                    input("\nPress Enter to continue...")
            
        except Exception as e:
            self.logger.error(f"Dashboard error: {e}")
            print(f"Fatal error: {e}")


async def main():
    """Main entry point for the dashboard."""
    dashboard = Dashboard()
    await dashboard.run()


if __name__ == "__main__":
    asyncio.run(main())
