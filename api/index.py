from flask import Flask, jsonify
from web3 import Web3
import os
import telebot
import time

# Initialize Flask app and Telegram bot
app = Flask(__name__)
bot_token = os.getenv("7377605568:AAGNNDS1uRGr003MIV1gneMqcZXWdyBTz1s")
bot = telebot.TeleBot(bot_token)

# Set your channel chat ID here (e.g., -1001234567890 for private channels)
CHANNEL_CHAT_ID = os.getenv("CHANNEL_CHAT_ID", "-1002461638660")

# Blockchain configuration
TARGET_ADDRESS = os.getenv("TARGET_ADDRESS", "0xc204af95b0307162118f7bc36a91c9717490ab69")
RPC_URL = os.getenv("RPC_URL", "https://base.drpc.org")
w3 = Web3(Web3.HTTPProvider(RPC_URL))

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
                        
                        # Prepare and send deployment message to Telegram
                        deployment_message = (
                            f"🚀 New Token Deployment Detected!\n\n"
                            f"🔹 From Address: {TARGET_ADDRESS}\n"
                            f"🔹 Transaction Hash: {tx['hash'].hex()}\n"
                            f"🔹 Contract Address: {contract_address}\n"
                            f"🔹 Block Number: {new_block}\n"
                            f"Check the transaction: https://basescan.org/tx/{tx['hash'].hex()}\n"
                            f"Check the contract: https://basescan.org/address/{contract_address}"
                        )
                        send_telegram_message(deployment_message)

                # Update the latest block
                latest_block = new_block

            # Wait before checking the next block
            time.sleep(10)

        except Exception as e:
            print(f"Error in monitoring: {e}")
            time.sleep(10)

# Route to start monitoring (optional endpoint)
@app.route('/start_monitoring', methods=['GET'])
def start_monitoring():
    # Start the monitoring in the background (as an example)
    import threading
    monitor_thread = threading.Thread(target=monitor_for_deployments)
    monitor_thread.start()
    return jsonify({"status": "Monitoring started"}), 200

# Status endpoint
@app.route('/status', methods=['GET'])
def status():
    return jsonify({"status": "Bot is running and ready to monitor"}), 200

# Main entry point for the Flask app
if __name__ == "__main__":
    # Start monitoring on app start
    monitor_for_deployments()
    # Uncomment the following line if you only want to run Flask server without monitoring
    # app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
