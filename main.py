import requests
import time

TELEGRAM_TOKEN = "8394510966:AAGbpFgVYnbd8UlkN2u_BOvA-SI1QFk1xtA"
CHAT_ID = "6736189155"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# TEST MESSAGE (safe placement)
send_telegram("✅ Bot is live")

DEX_API = "https://api.dexscreener.com/latest/dex/pairs/solana"

seen = set()

def score(pair):
    return 60

while True:
    try:
        res = requests.get(DEX_API).json()

        for pair in res["pairs"]:
            addr = pair["pairAddress"]

            if addr in seen:
                continue
            seen.add(addr)

            name = pair["baseToken"]["name"]

            send_telegram(f"Test coin detected: {name}")

        time.sleep(30)

    except Exception as e:
        print(e)
        time.sleep(10)
