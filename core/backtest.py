"""Backtesting engine for trading strategies."""

import asyncio
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple


class Backtester:
    """Backtesting engine for evaluating trading strategies."""
    
    def __init__(self, config: Dict):
        """Initialize backtester with configuration.
        
        Args:
            config: Configuration dictionary with backtesting parameters
        """
        self.config = config
        self.results = {}
        self.trades = []
        self.logger = logging.getLogger(__name__)
        
    async def run(self, strategy, data: pd.DataFrame, initial_capital: float = 10000.0) -> Dict:
        """Run backtest on given strategy and data.
        
        Args:
            strategy: Trading strategy instance with generate_signal method
            data: Historical market data DataFrame
            initial_capital: Starting capital for backtest
            
        Returns:
            Dictionary containing backtest results and metrics
        """
        try:
            self.logger.info(f"Starting backtest with initial capital: ${initial_capital}")
            
            capital = initial_capital
            position = 0
            position_price = 0
            equity_curve = []
            
            for idx, row in data.iterrows():
                # Generate trading signal
                signal = await self._get_signal(strategy, data.loc[:idx])
                
                # Execute trade based on signal
                if signal == 'buy' and position == 0:
                    position = capital / row['close']
                    position_price = row['close']
                    capital = 0
                    self.trades.append({
                        'timestamp': idx,
                        'type': 'buy',
                        'price': row['close'],
                        'size': position
                    })
                    self.logger.debug(f"BUY at {row['close']}, size: {position}")
                    
                elif signal == 'sell' and position > 0:
                    capital = position * row['close']
                    pnl = (row['close'] - position_price) / position_price * 100
                    self.trades.append({
                        'timestamp': idx,
                        'type': 'sell',
                        'price': row['close'],
                        'size': position,
                        'pnl': pnl
                    })
                    self.logger.debug(f"SELL at {row['close']}, PnL: {pnl:.2f}%")
                    position = 0
                    position_price = 0
                
                # Calculate current equity
                current_equity = capital + (position * row['close'] if position > 0 else 0)
                equity_curve.append(current_equity)
            
            # Calculate metrics
            final_capital = capital + (position * data.iloc[-1]['close'] if position > 0 else 0)
            self.results = self._calculate_metrics(initial_capital, final_capital, equity_curve)
            
            self.logger.info(f"Backtest completed. Final capital: ${final_capital:.2f}")
            return self.results
            
        except Exception as e:
            self.logger.error(f"Backtest error: {e}")
            raise
    
    async def _get_signal(self, strategy, data: pd.DataFrame) -> str:
        """Get trading signal from strategy.
        
        Args:
            strategy: Trading strategy instance
            data: Historical data up to current point
            
        Returns:
            Trading signal: 'buy', 'sell', or 'hold'
        """
        try:
            if hasattr(strategy, 'generate_signal'):
                signal = await strategy.generate_signal(data)
                return signal
            return 'hold'
        except Exception as e:
            self.logger.warning(f"Signal generation error: {e}")
            return 'hold'
    
    def _calculate_metrics(self, initial: float, final: float, equity_curve: List[float]) -> Dict:
        """Calculate performance metrics.
        
        Args:
            initial: Initial capital
            final: Final capital
            equity_curve: List of equity values over time
            
        Returns:
            Dictionary of performance metrics
        """
        total_return = ((final - initial) / initial) * 100
        
        # Calculate additional metrics
        equity_array = np.array(equity_curve)
        returns = np.diff(equity_array) / equity_array[:-1]
        
        sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        max_drawdown = self._calculate_max_drawdown(equity_array)
        
        winning_trades = [t for t in self.trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in self.trades if t.get('pnl', 0) < 0]
        
        return {
            'initial_capital': initial,
            'final_capital': final,
            'total_return_pct': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown_pct': max_drawdown,
            'total_trades': len(self.trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / len(self.trades) * 100 if self.trades else 0,
            'equity_curve': equity_curve
        }
    
    def _calculate_max_drawdown(self, equity_curve: np.ndarray) -> float:
        """Calculate maximum drawdown percentage.
        
        Args:
            equity_curve: Array of equity values
            
        Returns:
            Maximum drawdown as percentage
        """
        running_max = np.maximum.accumulate(equity_curve)
        drawdown = (equity_curve - running_max) / running_max * 100
        return abs(np.min(drawdown))
    
    def get_results(self) -> Dict:
        """Get backtest results."""
        return self.results
    
    def get_trades(self) -> List[Dict]:
        """Get list of executed trades."""
        return self.trades
