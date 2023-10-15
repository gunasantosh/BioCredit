from algosdk.v2client import algod
from algosdk import mnemonic
from beaker import client, sandbox
import contract
import os
from dotenv import load_dotenv
load_dotenv("../../.env")

API_KEY=os.getenv("API_KEY")

def create_application():
    algod_address = "https://testnet-algorand.api.purestake.io/ps2"
    algod_token = ""
    headers = {
        "X-API-Key": API_KEY,
    }
    sender=os.getenv('PUBLIC_KEY')
    mnemoni=os.getenv('MNEMONIC')
    print(sender)
    private_key = mnemonic.to_private_key(mnemoni)

    with open("artifacts/approval.teal", "r") as f:
        approval_program = f.read()

    with open("artifacts/clear.teal", "r") as f:
        clear_program = f.read()

    acct=sandbox.SandboxAccount(address=sender,private_key=private_key)
    algod_client = algod.AlgodClient(algod_token, algod_address, headers)
    app_client = client.ApplicationClient(
        algod_client, contract.app, signer=acct.signer
    )

    app_id, app_address, _ = app_client.create()
    print(f"Deployed Application ID: {app_id} Address: {app_address}")


create_application()