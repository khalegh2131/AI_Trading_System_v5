import pytest, subprocess

def test_deploy():
    result = subprocess.run(["docker", "compose", "-f", "docker-compose.yml", "ps"], capture_output=True)
    assert "ai_trading_v5" in result.stdout.decode()