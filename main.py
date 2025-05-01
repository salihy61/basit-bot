import os
import time
import requests
from telegram import Bot

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SYMBOL = os.getenv("SYMBOL", "BTCUSDT")  # örneğin BTCUSDT
bot = Bot(token=TOKEN)

def send_signal(message):
    bot.send_message(chat_id=CHAT_ID, text=message)

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

while True:
    try:
        candles = get_ohlcv(symbol=SYMBOL)
        if len(candles) >= 2:
            prev, curr = candles[-2], candles[-1]
            if is_bullish_engulf(prev, curr):
                send_signal(f"📈 Bullish Engulf detected on {SYMBOL}!")
            elif is_bearish_engulf(prev, curr):
                send_signal(f"📉 Bearish Engulf detected on {SYMBOL}!")
        time.sleep(300)  # 5 dakika bekle
    except Exception as e:
        send_signal(f"❌ Error: {e}")
        time.sleep(300)
