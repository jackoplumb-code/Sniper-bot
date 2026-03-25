import time
import requests
import os
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ===== CONFIG =====
TOKENS = [
    "DezXAZ8z7PnrnRJjz3wXBoRgixCa6s7YaB1pPB263",  # BONK
]

WALLET_PUBLIC_KEY = os.getenv("WALLET_PUBLIC_KEY")

BUY_PERCENT = 0.1
COOLDOWN = 60

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))

BOT_RUNNING = False

# ===== STATE =====
STATE = {
    "last_trade_time": 0,
    "in_position": False
}

# ===== GET TOKEN PRICE =====
def get_token_price(token_address):
    try:
        url = "https://api.jup.ag/v6/quote"

        params = {
            "inputMint": "So11111111111111111111111111111111111111112",
            "outputMint": token_address,
            "amount": 100000000,
            "slippageBps": 1000
        }

        res = requests.get(
            url,
            params=params,
            headers={
                "accept": "application/json",
                "User-Agent": "Mozilla/5.0"
            },
            timeout=10
        )

        data = res.json()
        print("JUP RESPONSE:", data)

        if "data" not in data or len(data["data"]) == 0:
            print(f"No route for {token_address}")
            return None

        return float(data["data"][0]["outAmount"]) / 1e9

    except Exception as e:
        print("PRICE ERROR:", e)
        return None

# ===== GET BALANCE =====
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

        return data["result"]["value"] / 1e9

    except Exception as e:
        print("BALANCE ERROR:", e)
        return None

# ===== CALCULATE BUY =====
def calculate_buy_amount():
    balance = get_sol_balance()

    if not balance:
        return 0.01

    return balance * BUY_PERCENT

# ===== EXECUTE BUY (SAFE MODE) =====
def execute_buy(token):
    amount = calculate_buy_amount()
    print(f"🚀 BUY SIGNAL: {token} | {amount} SOL")

    # SAFE MODE
    print("⚠️ Trade not executed (testing mode)")

    return True

# ===== TELEGRAM COMMANDS =====
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_RUNNING
    BOT_RUNNING = True
    await update.message.reply_text("🚀 Bot started")


async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_RUNNING
    BOT_RUNNING = False
    await update.message.reply_text("🛑 Bot stopped")


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = "RUNNING" if BOT_RUNNING else "STOPPED"
    await update.message.reply_text(f"📊 Status: {status}")

# ===== MAIN TRADING LOOP =====
def trading_loop():
    global BOT_RUNNING

    while True:
        try:
            if not BOT_RUNNING:
                time.sleep(2)
                continue

            print("Scanning tokens...")

            for token in TOKENS:
                print(f"Checking: {token}")

                price = get_token_price(token)

                if price is None:
                    continue

                print(f"VALID TOKEN → {token}")

                success = execute_buy(token)

                if success:
                    STATE["last_trade_time"] = time.time()
                    time.sleep(10)

            time.sleep(5)

        except Exception as e:
            print("MAIN LOOP ERROR:", e)
            time.sleep(5)

# ===== MAIN =====
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("stop", stop_cmd))
    app.add_handler(CommandHandler("status", status_cmd))

    threading.Thread(target=trading_loop).start()

    print("Telegram bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()