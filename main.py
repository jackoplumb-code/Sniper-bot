import os
import time
import base64
import threading
import requests
import base58

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from solders.keypair import Keypair
from solders.transaction import VersionedTransaction

# ================= CONFIG =================
TELEGRAM_TOKEN = os.getenv("8394510966:AAGbpFgVYnbd8UlkN2u_BOvA-SI1QFk1xtA")
PRIVATE_KEY = os.getenv("5MVs88jnFpbJHce29pfm1jLo8GekjWg7JVsfrkuuiNoFQvP3bsMf4jgWNT3oekrKJ4i9P1eZpWVwQkfDQBjW8b8C")
RPC_URL = "https://api.mainnet-beta.solana.com"

wallet = Keypair.from_bytes(base58.b58decode(PRIVATE_KEY))

TOKENS = [
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
]

BOT_RUNNING = {"value": True}

POSITIONS = {}  # token -> {buy_price, amount}
STATS = {"trades": 0, "wins": 0, "losses": 0, "pnl": 0}

TP_PERCENT = 20   # take profit %
SL_PERCENT = -10  # stop loss %

JUP_QUOTE = "https://quote-api.jup.ag/v6/quote"
JUP_SWAP = "https://quote-api.jup.ag/v6/swap"

# ================= PRICE =================
def get_token_price(token):
    try:
        params = {
            "inputMint": "So11111111111111111111111111111111111111112",
            "outputMint": token,
            "amount": 10000000,
        }
        res = requests.get(JUP_QUOTE, params=params, timeout=10).json()
        out = res["data"][0]["outAmount"]
        return float(out) / 1e6
    except:
        return None

# ================= SAFETY =================
def is_token_safe(token):
    try:
        # basic: must have route (liquidity proxy)
        params = {
            "inputMint": "So11111111111111111111111111111111111111112",
            "outputMint": token,
            "amount": 10000000,
        }
        res = requests.get(JUP_QUOTE, params=params, timeout=5).json()

        if "data" not in res or not res["data"]:
            print("❌ No liquidity route")
            return False

        return True
    except:
        return False

# ================= SWAP =================
def jupiter_swap(input_mint, output_mint, amount):
    try:
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": amount,
            "slippageBps": 500
        }

        quote = requests.get(JUP_QUOTE, params=params, timeout=10).json()
        if "data" not in quote or not quote["data"]:
            return None

        route = quote["data"][0]

        payload = {
            "quoteResponse": route,
            "userPublicKey": str(wallet.pubkey()),
            "wrapAndUnwrapSol": True
        }

        swap = requests.post(JUP_SWAP, json=payload, timeout=10).json()
        tx_b64 = swap.get("swapTransaction")

        if not tx_b64:
            return None

        tx = VersionedTransaction.from_bytes(base64.b64decode(tx_b64))
        tx.sign([wallet])

        sig = client.send_raw_transaction(bytes(tx)).value
        print(f"✅ TX: https://solscan.io/tx/{sig}")
        return sig

    except Exception as e:
        print("SWAP ERROR:", e)
        return None

# ================= BUY =================
def execute_buy(token):
    print(f"🚀 BUYING {token}")

    sig = jupiter_swap(
        "So11111111111111111111111111111111111111112",
        token,
        10000000
    )

    if not sig:
        return

    price = get_token_price(token)

    if price:
        POSITIONS[token] = {
            "buy_price": price,
            "amount": 10000000
        }
        print(f"📈 Bought at {price}")

# ================= SELL =================
def execute_sell(token):
    print(f"💰 SELLING {token}")

    sig = jupiter_swap(
        token,
        "So11111111111111111111111111111111111111112",
        POSITIONS[token]["amount"]
    )

    if not sig:
        return

    sell_price = get_token_price(token)
    buy_price = POSITIONS[token]["buy_price"]

    if sell_price:
        pnl = ((sell_price - buy_price) / buy_price) * 100
        STATS["trades"] += 1
        STATS["pnl"] += pnl

        if pnl > 0:
            STATS["wins"] += 1
        else:
            STATS["losses"] += 1

        print(f"📊 PnL: {round(pnl,2)}%")

    del POSITIONS[token]

# ================= POSITION MGMT =================
def manage_positions():
    for token in list(POSITIONS.keys()):
        price = get_token_price(token)
        if not price:
            continue

        buy_price = POSITIONS[token]["buy_price"]
        change = ((price - buy_price) / buy_price) * 100

        print(f"📊 {token} change: {round(change,2)}%")

        if change >= TP_PERCENT:
            print("🎯 TAKE PROFIT")
            execute_sell(token)

        elif change <= SL_PERCENT:
            print("🛑 STOP LOSS")
            execute_sell(token)

# ================= LOOP =================
def trading_loop():
    while True:
        try:
            if not BOT_RUNNING["value"]:
                time.sleep(5)
                continue

            manage_positions()

            for token in TOKENS:
                if token in POSITIONS:
                    continue

                print(f"Checking {token}")

                if not is_token_safe(token):
                    continue

                price = get_token_price(token)
                if not price:
                    continue

                execute_buy(token)

            time.sleep(10)

        except Exception as e:
            print("LOOP ERROR:", e)
            time.sleep(5)

# ================= TELEGRAM =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    BOT_RUNNING["value"] = True
    await update.message.reply_text("✅ Bot started")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    BOT_RUNNING["value"] = False
    await update.message.reply_text("⏸ Bot stopped")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = f"Running: {BOT_RUNNING['value']}\nTrades: {STATS['trades']}\nPnL: {round(STATS['pnl'],2)}%"
    await update.message.reply_text(msg)

# ================= MAIN =================
def main():
    print("🚀 Starting bot...")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("status", status))

    threading.Thread(target=trading_loop, daemon=True).start()

    print("🤖 Bot running...")
    app.run_polling(drop_pending_updates=True)

if name == "main":
    main()