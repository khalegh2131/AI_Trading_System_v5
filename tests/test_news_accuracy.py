import pytest
from utils.news_patch_final import NewsPatchFinal

def test_news_accuracy():
    news = NewsPatchFinal()
    assert news.sentiment("Bitcoin surges!")['score'] > 0.7