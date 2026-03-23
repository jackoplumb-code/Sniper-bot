import requests
import time

TELEGRAM_TOKEN = "PASTE_TOKEN"
CHAT_ID = "PASTE_CHAT_ID"

DEX_API = "https://api.dexscreener.com/latest/dex/pairs/solana"

seen = set()

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

def score(pair):
    score = 0

    liquidity = pair.get("liquidity", {}).get("usd", 0)
    volume_5m = pair.get("volume", {}).get("m5", 0)
    buys = pair.get("txns", {}).get("m5", {}).get("buys", 0)
    sells = pair.get("txns", {}).get("m5", {}).get("sells", 0)
    price_change = pair.get("priceChange", {}).get("m5", 0)

    # 💧 Liquidity filter
    if liquidity > 20000:
        score += 20
    elif liquidity > 8000:
        score += 10
    else:
        return 0  # skip trash early

    # 🐋 Volume spike (early whales)
    if volume_5m > 50000:
        score += 25
    elif volume_5m > 15000:
        score += 15

    # 🟢 Buy dominance (very important)
    if buys > sells * 1.8:
        score += 25
    elif buys > sells * 1.3:
        score += 15

    # 🚀 Early momentum
    if price_change > 10:
        score += 15
    elif price_change > 5:
        score += 10

    # 🔥 Activity spike
    if buys > 60:
        score += 15

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

                buys = pair.get("txns", {}).get("m5", {}).get("buys", 0)
                sells = pair.get("txns", {}).get("m5", {}).get("sells", 0)
                vol = pair.get("volume", {}).get("m5", 0)

                msg = f"""
🚀 EARLY RUNNER DETECTED

{name}
Score: {s}/100

💧 Liquidity: ${liq}
📊 5m Volume: ${vol}

🐋 Buys: {buys}
📉 Sells: {sells}

⚡ Strong early momentum + buy pressure
                """

                send_telegram(msg)

        time.sleep(12)

    except Exception as e:
        print(e)
        time.sleep(8)
