import time
import requests
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ===== CONFIG (PASTE YOUR VALUES HERE) =====
TELEGRAM_TOKEN = "8394510966:AAGbpFgVYnbd8UlkN2u_BOvA-SI1QFk1xtA"
CHAT_ID = 6736189155
WALLET_PUBLIC_KEY = "HYpGuL2ohivog1mtaa4hgHLGHnH186AKqdUBzg4mTV44"

TOKENS = [
    "DezXAZ8z7PnrnRJjz3wXBoRgixCa6s7YaB1pPB263",  # BONK
]

BOT_RUNNING = False

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
            print(f"❌ No route for {token_address}")
            return None

        return float(data["data"][0]["outAmount"]) / 1e9

    except Exception as e:
        print("PRICE ERROR:", e)
        return None


# ===== RUG FILTER (SAFETY CHECK) =====
def is_token_safe(token):
    try:
        url = "https://api.mainnet-beta.solana.com"

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getAccountInfo",
            "params": [
                token,
                {"encoding": "jsonParsed"}
            ]
        }

        res = requests.post(url, json=payload)
        data = res.json()

        if "result" not in data or not data["result"]["value"]:
            print("❌ Token not found")
            return False

        info = data["result"]["value"]["data"]["parsed"]["info"]

        mint_authority = info.get("mintAuthority")
        freeze_authority = info.get("freezeAuthority")

        if mint_authority is not None:
            print("🚫 Mint still enabled (RUG RISK)")
            return False

        if freeze_authority is not None:
            print("🚫 Freeze still enabled (RUG RISK)")
            return False

        print("✅ Token safe")
        return True

    except Exception as e:
        print("SAFETY CHECK ERROR:", e)
        return False


# ===== EXECUTE BUY (SAFE MODE) =====
def execute_buy(token):
    print(f"🚀 BUY SIGNAL: {token}")
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

            print("🔎 Scanning tokens...")

            for token in TOKENS:
                print(f"\nChecking: {token}")

                price = get_token_price(token)

                if price is None:
                    continue

                # 🔥 SAFETY CHECK
                if not is_token_safe(token):
                    print(f"🚫 Skipping unsafe token: {token}")
                    continue

                print(f"🔥 VALID TOKEN → {token}")

                execute_buy(token)

                time.sleep(10)

            time.sleep(5)

        except Exception as e:
            print("MAIN LOOP ERROR:", e)
            time.sleep(5)


# ===== START BOT =====
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("stop", stop_cmd))
    app.add_handler(CommandHandler("status", status_cmd))

    threading.Thread(target=trading_loop, daemon=True).start()

    print("🤖 Telegram bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()