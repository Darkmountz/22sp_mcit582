#!/usr/bin/python3

from algosdk.v2client import algod
from algosdk import mnemonic
from algosdk import transaction
from algosdk import account, encoding

# Connect to Algorand node maintained by PureStake
algod_address = "https://testnet-algorand.api.purestake.io/ps2"
algod_token = "B3SU4KcVKi94Jap2VXkK83xx38bsv95K5UZm2lab"
# algod_token = 'IwMysN3FSZ8zGVaQnoUIJ9RXolbQ5nRY62JRqF2H'
headers = {
    "X-API-Key": algod_token,
}

acl = algod.AlgodClient(algod_token, algod_address, headers)
min_balance = 100000  # https://developer.algorand.org/docs/features/accounts/#minimum-balance
sk = 'b6fFPMn0N870P+r77X6PUc7jddJwsT/ZPt/oI2zn1C2S/kt5NodRSB+SHUuAhvRZqNiF5lkIpvqszR3vjls5Cw=='
address = 'SL7EW6JWQ5IUQH4SDVFYBBXULGUNRBPGLEEKN6VMZUO67DS3HEF7UA3GZI'


def send_tokens(receiver_pk, tx_amount):
    params = acl.suggested_params()
    gen_hash = params.gh
    first_valid_round = params.first
    tx_fee = params.min_fee
    last_valid_round = params.last

    # Your code here
    # https://py-algorand-sdk.readthedocs.io/en/latest/algosdk/transaction.html
    txn = transaction.PaymentTxn(address, tx_fee, first_valid_round, last_valid_round, gen_hash, receiver_pk,
                                 tx_amount)

    # sign with secret key
    sign_txn = txn.sign(sk)

    # send
    txid = acl.send_transaction(sign_txn)

    return address, txid


# Function from Algorand Inc.
def wait_for_confirmation(client, txid):
    """
    Utility function to wait until the transaction is
    confirmed before proceeding.
    """
    last_round = client.status().get('last-round')
    txinfo = client.pending_transaction_info(txid)
    while not (txinfo.get('confirmed-round') and txinfo.get('confirmed-round') > 0):
        print("Waiting for confirmation")
        last_round += 1
        client.status_after_block(last_round)
        txinfo = client.pending_transaction_info(txid)
    print("Transaction {} confirmed in round {}.".format(txid, txinfo.get('confirmed-round')))
    return txinfo


def generate_account_with_info():
    sk, address = account.generate_account()
    return sk, address


# if __name__ == '__main__':
#     # sk, address = generate_account_with_info()
#     # print(sk)
#     # print(address)
#
#     sk = 'b6fFPMn0N870P+r77X6PUc7jddJwsT/ZPt/oI2zn1C2S/kt5NodRSB+SHUuAhvRZqNiF5lkIpvqszR3vjls5Cw=='
#     address = 'SL7EW6JWQ5IUQH4SDVFYBBXULGUNRBPGLEEKN6VMZUO67DS3HEF7UA3GZI'
#
#     send_amount = 1
#
#     send_tokens('FHACVHUPERBRXBYP72OXDXLXO5OHJBDHMEHLE2GWLL4DVJ5QZPSX6VYUBM', send_amount)
