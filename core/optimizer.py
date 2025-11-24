"""Strategy optimization module for parameter tuning."""

import asyncio
import logging
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from itertools import product


class StrategyOptimizer:
    """Optimizer for finding best strategy parameters."""
    
    def __init__(self, config: Dict):
        """Initialize optimizer with configuration.
        
        Args:
            config: Configuration dictionary with optimization parameters
        """
        self.config = config
        self.best_params = {}
        self.results_history = []
        self.logger = logging.getLogger(__name__)
        
    async def optimize(self, strategy_class, data, param_grid: Dict, 
                      metric: str = 'sharpe_ratio') -> Tuple[Dict, float]:
        """Optimize strategy parameters using grid search.
        
        Args:
            strategy_class: Strategy class to optimize
            data: Historical data for backtesting
            param_grid: Dictionary of parameters and their possible values
            metric: Metric to optimize ('sharpe_ratio', 'total_return', etc.)
            
        Returns:
            Tuple of (best_parameters, best_score)
        """
        try:
            self.logger.info(f"Starting optimization with metric: {metric}")
            
            # Generate parameter combinations
            param_combinations = self._generate_param_combinations(param_grid)
            self.logger.info(f"Testing {len(param_combinations)} parameter combinations")
            
            best_score = float('-inf')
            best_params = {}
            
            # Test each parameter combination
            for idx, params in enumerate(param_combinations):
                try:
                    # Create strategy instance with parameters
                    strategy = strategy_class(self.config, **params)
                    
                    # Run backtest
                    from core.backtest import Backtester
                    backtester = Backtester(self.config)
                    results = await backtester.run(strategy, data)
                    
                    # Extract score
                    score = results.get(metric, float('-inf'))
                    
                    # Store results
                    self.results_history.append({
                        'params': params,
                        'score': score,
                        'results': results
                    })
                    
                    # Update best parameters
                    if score > best_score:
                        best_score = score
                        best_params = params
                        self.logger.info(f"New best {metric}: {best_score:.4f} with params: {params}")
                    
                    if (idx + 1) % 10 == 0:
                        self.logger.debug(f"Progress: {idx + 1}/{len(param_combinations)} combinations tested")
                        
                except Exception as e:
                    self.logger.warning(f"Error testing params {params}: {e}")
                    continue
            
            self.best_params = best_params
            self.logger.info(f"Optimization complete. Best {metric}: {best_score:.4f}")
            return best_params, best_score
            
        except Exception as e:
            self.logger.error(f"Optimization error: {e}")
            raise
    
    def _generate_param_combinations(self, param_grid: Dict) -> List[Dict]:
        """Generate all parameter combinations from grid.
        
        Args:
            param_grid: Dictionary of parameters and their possible values
            
        Returns:
            List of parameter dictionaries
        """
        keys = param_grid.keys()
        values = param_grid.values()
        combinations = []
        
        for combo in product(*values):
            param_dict = dict(zip(keys, combo))
            combinations.append(param_dict)
        
        return combinations
    
    async def bayesian_optimize(self, strategy_class, data, param_bounds: Dict,
                                n_iterations: int = 50, metric: str = 'sharpe_ratio') -> Tuple[Dict, float]:
        """Optimize using Bayesian optimization (simplified version).
        
        Args:
            strategy_class: Strategy class to optimize
            data: Historical data for backtesting
            param_bounds: Dictionary of parameters and their (min, max) bounds
            n_iterations: Number of optimization iterations
            metric: Metric to optimize
            
        Returns:
            Tuple of (best_parameters, best_score)
        """
        try:
            self.logger.info(f"Starting Bayesian optimization with {n_iterations} iterations")
            
            best_score = float('-inf')
            best_params = {}
            
            # Initialize with random samples
            for i in range(n_iterations):
                # Sample random parameters within bounds
                params = {
                    key: np.random.uniform(bounds[0], bounds[1])
                    for key, bounds in param_bounds.items()
                }
                
                try:
                    # Test parameters
                    strategy = strategy_class(self.config, **params)
                    from core.backtest import Backtester
                    backtester = Backtester(self.config)
                    results = await backtester.run(strategy, data)
                    
                    score = results.get(metric, float('-inf'))
                    
                    self.results_history.append({
                        'params': params,
                        'score': score,
                        'results': results
                    })
                    
                    if score > best_score:
                        best_score = score
                        best_params = params
                        self.logger.info(f"Iteration {i+1}: New best {metric}: {best_score:.4f}")
                    
                except Exception as e:
                    self.logger.warning(f"Error in iteration {i+1}: {e}")
                    continue
            
            self.best_params = best_params
            self.logger.info(f"Bayesian optimization complete. Best {metric}: {best_score:.4f}")
            return best_params, best_score
            
        except Exception as e:
            self.logger.error(f"Bayesian optimization error: {e}")
            raise
    
    def get_best_params(self) -> Dict:
        """Get best parameters found during optimization."""
        return self.best_params
    
    def get_results_history(self) -> List[Dict]:
        """Get history of all optimization results."""
        return self.results_history
    
    def get_top_n_params(self, n: int = 5) -> List[Tuple[Dict, float]]:
        """Get top N parameter sets by score.
        
        Args:
            n: Number of top results to return
            
        Returns:
            List of (parameters, score) tuples
        """
        sorted_results = sorted(
            self.results_history,
            key=lambda x: x['score'],
            reverse=True
        )
        return [(r['params'], r['score']) for r in sorted_results[:n]]
