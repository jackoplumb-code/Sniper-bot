import time
import requests
import os

# ===== CONFIG =====
TOKEN_ADDRESS = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"
WALLET_PUBLIC_KEY = "HYpGuL2ohivog1mtaa4hgHLGHnH186AKqdUBzg4mTV44"

BUY_PERCENT = 0.1  # 10%
COOLDOWN = 60

# ===== STATE =====
STATE = {
    "last_trade_time": 0,
    "in_position": False
}

# ===== GET SOL BALANCE =====
def get_sol_balance():
    try:
        url = "https://api.mainnet-beta.solana.com"

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [WALLET_PUBLIC_KEY]
        }

        res = requests.post(url, json=payload)
        data = res.json()

        if "result" not in data:
            print("BALANCE ERROR:", data)
            return None

        lamports = data["result"]["value"]
        return lamports / 1e9

    except Exception as e:
        print("BALANCE ERROR:", e)
        return None


# ===== CALCULATE BUY =====
def calculate_buy_amount():
    balance = get_sol_balance()

    if not balance:
        print("Using fallback buy")
        return 0.01

    return balance * BUY_PERCENT


# ===== GET TOKEN PRICE =====
def get_token_price():
    try:
        url = "https://api.jup.ag/v6/quote"

        params = {
            "inputMint": "So11111111111111111111111111111111111111112",
            "outputMint": TOKEN_ADDRESS,
            "amount": 10000000,
            "slippageBps": 1000
        }

        res = requests.get(url, params=params)
        data = res.json()

        if "data" not in data or len(data["data"]) == 0:
            print("No route found")
            return None

        return float(data["data"][0]["outAmount"]) / 1e9

    except Exception as e:
        print("PRICE ERROR:", e)
        return None


# ===== JUPITER SWAP (SAFE MODE) =====
def execute_jupiter_swap(amount_sol):
    try:
        url = "https://api.jup.ag/v6/swap"

        payload = {
            "inputMint": "So11111111111111111111111111111111111111112",
            "outputMint": TOKEN_ADDRESS,
            "amount": int(amount_sol * 1e9),
            "slippageBps": 1000,
            "userPublicKey": WALLET_PUBLIC_KEY,
            "wrapAndUnwrapSol": True
        }

        res = requests.post(url, json=payload)
        data = res.json()

        if "swapTransaction" not in data:
            print("Swap failed:", data)
            return False

        print("✅ Swap transaction created (NOT SENT YET)")
        return True

    except Exception as e:
        print("SWAP ERROR:", e)
        return False


# ===== EXECUTE BUY =====
def execute_buy():
    amount = calculate_buy_amount()

    print(f"🚀 REAL BUY ATTEMPT: {amount} SOL")

    success = execute_jupiter_swap(amount)

    return success


# ===== MAIN LOOP =====
while True:
    try:
        print("Bot running...")

        # cooldown
        if time.time() - STATE["last_trade_time"] < COOLDOWN:
            time.sleep(5)
            continue

        # get price
        price = get_token_price()

        if price is None:
            print("⚠️ Price is None, forcing test buy...")
            success = execute_buy()
        else:
            success = execute_buy()

        if success:
            STATE["in_position"] = True
            STATE["last_trade_time"] = time.time()

        time.sleep(5)

    except Exception as e:
        print("MAIN LOOP ERROR:", e)
        time.sleep(5)