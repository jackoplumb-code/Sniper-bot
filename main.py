import time
import requests
import os

MIN_VOLUME = 50000
MIN_LIQUIDITY = 10000
MIN_PRICE_CHANGE = 0.1  # 10%

COOLDOWN_SECONDS = 60

last_trade_time = 0

TOKEN_ADDRESS = os.getenv("TOKEN_ADDRESS")

CONFIG = {
    "TRAILING_STOP": 0.15,
    "STOP_LOSS": 0.85,
    "PARTIAL_TP": 1.5,
    "MAX_HOLD_TIME": 180,
    "MIN_LIQUIDITY": 5000,
    "MIN_VOLUME": 15000,
    "MIN_SCORE": 60
}

STATE = {
    "entry_price": None,
    "highest_price": None,
    "stop_price": None,
    "entry_time": None,
    "partial_sold": False
}

# ================= DATA =================

def get_token_data():
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{TOKEN_ADDRESS}"
        res = requests.get(url, timeout=10)

        if res.status_code != 200:
            print("Bad response from API")
            return None

        data = res.json()

        if not data or "pairs" not in data or not data["pairs"]:
            print("No pairs found")
            return None

        pair = data["pairs"][0]

        return {
    "price": float(pair.get("priceUsd", 0)),
    "volume": float(pair.get("volume", {}).get("h24", 0)),
    "liquidity": float(pair.get("liquidity", {}).get("usd", 0)),
    "price_change": float(pair.get("priceChange", {}).get("h1", 0)),
}

    except Exception as e:
        print("DATA ERROR:", e)
        return None

# ================= LOGIC =================

def score_token(data):
    score = 0
    if data["volume"] > CONFIG["MIN_VOLUME"]:
        score += 30
    if data["liquidity"] > CONFIG["MIN_LIQUIDITY"]:
        score += 30
    return score

def should_enter(data):
    global last_trade_time

    now = time.time()

    # cooldown (prevents spam trades)
    if now - last_trade_time < COOLDOWN_SECONDS:
        return False

    # strong filters
    if data["volume"] < MIN_VOLUME:
        return False

    if data["liquidity"] < MIN_LIQUIDITY:
        return False

    if data["price_change"] < MIN_PRICE_CHANGE:
        return False

    return True

def on_buy(price):
    global last_trade_time

    STATE["entry_price"] = price
    STATE["highest_price"] = price
    STATE["stop_price"] = price * (1 - CONFIG["TRAILING_STOP"])
    STATE["entry_time"] = time.time()
    STATE["partial_sold"] = False

    last_trade_time = time.time()

def update_trailing(price):
    if price > STATE["highest_price"]:
        STATE["highest_price"] = price
        STATE["stop_price"] = price * (1 - CONFIG["TRAILING_STOP"])

def should_exit(data):
    price = data["price"]

    if price <= STATE["entry_price"] * CONFIG["STOP_LOSS"]:
        return "stop_loss"

    if price <= STATE["stop_price"]:
        return "trailing_stop"

    if time.time() - STATE["entry_time"] > CONFIG["MAX_HOLD_TIME"]:
        return "time_exit"

    return None

def should_partial(price):
    return (
        not STATE["partial_sold"]
        and price >= STATE["entry_price"] * CONFIG["PARTIAL_TP"]
    )

# ================= FAKE EXECUTION =================

def execute_buy():
    print("FAKE BUY")
    return get_token_data()["price"]

def execute_sell(percent, reason):
    print(f"FAKE SELL {percent*100}% | {reason}")

# ================= MAIN LOOP =================

while True:
    try:
        data = get_token_data()

        if not data:
            time.sleep(2)
            continue

        if STATE["entry_price"] is None:
            if should_enter(data):
                price = execute_buy()
                on_buy(price)

        else:
            update_trailing(data["price"])

            if should_partial(data["price"]):
                execute_sell(0.5, "partial_tp")
                STATE["partial_sold"] = True

            reason = should_exit(data)
            if reason:
                execute_sell(1.0, reason)
                STATE["entry_price"] = None

        time.sleep(1)

    except Exception as e:
        print("MAIN LOOP ERROR:", e)
        time.sleep(3)