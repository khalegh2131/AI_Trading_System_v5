import asyncio, logging, numpy as np
from utils.alert_zero_gap import send_telegram
from utils.kelly_allocator import kelly_size
from utils.risk_dynamic import compute_correlation

class PositionPatchFinal:
    def __init__(self, cfg):
        self.cfg = cfg
        self.positions = {}  # فرض: از position_sizer.py

    async def run(self):
        while True:
            await self._hedge_and_close()
            await asyncio.sleep(30)

    async def _hedge_and_close(self):
        corr = compute_correlation(self.cfg['assets'])  # از risk_dynamic.py
        hedge_qty = 0.5 * corr * kelly_size(signal=0.5)
        if hedge_qty:
            logging.info(f"Hedging {hedge_qty} units")
        if self._pnl() < -0.02:
            self.positions.clear()  # بستن پوزیشن‌ها
            await send_telegram("🔒 Closed positions at 2% loss")

    def _pnl(self):
        # فرض: از risk_dynamic.py
        return -0.01  # برای تست