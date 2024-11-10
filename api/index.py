from flask import Flask, jsonify
from web3 import Web3
import os
import telebot
import threading
import time

# Initialize Flask app and Telegram bot
app = Flask(__name__)

# Load environment variables
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_CHAT_ID = os.getenv("CHANNEL_CHAT_ID", "-1002461638660")
TARGET_ADDRESS = os.getenv("TARGET_ADDRESS", "0xc204af95b0307162118f7bc36a91c9717490ab69")
RPC_URL = os.getenv("RPC_URL", "https://base-mainnet.g.alchemy.com/v2/a6pyXUFXfmPbkwqJ9cCvfyjKL4LjK32u")

# Check if required environment variables are set
if not bot_token:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set or is empty.")
if not CHANNEL_CHAT_ID:
    raise ValueError("CHANNEL_CHAT_ID environment variable is not set or is empty.")
if not RPC_URL:
    raise ValueError("RPC_URL environment variable is not set or is empty.")

# Initialize Web3 and Telegram bot
w3 = Web3(Web3.HTTPProvider(RPC_URL))
bot = telebot.TeleBot(bot_token)

# Check blockchain connection by attempting to fetch the latest block number
try:
    latest_block = w3.eth.block_number
    print("Connected to the blockchain. Latest block:", latest_block)
except Exception as e:
    raise ConnectionError(f"Failed to connect to the blockchain via RPC URL: {e}")

print("Connected to the blockchain. Monitoring for deployments...")

# Function to send a message to the Telegram channel
def send_telegram_message(message):
    try:
        bot.send_message(CHANNEL_CHAT_ID, message, parse_mode="Markdown")
        print("Message sent to Telegram channel.")
    except Exception as e:
        print(f"Failed to send message: {e}")

# Function to monitor new token deployments
def monitor_for_deployments():
    latest_block = w3.eth.block_number
    print("Monitoring for new deployments...")

    while True:
        try:
            # Check the latest block
            new_block = w3.eth.block_number
            if new_block > latest_block:
                # Fetch transactions from the latest block
                block = w3.eth.get_block(new_block, full_transactions=True)
                
                for tx in block.transactions:
                    # Check if transaction is from the target address and creates a contract
                    if tx['from'].lower() == TARGET_ADDRESS.lower() and tx['to'] is None:
                        # Get contract address from the transaction receipt
                        receipt = w3.eth.get_transaction_receipt(tx['hash'])
                        contract_address = receipt.contractAddress

                        # Generate the direct buy link
                        buy_link = f"https://t.me/SigmaTrading3_bot?start=buy_{contract_address}"
                        
                        # Prepare and send deployment message to Telegram
                        deployment_message = (
                            f"🚀 New Token Deployment Detected!\n\n"
                            f"🔹 From Address: {TARGET_ADDRESS}\n"
                            f"🔹 Transaction Hash: {tx['hash'].hex()}\n"
                            f"🔹 Contract Address: {contract_address}\n"
                            f"🔹 Block Number: {new_block}\n"
                            f"Check the transaction: https://basescan.org/tx/{tx['hash'].hex()}\n"
                            f"Check the contract: https://basescan.org/address/{contract_address}\n"
                            f"💰 [Direct Buy Link with @SigmaTrading3_bot]({buy_link})"
                        )
                        send_telegram_message(deployment_message)

                # Update the latest block
                latest_block = new_block

            # Wait before checking the next block
            time.sleep(30)

        except Exception as e:
            print(f"Error in monitoring: {e}")
            time.sleep(30)

# Route to start monitoring (optional endpoint)
@app.route('/start_monitoring', methods=['GET'])
def start_monitoring():
    # Start the monitoring in the background (as an example)
    monitor_thread = threading.Thread(target=monitor_for_deployments)
    monitor_thread.start()
    return jsonify({"status": "Monitoring started"}), 200

# Status endpoint
@app.route('/status', methods=['GET'])
def status():
    return jsonify({"status": "Bot is running and ready to monitor"}), 200

# Main entry point for the Flask app
if __name__ == "__main__":
    # Start the monitoring thread
    monitor_thread = threading.Thread(target=monitor_for_deployments)
    monitor_thread.start()

    # Start the Flask server
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
