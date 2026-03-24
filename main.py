import time
import requests
import os

# ====== USER CONFIG ======
WALLET_PUBLIC_KEY = "HYpGuL2ohivog1mtaa4hgHLGHnH186AKqdUBzg4mTV44"
TOKEN_ADDRESS = os.getenv("TOKEN_ADDRESS")  # set in Railway

BUY_PERCENT = 0.05  # 5% per trade (safe start)
COOLDOWN_SECONDS = 60

# ====== STATE ======
STATE = {
    "in_position": False,
    "last_trade_time": 0
}

# ====== GET SOL BALANCE ======
def get_sol_balance():
    try:
        url = "https://api.mainnet-beta.solana.com"

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [WALLET_PUBLIC_KEY]
        }

        response = requests.post(url, json=payload)
        data = response.json()

        lamports = data["result"]["value"]
        return lamports / 1e9

    except Exception as e:
        print("BALANCE ERROR:", e)
        return None

# ====== CALCULATE BUY ======
def calculate_buy_amount():
    balance = get_sol_balance()

    if not balance:
        print("Using fallback buy")
        return 0.01

    return balance * BUY_PERCENT

# ====== GET TOKEN PRICE ======
def get_token_price():
    try:
        url = "https://api.jup.ag/v6/quote"

        params = {
            "inputMint": "So11111111111111111111111111111111111111112",
            "outputMint": TOKEN_ADDRESS,
            "amount": 10000000,  # 0.01 SOL
            "slippageBps": 1000
        }

        res = requests.get(url, params=params)
        data = res.json()

        return float(data["outAmount"]) if "outAmount" in data else None

    except Exception as e:
        print("PRICE ERROR:", e)
        return None

# ====== EXECUTE BUY (SIMULATED STILL) ======
def execute_buy():
    amount = calculate_buy_amount()
    print(f"REAL BUY: {amount} SOL")

    # ⚠️ STILL SIMULATED (no real tx yet)
    return True

# ====== EXECUTE SELL (SIMULATED) ======
def execute_sell():
    print("SELL (simulated)")
    return True

# ====== MAIN LOOP ======
while True:
    try:
        print("Bot running...")

        # cooldown
        if time.time() - STATE["last_trade_time"] < 60:
            time.sleep(5)
            continue

        # get price
        price = get_token_price()

        if price is None:
             print("⚠️ Price is None, forcing test buy...")
        
        if True:
            success = execute_buy()

            if success:
                STATE["in_position"] = True
                STATE["last_trade_time"] = time.time()

        time.sleep(5)

    except Exception as e:
        print("MAIN LOOP ERROR:", e)
        time.sleep(5)