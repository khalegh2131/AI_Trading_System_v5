import asyncio, json, logging, numpy as np, pandas as pd, aioredis
from utils.v2ray_pre_connector import V2RayPreConnector

class DataPatchFinal:
    def __init__(self, cfg):
        self.cfg = cfg
        self.v2ray = V2RayPreConnector(cfg)
        self.redis = None

    async def run(self):
        try:
            self.redis = await aioredis.from_url("redis://localhost", decode_responses=True)
            tasks = [self._ws(ex, sym) for ex in ["Binance", "OANDA"] for sym in self.cfg['assets']]
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logging.error(f"Redis/Data error: {e}")
            await asyncio.sleep(5)
            await self.run()  # Retry

    async def _ws(self, ex, sym):
        url = {"Binance": f"wss://stream.binance.com:9443/ws/{sym.replace('/','_').lower()}@kline_1m",
               "OANDA": f"wss://stream-fxpractice.oanda.com/v3/accounts/{self.cfg['oanda_account']}/candles/{sym.replace('/','_')}"}
        async for ws in websockets.connect(url[ex], extra_headers=self.v2ray.ws_headers()):
            try:
                async for raw in ws:
                    c = await self._parse(ex, raw)
                    if c and c['x']:
                        await self._save_clean(sym, c)
                    else:
                        await self.fill_gap(sym, c.get('t', int(pd.Timestamp.utcnow().timestamp()*1000)))
            except Exception as e:
                logging.warning(f"{ex} WS failed: {e}")
                await self.v2ray.switch_server()
                await self._failover_http(sym)

    async def fill_gap(self, symbol, missing_ts):
        try:
            prev = await self.redis.lrange(f"clean:{symbol}:1m", 0, 3)
            if not prev:
                logging.warning(f"No data to fill gap for {symbol}")
                return
            data = [json.loads(p) for p in prev]
            avg = {k: np.mean([float(d[k]) for d in data]) for k in ["o", "h", "l", "c", "v"]}
            avg["t"] = missing_ts
            avg["x"] = True
            await self.redis.lpush(f"clean:{symbol}:1m", json.dumps(avg))
            await self.redis.ltrim(f"clean:{symbol}:1m", 0, 9999)
        except Exception as e:
            logging.error(f"Redis gap fill error: {e}")

    async def _failover_http(self, sym):
        for src in ["Binance", "OANDA", "CoinGecko"]:
            try:
                async with aiohttp.ClientSession() as s:
                    if src == "CoinGecko":
                        url = f"https://api.coingecko.com/api/v3/coins/{sym.lower()}/ohlc?vs_currency=usd&days=1"
                        data = await (await s.get(url)).json()
                        return [[float(c[1]), float(c[2]), float(c[3]), float(c[4]), float(c[5])]
                                for c in data if float(c[5]) > 0 and float(c[2]) >= float(c[3])]
                    # Binance/OANDA از zero_gap.py
            except Exception as e:
                logging.warning(f"{src} HTTP failed: {e}")

    async def _parse(self, ex, raw):
        if ex == "Binance":
            k = json.loads(raw)['k']
            return {"t": k['t'], "o": float(k['o']), "h": float(k['h']),
                    "l": float(k['l']), "c": float(k['c']), "v": float(k['v']), "x": k['x']}
        if ex == "OANDA":
            msg = json.loads(raw)
            c = msg['candles'][0]
            return {"t": int(c['time']), "o": float(c['mid']['o']), "h": float(c['mid']['h']),
                    "l": float(c['mid']['l']), "c": float(c['mid']['c']), "v": 1, "x": True}