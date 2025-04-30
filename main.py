import os
from binance.um_futures import UMFutures
from telegram import Bot
from datetime import datetime, timedelta
import pandas as pd

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
COINS = os.getenv("COINS", "BTCUSDT").split(",")

bot = Bot(token=TELEGRAM_TOKEN)

client = UMFutures()

def load_last_signal(symbol):
    file = f"{symbol}_last_signal.txt"
    return open(file).read().strip() if os.path.exists(file) else ""

def save_last_signal(symbol, signal):
    with open(f"{symbol}_last_signal.txt", "w") as f:
        f.write(signal)

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

def check_signal(df, symbol):
    prev = df.iloc[-2]
    curr = df.iloc[-1]
    date_now = curr['open_time'].strftime('%Y-%m-%d %H:%M')
    yesterday = curr['open_time'].date() - timedelta(days=1)
    ydf = df[df['open_time'].dt.date == yesterday]

    if ydf.empty:
        return

    high = ydf['high'].max()
    low = ydf['low'].min()
    close = ydf.iloc[-1]['close']
    H3, L3 = calculate_camarilla(high, low, close)
    near_H3 = abs(curr['close'] - H3) / H3 < 0.002
    near_L3 = abs(curr['close'] - L3) / L3 < 0.002

    signal = ""
    if near_H3 and (is_bearish_engulfing(prev['open'], prev['close'], curr['open'], curr['close']) or
                    is_pinbar(curr['open'], curr['high'], curr['low'], curr['close']) or
                    is_shooting_star(curr['open'], curr['high'], curr['low'], curr['close'])):
        signal = f"📉 SHORT Sinyali\n{symbol}\nFiyat: {curr['close']:.2f}\nZaman: {date_now}"

    elif near_L3 and (is_bullish_engulfing(prev['open'], prev['close'], curr['open'], curr['close']) or
                      is_pinbar(curr['open'], curr['high'], curr['low'], curr['close']) or
                      is_hammer(curr['open'], curr['high'], curr['low'], curr['close'])):
        signal = f"📈 LONG Sinyali\n{symbol}\nFiyat: {curr['close']:.2f}\nZaman: {date_now}"

    if signal and signal != load_last_signal(symbol):
        bot.send_message(chat_id=CHAT_ID, text=signal)
        save_last_signal(symbol, signal)
        print(f"📤 Yeni sinyal gönderildi: {symbol}")
    else:
        print(f"🔁 Yeni sinyal yok: {symbol}")

if __name__ == "__main__":
    for coin in COINS:
        try:
            df = get_data(coin.strip())
            check_signal(df, coin.strip())
        except Exception as e:
            print(f"⚠️ {coin} için hata oluştu: {e}")
