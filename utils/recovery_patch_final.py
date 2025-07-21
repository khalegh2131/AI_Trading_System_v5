import asyncio, logging, aiohttp, pytest, time
from utils.alert_zero_gap import send_telegram
from utils.data_patch_final import DataPatchFinal

class RecoveryPatchFinal:
    def __init__(self, cfg):
        self.cfg = cfg
        self.data = DataPatchFinal(cfg)

    async def run(self):
        while True:
            await self._fill_and_alert()
            await asyncio.sleep(30)

    async def _fill_and_alert(self):
        for sym in self.cfg['assets']:
            await self.data.fill_gap(sym, int(time.time() * 1000))
        if self._pnl() < -0.02:
            await send_telegram(f"⚠️ Loss = {self._pnl()*100:.2f}%")
        if self._latency() > 500:
            await send_telegram(f"⚠️ Latency = {self._latency()} ms")
        pytest.main(["-x", "tests/test_stress.py"])

    def _pnl(self):
        # فرض: از risk_dynamic.py
        return -0.01  # برای تست (باید از API صرافی بگیره)

    def _latency(self):
        # فرض: محاسبه latency از log_manager.py
        return 100  # برای تست (باید از API یا سرور بگیره)