import requests
import time

TELEGRAM_TOKEN = "8394510966:AAGbpFgVYnbd8UlkN2u_BOvA-SI1QFk1xtA"
CHAT_ID = "8394510966"
send_telegram("✅ Bot is live")

DEX_API = "https://api.dexscreener.com/latest/dex/pairs/solana"

seen = set()

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

def score(pair):
    score = 0

    liquidity = pair.get("liquidity", {}).get("usd", 0)
    volume = pair.get("volume", {}).get("h1", 0)
    buys = pair.get("txns", {}).get("h1", {}).get("buys", 0)
    sells = pair.get("txns", {}).get("h1", {}).get("sells", 0)
    price_change = pair.get("priceChange", {}).get("h1", 0)

    if liquidity > 25000:
        score += 20
    elif liquidity > 10000:
        score += 10

    if volume > 80000:
        score += 20
    elif volume > 20000:
        score += 10

    if buys > sells * 1.5:
        score += 20

    if price_change > 15:
        score += 15

    if buys > 80:
        score += 15

    if liquidity < 5000:
        score -= 20

    return score

while True:
    try:
        res = requests.get(DEX_API).json()

        for pair in res["pairs"]:
            addr = pair["pairAddress"]

            if addr in seen:
                continue
            seen.add(addr)

            s = score(pair)

            if s >= 60:
                name = pair["baseToken"]["name"]
                price = pair["priceUsd"]
                liq = pair.get("liquidity", {}).get("usd", 0)
                buys = pair.get("txns", {}).get("h1", {}).get("buys", 0)
                sells = pair.get("txns", {}).get("h1", {}).get("sells", 0)

                msg = f"""
🚀 HIGH-POTENTIAL COIN

{name}
Score: {s}/100
💧 Liquidity: ${liq}
💰 Price: ${price}

🐋 Buys: {buys}
📉 Sells: {sells}
                """

                send_telegram(msg)

        time.sleep(15)

    except Exception as e:
        print(e)
        time.sleep(10)
