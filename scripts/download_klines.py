"""Script to download historical kline/candlestick data from exchanges."""

import asyncio
import logging
import json
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
from pathlib import Path


class KlineDownloader:
    """Download historical kline data from cryptocurrency and forex exchanges."""
    
    def __init__(self, config_path: str = "personal_config.json"):
        """Initialize the kline downloader.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.logger = logging.getLogger(__name__)
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
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
            logging.error(f"Failed to load config: {e}")
            return {}
    
    async def download_binance_klines(self, symbol: str, interval: str = "1m",
                                     start_date: Optional[str] = None,
                                     end_date: Optional[str] = None) -> pd.DataFrame:
        """Download kline data from Binance.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            interval: Kline interval (1m, 5m, 15m, 1h, 1d, etc.)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            DataFrame with kline data
        """
        try:
            import ccxt
            
            self.logger.info(f"Downloading {symbol} klines from Binance...")
            
            exchange = ccxt.binance({
                'enableRateLimit': True,
            })
            
            # Set date range
            if start_date:
                start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp() * 1000)
            else:
                start_ts = int((datetime.now() - timedelta(days=30)).timestamp() * 1000)
            
            if end_date:
                end_ts = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp() * 1000)
            else:
                end_ts = int(datetime.now().timestamp() * 1000)
            
            # Fetch klines
            all_klines = []
            current_ts = start_ts
            
            while current_ts < end_ts:
                try:
                    # ccxt is synchronous, run in executor for async context
                    loop = asyncio.get_event_loop()
                    klines = await loop.run_in_executor(
                        None,
                        lambda: exchange.fetch_ohlcv(
                            symbol,
                            timeframe=interval,
                            since=current_ts,
                            limit=1000
                        )
                    )
                    
                    if not klines:
                        break
                    
                    all_klines.extend(klines)
                    current_ts = klines[-1][0] + 1
                    
                    self.logger.debug(f"Downloaded {len(klines)} klines, total: {len(all_klines)}")
                    
                    # Rate limiting
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    self.logger.warning(f"Error fetching klines: {e}")
                    await asyncio.sleep(2)
                    continue
            
            # Convert to DataFrame
            df = pd.DataFrame(
                all_klines,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df.set_index('timestamp')
            
            self.logger.info(f"Downloaded {len(df)} klines for {symbol}")
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to download Binance klines: {e}")
            raise
    
    async def download_oanda_klines(self, symbol: str, granularity: str = "M1",
                                   start_date: Optional[str] = None,
                                   end_date: Optional[str] = None) -> pd.DataFrame:
        """Download kline data from OANDA.
        
        Args:
            symbol: Currency pair (e.g., 'EUR_USD')
            granularity: Candle granularity (M1, M5, H1, D, etc.)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            DataFrame with kline data
        """
        try:
            self.logger.info(f"Downloading {symbol} klines from OANDA...")
            
            # This would require OANDA API integration
            # Placeholder for demonstration
            self.logger.warning("OANDA API integration pending")
            
            return pd.DataFrame()
            
        except Exception as e:
            self.logger.error(f"Failed to download OANDA klines: {e}")
            raise
    
    async def download_for_symbol(self, symbol: str, exchange: str = "binance",
                                 interval: str = "1m", days: int = 30) -> bool:
        """Download klines for a specific symbol.
        
        Args:
            symbol: Trading symbol
            exchange: Exchange name ('binance' or 'oanda')
            interval: Data interval
            days: Number of days of historical data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            end_date = datetime.now().strftime("%Y-%m-%d")
            
            if exchange.lower() == "binance":
                # Convert symbol format (e.g., BTC/USDT -> BTCUSDT)
                binance_symbol = symbol.replace("/", "")
                df = await self.download_binance_klines(
                    binance_symbol, interval, start_date, end_date
                )
            elif exchange.lower() == "oanda":
                # Convert symbol format (e.g., EUR/USD -> EUR_USD)
                oanda_symbol = symbol.replace("/", "_")
                df = await self.download_oanda_klines(
                    oanda_symbol, interval, start_date, end_date
                )
            else:
                self.logger.error(f"Unknown exchange: {exchange}")
                return False
            
            # Save to file
            if not df.empty:
                filename = self.data_dir / f"{symbol.replace('/', '_')}_{interval}_{exchange}.csv"
                df.to_csv(filename)
                self.logger.info(f"Saved data to {filename}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error downloading data for {symbol}: {e}")
            return False
    
    async def download_all_configured(self, days: int = 30):
        """Download klines for all symbols in configuration.
        
        Args:
            days: Number of days of historical data
        """
        try:
            assets = self.config.get('assets', [])
            
            if not assets:
                self.logger.warning("No assets configured")
                return
            
            self.logger.info(f"Downloading data for {len(assets)} assets...")
            
            tasks = []
            for asset in assets:
                # Determine exchange based on symbol
                if 'USDT' in asset or 'BTC' in asset:
                    exchange = 'binance'
                else:
                    exchange = 'oanda'
                
                tasks.append(self.download_for_symbol(asset, exchange, "1m", days))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful = sum(1 for r in results if r is True)
            self.logger.info(f"Download complete: {successful}/{len(assets)} successful")
            
        except Exception as e:
            self.logger.error(f"Error in batch download: {e}")


async def main():
    """Main entry point for the script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description='Download historical kline data')
    parser.add_argument('--symbol', type=str, help='Trading symbol (e.g., BTC/USDT)')
    parser.add_argument('--exchange', type=str, default='binance', 
                       help='Exchange name (binance/oanda)')
    parser.add_argument('--interval', type=str, default='1m', 
                       help='Data interval (1m, 5m, 1h, 1d)')
    parser.add_argument('--days', type=int, default=30, 
                       help='Number of days of historical data')
    parser.add_argument('--all', action='store_true', 
                       help='Download for all configured assets')
    
    args = parser.parse_args()
    
    downloader = KlineDownloader()
    
    if args.all:
        await downloader.download_all_configured(args.days)
    elif args.symbol:
        success = await downloader.download_for_symbol(
            args.symbol, args.exchange, args.interval, args.days
        )
        if success:
            print(f"✓ Successfully downloaded data for {args.symbol}")
        else:
            print(f"✗ Failed to download data for {args.symbol}")
    else:
        print("Error: Please specify --symbol or use --all")
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
