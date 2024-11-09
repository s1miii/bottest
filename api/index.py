from flask import Flask, jsonify, render_template
from web3 import Web3
import os

app = Flask(__name__, template_folder="../templates", static_folder="../static")

# Configuration - Retrieve from environment variables
TARGET_ADDRESS = os.getenv("TARGET_ADDRESS", "0xc204af95b0307162118f7bc36a91c9717490ab69")
RPC_URL = os.getenv("RPC_URL", "https://base.drpc.org")  # Replace as needed

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(RPC_URL))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/check', methods=['GET'])
def check_for_deployments():
    latest_block = w3.eth.block_number
    block = w3.eth.get_block(latest_block, full_transactions=True)
    deployments = []

    for tx in block.transactions:
        if tx['from'].lower() == TARGET_ADDRESS.lower() and tx['to'] is None:
            receipt = w3.eth.get_transaction_receipt(tx['hash'])
            contract_address = receipt.contractAddress

            deployment_details = {
                "transaction_hash": tx['hash'].hex(),
                "contract_address": contract_address,
                "block_number": latest_block,
                "transaction_link": f"https://basescan.org/tx/{tx['hash'].hex()}",
                "contract_link": f"https://basescan.org/address/{contract_address}"
            }
            deployments.append(deployment_details)
    
    if deployments:
        return jsonify({
            "status": "New deployment(s) detected",
            "deployments": deployments
        }), 200
    else:
        return jsonify({
            "status": "No new deployments found in the latest block"
        }), 200

@app.route('/status', methods=['GET'])
def status():
    return jsonify({"status": "Bot is ready to check for deployments"}), 200
