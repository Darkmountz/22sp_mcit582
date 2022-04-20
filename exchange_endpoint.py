from typing import Dict, Any, Union

from flask import Flask, request, g
from flask_restful import Resource, Api
from sqlalchemy import create_engine
from flask import jsonify
import json
import eth_account
import algosdk
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import load_only
from datetime import datetime
import math
import sys
import traceback

# TODO: make sure you implement connect_to_algo, send_tokens_algo, and send_tokens_eth
from web3 import Web3

from send_tokens import connect_to_algo, connect_to_eth, send_tokens_algo, send_tokens_eth, indexer

import send_tokens

from models import Base, Order, TX, Log

engine = create_engine('sqlite:///orders.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

app = Flask(__name__)

""" Pre-defined methods (do not need to change) """


@app.before_request
def create_session():
    g.session = scoped_session(DBSession)


@app.teardown_appcontext
def shutdown_session(response_or_exc):
    sys.stdout.flush()
    g.session.commit()
    g.session.remove()


def connect_to_blockchains():
    try:
        # If g.acl has not been defined yet, then trying to query it fails
        acl_flag = False
        g.acl
    except AttributeError as ae:
        acl_flag = True

    try:
        if acl_flag or not g.acl.status():
            # Define Algorand client for the application
            g.acl = connect_to_algo()
    except Exception as e:
        print("Trying to connect to algorand client again")
        print(traceback.format_exc())
        g.acl = connect_to_algo()

    try:
        icl_flag = False
        g.icl
    except AttributeError as ae:
        icl_flag = True

    try:
        if icl_flag or not g.icl.health():
            # Define the index client
            g.icl = connect_to_algo(connection_type='indexer')
    except Exception as e:
        print("Trying to connect to algorand indexer client again")
        print(traceback.format_exc())
        g.icl = connect_to_algo(connection_type='indexer')

    try:
        w3_flag = False
        g.w3
    except AttributeError as ae:
        w3_flag = True

    try:
        if w3_flag or not g.w3.isConnected():
            g.w3 = connect_to_eth()
    except Exception as e:
        print("Trying to connect to web3 again")
        print(traceback.format_exc())
        g.w3 = connect_to_eth()


""" End of pre-defined methods """

""" Helper Methods (skeleton code for you to implement) """


def log_message(message_dict):
    msg = json.dumps(message_dict)
    g.session.add(Log(message=msg))
    g.session.commit()
    return


def get_algo_keys():
    # TODO: Generate or read (using the mnemonic secret)
    # the algorand public/private keys
    return algosdk.account.generate_account()


def get_eth_keys(filename="eth_mnemonic.txt"):
    w3 = Web3()

    # TODO: Generate or read (using the mnemonic secret)
    # the ethereum public/private keys
    w3.eth.account.enable_unaudited_hdwallet_features()
    account, mnemonic_secret = w3.eth.account.create_with_mnemonic()
    account = w3.eth.account.from_mnemonic(mnemonic_secret)
    return account._private_key, account._address


def fill_order(order, txes=[]):
    # TODO:
    # Match orders (same as Exchange Server II)
    # Validate the order has a payment to back it (make sure the counterparty also made a payment)
    # Make sure that you end up executing all resulting transactions!

    order.timestamp = datetime.now()

    g.session.add(order)
    g.session.commit()

    tx_item = {'receiver_pk': order.receiver_pk,
               'platform': order.sell_currency,
               'order_id': order.id,
               'tx_id': None}
    txes.append(tx_item)

    orders = g.session.query(Order).filter(Order.filled == None).all()

    for order in orders:
        if (order.buy_currency == order.sell_currency and
                order.sell_currency == order.buy_currency and
                float(order.sell_amount) / float(order.buy_amount) > float(order.buy_amount) / float(
                    order.sell_amount)):
            order.filled = datetime.now()
            order.counterparty_id = order.id
            order.counterparty = [order]
            g.session.commit()

            orders_get = {'buy_amount': order.buy_amount - order.sell_amount,
                          'sell_amount': order.sell_amount - order.buy_amount,
                          'buy_currency': order.buy_currency,
                          'sell_currency': order.sell_currency,
                          'creator_id': order.id,
                          'sender_pk': order.sender_pk,
                          'receiver_pk': order.receiver_pk}

            order_item: Order = Order(**{i: orders_get[i] for i in orders_get})
            fill_order(order_item, txes)


def execute_algo(acl, algo_sk, algo_txes):
    send_tokens_algo(acl, algo_sk, algo_txes)

    for tx in algo_txes:
        tx_dict: Dict[str, Union[str, Any]] = {
            'receiver_pk': tx['receiver_pk'],
            'order_id': tx['order_id'],
            'tx_id': tx['tx_id'],
            'platform': 'Algorand'}
        tx = TX(**{i: tx_dict[i] for i in tx_dict})
        g.session.add(tx)
        g.session.commit()


def execute_eth(w3, eth_sk, eth_txes):
    send_tokens_eth(w3, eth_sk, eth_txes)
    for tx in eth_txes:
        tx_dict = {'platform': 'Ethereum',
                   'receiver_pk': tx['receiver_pk'],
                   'order_id': tx['order_id'],
                   'tx_id': tx['tx_id']}
        tx = TX(**{i: tx_dict[i] for i in tx_dict})
        g.session.add(tx)
        g.session.commit()


def execute_txes(txes):
    if txes is None:
        return True
    if len(txes) == 0:
        return True
    print(f"Trying to execute {len(txes)} transactions")
    print(f"IDs = {[tx['order_id'] for tx in txes]}")
    eth_sk, eth_pk = get_eth_keys()
    algo_sk, algo_pk = get_algo_keys()

    if not all(tx['platform'] in ["Algorand", "Ethereum"] for tx in txes):
        print("Error: execute_txes got an invalid platform!")
        print(tx['platform'] for tx in txes)

    algo_txes = [tx for tx in txes if tx['platform'] == "Algorand"]
    eth_txes = [tx for tx in txes if tx['platform'] == "Ethereum"]

    # TODO:
    #       1. Send tokens on the Algorand and eth testnets, appropriately
    #          We've provided the send_tokens_algo and send_tokens_eth skeleton methods in send_tokens.py
    #       2. Add all transactions to the TX table

    # pass
    execute_algo(g.acl, algo_sk, algo_txes)

    execute_eth(g.w3, eth_sk, eth_txes)


""" End of Helper methods"""


@app.route('/address', methods=['POST'])
def address():
    if request.method == "POST":
        content = request.get_json(silent=True)
        if 'platform' not in content.keys():
            print(f"Error: no platform provided")
            return jsonify("Error: no platform provided")
        if not content['platform'] in ["Ethereum", "Algorand"]:
            print(f"Error: {content['platform']} is an invalid platform")
            return jsonify(f"Error: invalid platform provided: {content['platform']}")

        if content['platform'] == "Ethereum":
            # Your code here
            _, eth_pk = get_eth_keys()

            return jsonify(eth_pk)
        if content['platform'] == "Algorand":
            # Your code here
            _, algo_pk = get_algo_keys()

            return jsonify(algo_pk)


@app.route('/trade', methods=['POST'])
def trade():
    print("In trade", file=sys.stderr)
    connect_to_blockchains()
    get_keys()
    if request.method == "POST":
        content = request.get_json(silent=True)
        columns = ["buy_currency", "sell_currency", "buy_amount", "sell_amount", "platform", "tx_id", "receiver_pk"]
        fields = ["sig", "payload"]
        error = False
        for field in fields:
            if not field in content.keys():
                print(f"{field} not received by Trade")
                error = True
        if error:
            print(json.dumps(content))
            return jsonify(False)

        error = False
        for column in columns:
            if not column in content['payload'].keys():
                print(f"{column} not received by Trade")
                error = True
        if error:
            print(json.dumps(content))
            return jsonify(False)

        # Your code here

        # 1. Check the signature
        sig = content['sig']
        payload = content['payload']

        sender_pk = payload['sender_pk']

        is_sig = False

        if payload['platform'] == 'Algorand':
            is_sig = algosdk.util.verify_bytes(json.dumps(payload).encode('utf-8'), sig, sender_pk)

        elif payload['platform'] == 'Ethereum':
            is_sig = (eth_account.Account.recover_message(eth_account.messages.encode_defunct(text=json.dumps(payload)), signature=sig) == sender_pk)


        # 2. Add the order to the table
        if is_sig:
            payload['signature'] = sig
            order = Order(**{i: payload[i] for i in payload})

            if order.sell_currency == "Ethereum":
                tx = g.w3.eth.get_transaction(payload['tx_id'])
                if tx is None or tx["value"] != order.sell_amount:
                    return jsonify(False)
            elif order.sell_currency == "Algorand":
                tx = indexer.search_transaction(txid=payload['tx_id'])
                if tx is None or tx.amt != order.sell_amount:
                    return jsonify(False)

            txes = []
            fill_order(order, txes)

            execute_txes(txes)
            return jsonify(True)

        else:
            log_message(payload)
            return jsonify(False)

        return jsonify(True)


@app.route('/order_book')
def order_book():
    # Your code here
    # Note that you can access the database session using g.session
    all_orders = g.session.query(Order).all()
    order_list = []
    for order in all_orders:
        order_list.append({'sender_pk': order.sender_pk,
                           'receiver_pk': order.receiver_pk,
                           'buy_currency': order.buy_currency,
                           'sell_currency': order.sell_currency,
                           'buy_amount': order.buy_amount,
                           'sell_amount': order.sell_amount,
                           'signature': order.signature})
    result = {'data': order_list}
    return jsonify(result)


if __name__ == '__main__':
    app.run(port='5002')
