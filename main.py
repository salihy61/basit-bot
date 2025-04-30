from binance.um_futures import UMFutures
from telegram import Bot
import pandas as pd
import os
from datetime import datetime, timedelta
import time

client = UMFutures()
bot = Bot(token=os.environ["7958567842:AAH4vwZ1lqhcC4O-UJ4XgjIgcAE7nDjqPjU"])
CHAT_ID = os.environ["462113916"]

def get_data(symbol, limit=150):
    df = pd.DataFrame(client.klines(symbol=symbol, interval='15m', limit=limit),
                      columns=['open_time','open','high','low','close','volume','close_time',
                               'quote','trades','taker_buy_base','taker_buy_quote','ignore'])
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
    return df

def calculate_camarilla(high, low, close):
    rng = high - low
    H3 = close + (rng * 1.1 / 4)
    L3 = close - (rng * 1.1 / 4)
    return H3, L3

def is_bullish_engulfing(po, pc, co, cc):
    return pc < po and cc > co and cc > po and co < pc

def is_bearish_engulfing(po, pc, co, cc):
    return pc > po and cc < co and cc < po and co > pc

def is_pinbar(o, h, l, c):
    body = abs(c - o)
    upper = h - max(o, c)
    lower = min(o, c) - l
    return (upper > body * 2 or lower > body * 2) and (h - l > 0)

def is_hammer(o, h, l, c):
    body = abs(c - o)
    lower = min(o, c) - l
    upper = h - max(o, c)
    return lower > body * 2 and upper < body

def is_shooting_star(o, h, l, c):
    body = abs(c - o)
    upper = h - max(o, c)
    lower = min(o, c) - l
    return upper > body * 2 and lower < body

def check_signal(df, symbol='BTCUSDT'):
    prev = df.iloc[-2]
    curr = df.iloc[-1]
    date_now = curr['open_time'].strftime('%Y-%m-%d %H:%M')

    today = curr['open_time'].date()
    yesterday = today - timedelta(days=1)
    ydf = df[df['open_time'].dt.date == yesterday]

    if ydf.empty:
        return None

    high = ydf['high'].max()
    low = ydf['low'].min()
    close = ydf.iloc[-1]['close']
    H3, L3 = calculate_camarilla(high, low, close)

    near_H3 = abs(curr['close'] - H3) / H3 < 0.002
    near_L3 = abs(curr['close'] - L3) / L3 < 0.002

    if near_H3 and (is_bearish_engulfing(prev['open'], prev['close'], curr['open'], curr['close']) or
                    is_pinbar(curr['open'], curr['high'], curr['low'], curr['close']) or
                    is_shooting_star(curr['open'], curr['high'], curr['low'], curr['close'])):
        return f"📉 SHORT sinyali {symbol} - Fiyat: {curr['close']:.2f} - {date_now}"

    if near_L3 and (is_bullish_engulfing(prev['open'], prev['close'], curr['open'], curr['close']) or
                    is_pinbar(curr['open'], curr['high'], curr['low'], curr['close']) or
                    is_hammer(curr['open'], curr['high'], curr['low'], curr['close'])):
        return f"📈 LONG sinyali {symbol} - Fiyat: {curr['close']:.2f} - {date_now}"

    return None

def run():
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "AVAXUSDT", "XRPUSDT"]  # 🔁 takip edilecek coin listesi
    while True:
        try:
            for symbol in symbols:
                df = get_data(symbol)
                signal = check_signal(df, symbol)
                if signal:
                    bot.send_message(chat_id=CHAT_ID, text=signal)
                    print(f"📤 Sinyal gönderildi ({symbol}):", signal)
                else:
                    print(f"🔁 {symbol} için sinyal yok.")
        except Exception as e:
            print("❌ Hata:", e)
        time.sleep(60 * 15)

if __name__ == "__main__":
    run()
