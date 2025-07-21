import asyncio, aiohttp, asyncpraw, logging, os, pytest
from transformers import pipeline
from utils.alert_zero_gap import send_telegram

class NewsPatchFinal:
    def __init__(self):
        self.sentiment = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest")
        self.reddit = asyncpraw.Reddit(client_id=os.getenv("REDDIT_ID"),
                                      client_secret=os.getenv("REDDIT_SECRET"),
                                      user_agent="ai_trading")

    async def run(self):
        await asyncio.gather(self._reddit(), self._whale_real(), self._test_news())

    async def _reddit(self):
        subreddit = await self.reddit.subreddit("cryptocurrency")
        async for post in subreddit.hot(limit=10):
            score = self.sentiment(post.title[:512])[0]
            await send_telegram(f"Reddit: {post.title} → {score['label']}")

    async def _whale_real(self):
        url = f"https://api.whalealert.io/v1/transactions?api_key={os.getenv('WHALE_KEY')}"
        async with aiohttp.ClientSession() as s:
            data = await (await s.get(url)).json()
            for tx in data.get('transactions', []):
                if tx.get('amount_usd', 0) > 1_000_000:
                    await send_telegram(f"🐋 {tx['amount_usd']:,} $ moved")

    async def _test_news(self):
        pytest.main(["-x", "tests/test_news_accuracy.py"])