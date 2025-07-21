import asyncio, importlib, inspect
from pathlib import Path
from cryptography.fernet import Fernet

class OrchestratorZeroGap:
    def __init__(self, cfg):
        self.cfg = cfg
        self.modules = {}
        self.fernet = Fernet(Fernet.generate_key())

    async def run(self):
        await self.load_modules()
        await self.hot_reload()

    async def load_modules(self):
        for group, names in self.cfg['modules'].items():
            for name in names:
                module = importlib.import_module(f"{group}.{name}")
                cls = next(c for _, c in inspect.getmembers(module, inspect.isclass))
                self.modules[name] = cls(self.cfg)
                asyncio.create_task(self.modules[name].run())

    async def hot_reload(self):
        mtimes = {}
        while True:
            for path in Path('.').rglob('*.py'):
                if mtimes.get(path) != path.stat().st_mtime:
                    mtimes[path] = path.stat().st_mtime
                    await self.load_modules()
            await asyncio.sleep(5)