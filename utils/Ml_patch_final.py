import asyncio, tensorflow as tf, torch, pickle, numpy as np
from transformers import TransfoXLConfig, TransfoXLModel
from torch_geometric.nn import GCNConv
from stable_baselines3 import PPO
from utils.data_storage import get_latest_rows
from utils.orchestrator_zero_gap import OrchestratorZeroGap

class MLFinalPatch:
    def __init__(self, cfg):
        self.cfg = cfg
        self.models = {}
        self.orchestrator = OrchestratorZeroGap(cfg)

    async def run(self):
        while True:
            df = await get_latest_rows(5000)
            if len(df) >= 110:
                await self._switch_best(df)
                await self._backtest()
            await asyncio.sleep(1800)

    async def _switch_best(self, df):
        self.models = {"LSTM": self._lstm(), "GNN": self._gnn(), "TXL": self._txl(), "PPO": self._ppo(df)}
        sharpe = {k: self._calc_sharpe(m, df) for k, m in self.models.items()}
        best = max(sharpe, key=sharpe.get)
        pickle.dump(self.models[best], open(f"models/best_{best.lower()}.pkl", "wb"))
        await self.orchestrator.hot_reload()  # Hot-reload مدل

    def _calc_sharpe(self, model, df):
        returns = np.diff(df['c']) / df['c'][:-1]
        return np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) else 0

    def _lstm(self):
        model = tf.keras.Sequential([
            tf.keras.layers.Input(shape=(100, 4)),
            tf.keras.layers.LSTM(64),
            tf.keras.layers.Dense(3, activation='softmax')
        ])
        model.compile(loss='categorical_crossentropy', optimizer='adam')
        return model

    def _gnn(self):
        return GCNConv(4, 3)

    def _txl(self):
        config = TransfoXLConfig(n_layer=12, d_model=256)
        return TransfoXLModel(config)

    def _ppo(self, df):
        from stable_baselines3.common.envs import DummyVecEnv
        return PPO("MlpPolicy", DummyVecEnv([lambda: self._env(df)]), verbose=0)

    async def _backtest(self):
        import pytest
        pytest.main(["-x", "tests/test_backtest.py"])