import time
import requests
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ===== CONFIG =====
TELEGRAM_TOKEN = "8394510966:AAGbpFgVYnbd8UlkN2u_BOvA-SI1QFk1xtA"
WALLET_PUBLIC_KEY = "HYpGuL2ohivog1mtaa4hgHLGHnH186AKqdUBzg4mTV44"

TOKENS = [
    "DezXAZ8z7PnrnRJjz3wXBoRgixCa6s7YaB1pPB263",
]

BUY_PERCENT = 0.1
STOP_LOSS = 0.2
TRAILING_STOP = 0.2

BOT_RUNNING = False

# ===== STATE =====
POSITIONS = {}

STATS = {
    "total_trades": 0,
    "wins": 0,
    "losses": 0,
    "total_pnl_percent": 0
}

# ===== BALANCE =====
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
        return data["result"]["value"] / 1e9
    except:
        return 0

# ===== PRICE =====
def get_token_price(token):
    try:
        url = "https://quote-api.jup.ag/v6/quote"

        params = {
            "inputMint": "So11111111111111111111111111111111111111112",
            "outputMint": token,
            "amount": 100000000
        }

        res = requests.get(url, params=params)
        data = res.json()

        if "data" not in data or len(data["data"]) == 0:
            return None

        return float(data["data"][0]["outAmount"]) / 1e9
    except:
        return None

# ===== RUG CHECK =====
def is_token_safe(token):
    try:
        url = "https://api.mainnet-beta.solana.com"
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getAccountInfo",
            "params": [token, {"encoding": "jsonParsed"}]
        }

        res = requests.post(url, json=payload)
        data = res.json()

        info = data["result"]["value"]["data"]["parsed"]["info"]

        if info.get("mintAuthority") is not None:
            return False

        if info.get("freezeAuthority") is not None:
            return False

        return True
    except:
        return False

# ===== BUY =====
def execute_buy(token):
    balance = get_sol_balance()
    amount = balance * BUY_PERCENT

    price = get_token_price(token)
    if price is None:
        return

    POSITIONS[token] = {
        "entry": price,
        "highest": price,
        "amount": amount
    }

    print(f"🚀 BUY {token} at {price}")

# ===== SELL =====
def execute_sell(token, reason):
    if token not in POSITIONS:
        return

    entry = POSITIONS[token]["entry"]
    price = get_token_price(token)

    if price is None:
        return

    pnl = (price - entry) / entry * 100

    STATS["total_trades"] += 1
    STATS["total_pnl_percent"] += pnl

    if pnl > 0:
        STATS["wins"] += 1
    else:
        STATS["losses"] += 1

    print(f"💰 SELL {token} | {reason} | {round(pnl,2)}%")

    del POSITIONS[token]

# ===== MANAGE POSITIONS =====
def manage_positions():
    for token in list(POSITIONS.keys()):
        price = get_token_price(token)
        if price is None:
            continue

        entry = POSITIONS[token]["entry"]
        highest = POSITIONS[token]["highest"]

        if price > highest:
            POSITIONS[token]["highest"] = price
            highest = price

        # STOP LOSS
        if price <= entry * (1 - STOP_LOSS):
            execute_sell(token, "STOP LOSS")
            continue

        # TRAILING STOP
        if price <= highest * (1 - TRAILING_STOP):
            execute_sell(token, "TRAILING STOP")

# ===== LOOP =====
def trading_loop():
    global BOT_RUNNING

    while True:
        try:
            if not BOT_RUNNING:
                time.sleep(2)
                continue

            manage_positions()

            for token in TOKENS:
                if token in POSITIONS:
                    continue

                price = get_token_price(token)
                if price is None:
                    continue

                if not is_token_safe(token):
                    continue

                execute_buy(token)

            time.sleep(5)

        except Exception as e:
            print("ERROR:", e)

# ===== TELEGRAM =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_RUNNING
    BOT_RUNNING = True
    await update.message.reply_text("🚀 Bot started")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_RUNNING
    BOT_RUNNING = False
    await update.message.reply_text("🛑 Bot stopped")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    balance = get_sol_balance()

    msg = f"📊 BOT STATUS\n\n"
    msg += f"💰 Wallet: {round(balance,4)} SOL\n\n"

    # OPEN POSITIONS
    if POSITIONS:
        msg += "📂 OPEN POSITIONS:\n"
        for token, data in POSITIONS.items():
            price = get_token_price(token)
            if price:
                pnl = (price - data["entry"]) / data["entry"] * 100
                msg += f"{token[:6]}... | {round(pnl,2)}%\n"
    else:
        msg += "📂 No open positions\n"

    # STATS
    msg += f"\n📈 PERFORMANCE\n"
    msg += f"Trades: {STATS['total_trades']}\n"
    msg += f"Wins: {STATS['wins']}\n"
    msg += f"Losses: {STATS['losses']}\n"

    if STATS["total_trades"] > 0:
        winrate = (STATS["wins"] / STATS["total_trades"]) * 100
        msg += f"Winrate: {round(winrate,2)}%\n"

    msg += f"Total PnL: {round(STATS['total_pnl_percent'],2)}%\n"

    await update.message.reply_text(msg)

# ===== MAIN =====
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("status", status))

    threading.Thread(target=trading_loop, daemon=True).start()

    print("🤖 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()