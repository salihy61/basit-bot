import os
import asyncio
import requests
from telegram import Bot

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SYMBOL = os.getenv("SYMBOL", "BTCUSDT")
bot = Bot(token=TOKEN)

def get_ohlcv(symbol="BTCUSDT", interval="5m", limit=2):
    url = f"https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    data = requests.get(url, params=params).json()
    return [
        {"open": float(d[1]), "high": float(d[2]), "low": float(d[3]), "close": float(d[4])}
        for d in data
    ]

def is_bullish_engulf(prev, curr):
    return prev['close'] < prev['open'] and curr['close'] > curr['open'] and \
           curr['close'] > prev['open'] and curr['open'] < prev['close']

def is_bearish_engulf(prev, curr):
    return prev['close'] > prev['open'] and curr['close'] < curr['open'] and \
           curr['open'] > prev['close'] and curr['close'] < prev['open']

async def run_bot():
    while True:
        try:
            candles = get_ohlcv(symbol=SYMBOL)
            if len(candles) >= 2:
                prev, curr = candles[-2], candles[-1]
                if is_bullish_engulf(prev, curr):
                    await bot.send_message(chat_id=CHAT_ID, text=f"📈 Bullish Engulf on {SYMBOL}")
                elif is_bearish_engulf(prev, curr):
                    await bot.send_message(chat_id=CHAT_ID, text=f"📉 Bearish Engulf on {SYMBOL}")
        except Exception as e:
            await bot.send_message(chat_id=CHAT_ID, text=f"❌ Error: {e}")
        await asyncio.sleep(300)  # 5 dakika

if __name__ == "__main__":
    asyncio.run(run_bot())
