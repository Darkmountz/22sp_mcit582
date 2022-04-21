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

from algosdk import mnemonic
import web3
from web3 import Web3, HTTPProvider

# TODO: make sure you implement connect_to_algo, send_tokens_algo, and send_tokens_eth
from send_tokens import connect_to_algo, connect_to_eth, send_tokens_algo, send_tokens_eth

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
            print("connect_to_algo()-1")
    except Exception as e:
        print("Trying to connect to algorand client again")
        print(traceback.format_exc())
        g.acl = connect_to_algo()
        print("connect_to_algo()-1-e")

    try:
        icl_flag = False
        g.icl
    except AttributeError as ae:
        icl_flag = True

    try:
        if icl_flag or not g.icl.health():
            # Define the index client
            g.icl = connect_to_algo(connection_type='indexer')
            print("connect_to_algo()-2")
    except Exception as e:
        print("Trying to connect to algorand indexer client again")
        print(traceback.format_exc())
        g.icl = connect_to_algo(connection_type='indexer')
        print("connect_to_algo()-2-e")

    try:
        w3_flag = False
        g.w3
    except AttributeError as ae:
        w3_flag = True

    try:
        if w3_flag or not g.w3.isConnected():
            g.w3 = connect_to_eth()
            print("connect_to_eth()")
    except Exception as e:
        print("Trying to connect to web3 again")
        print(traceback.format_exc())
        g.w3 = connect_to_eth()
        print("connect_to_eth()-e")


""" End of pre-defined methods """

""" Helper Methods (skeleton code for you to implement) """


def log_message(d):
    # Takes input dictionary d and writes it to the Log table
    return Log(message=json.dumps(d['payload']))


def get_algo_keys():
    # TODO: Generate or read (using the mnemonic secret)
    secret = "typical permit hurdle hat song detail cattle merge oxygen crowd arctic cargo smooth fly rice vacuum lounge yard frown predict west wife latin absent cup"
    return mnemonic.to_private_key(secret), mnemonic.to_public_key(secret)


def get_eth_keys(filename="eth_mnemonic.txt"):
    w3 = Web3()

    # TODO: Generate or read (using the mnemonic secret)
    w3.eth.account.enable_unaudited_hdwallet_features()
    secret = "double double teach potato comic hope problem enough stem upper behave brick"

    acc = w3.eth.account.from_mnemonic(secret)
    return acc._private_key, acc._address


def fill_order(order, txes=[]):
    cur_order = order

    order_list = []
    orders = g.session.query(Order).filter(Order.filled == None).all()

    for ord in orders:
        if ((ord.buy_currency == cur_order.sell_currency)
                and (ord.sell_currency == cur_order.buy_currency)
                and (ord.sell_amount / ord.buy_amount >= cur_order.buy_amount / cur_order.sell_amount)
                and (ord.counterparty_id == None)):
            order_list.append(ord)

    if len(order_list) > 0:
        ord_get = order_list[0]

        ord_get.filled = datetime.now()
        ord_get.counterparty_id = cur_order.id

        cur_order.filled = datetime.now()
        cur_order.counterparty_id = ord_get.id

        g.session.commit()

        compare_order(cur_order, ord_get, txes)


def compare_order(order_a, order_b, txes):
    if order_a.sell_amount < order_b.buy_amount:
        order_c = Order(sender_pk=order_b.sender_pk,
                        receiver_pk=order_b.receiver_pk,
                        buy_currency=order_b.buy_currency,
                        sell_currency=order_b.sell_currency,
                        buy_amount=order_b.buy_amount - order_a.sell_amount,
                        sell_amount=(order_b.sell_amount / order_b.buy_amount) * (
                                order_b.buy_amount - order_a.sell_amount),
                        creator_id=order_b.id,
                        tx_id=order_b.tx_id)
        g.session.add(order_c)
        g.session.commit()
        txes.append({'platform': order_a.buy_currency, 'receiver_pk': order_a.receiver_pk,
                     'order_id': order_a.id, 'amount': order_a.buy_amount})
        txes.append({'platform': order_b.buy_currency, 'receiver_pk': order_b.receiver_pk,
                     'order_id': order_b.id, 'amount': order_a.sell_amount})

        sub_order = g.session.query(Order).order_by(Order.id.desc()).first()
        fill_order(sub_order, txes)


    elif order_a.buy_amount > order_b.sell_amount:
        order_c = Order(sender_pk=order_a.sender_pk,
                        receiver_pk=order_a.receiver_pk,
                        buy_currency=order_a.buy_currency,
                        sell_currency=order_a.sell_currency,
                        buy_amount=order_a.buy_amount - order_b.sell_amount,
                        sell_amount=(order_a.buy_amount - order_b.sell_amount) / (
                                order_a.buy_amount / order_a.sell_amount),
                        creator_id=order_a.id,
                        tx_id=order_a.tx_id)
        g.session.add(order_c)
        g.session.commit()

        txes.append({'platform': order_a.buy_currency, 'receiver_pk': order_a.receiver_pk,
                     'order_id': order_a.id, 'amount': order_b.sell_amount})
        txes.append({'platform': order_b.buy_currency, 'receiver_pk': order_b.receiver_pk,
                     'order_id': order_b.id, 'amount': order_b.buy_amount})

        sub_order = g.session.query(Order).order_by(Order.id.desc()).first()
        fill_order(sub_order, txes)

    else:
        txes.append({'platform': order_a.buy_currency, 'receiver_pk': order_a.receiver_pk,
                     'order_id': order_a.id, 'amount': order_a.buy_amount})
        txes.append({'platform': order_b.buy_currency, 'receiver_pk': order_b.receiver_pk,
                     'order_id': order_b.id, 'amount': order_b.buy_amount})


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
    algo_id = send_tokens_algo(g.acl, algo_sk, algo_txes)
    modify(algo_id, algo_txes)

    eth_id = send_tokens_eth(g.w3, eth_sk.hex(), eth_txes)
    modify(eth_id, eth_txes)


def modify(tx_id, txes):
    for i, tx_dict in enumerate(txes):
        tx = TX(platform=tx_dict['platform'],
                receiver_pk=tx_dict['receiver_pk'],
                order_id=tx_dict['order_id'],
                tx_id=tx_id[i])
        g.session.add(tx)
        g.session.commit()


def get_list(order):
    return {
        field.name: getattr(order, field.name)
        for field in order.__table__.columns
    }


""" End of Helper methods"""


@app.route('/address', methods=['POST'])
def address():
    if request.method == "POST":
        print("--------- address ---------")
        content = request.get_json(silent=True)

        # check whether the input content contains a 'platform'
        if 'platform' not in content.keys():
            print(f"Error: no platform provided")
            return jsonify("Error: no platform provided")

        # check whether the input platform is "Ethereum" or "Algorand"
        if not content['platform'] in ["Ethereum", "Algorand"]:
            print(f"Error: {content['platform']} is an invalid platform")
            return jsonify(f"Error: invalid platform provided: {content['platform']}")

        if content['platform'] == "Ethereum":
            return jsonify(get_eth_keys()[1])

        if content['platform'] == "Algorand":
            return jsonify(get_algo_keys()[1])


@app.route('/trade', methods=['POST'])
def trade():
    print("In trade", file=sys.stderr)
    connect_to_blockchains()
    get_eth_keys()
    get_algo_keys()
    if request.method == "POST":
        print("--------- trade ---------")
        content = request.get_json(silent=True)
        columns = ["buy_currency", "sell_currency", "buy_amount", "sell_amount", "platform", "tx_id", "receiver_pk"]
        fields = ["sig", "payload"]

        # Orders should have two fields “payload” and "sig".
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

        sig = content['sig']
        payload = content['payload']
        platform = payload['platform']

        platforms = ["Algorand", "Ethereum"]
        if not platform in platforms:
            return jsonify(False)

        verified = False
        sender_pk = payload['sender_pk']
        platform = payload['platform']
        msg = json.dumps(payload)

        if platform == "Algorand":
            if algosdk.util.verify_bytes(msg.encode('utf-8'), sig, sender_pk):
                verified = True

        elif platform == "Ethereum":
            eth_encoded_msg = eth_account.messages.encode_defunct(text=msg)
            if eth_account.Account.recover_message(eth_encoded_msg, signature=sig) == sender_pk:
                verified = True

        if verified is False:
            log_message(msg)
            return jsonify(False)

        else:
            ord = Order(sender_pk=payload['sender_pk'],
                        receiver_pk=payload['receiver_pk'],
                        buy_currency=payload['buy_currency'],
                        sell_currency=payload['sell_currency'],
                        buy_amount=payload['buy_amount'],
                        sell_amount=payload['sell_amount'],
                        tx_id=payload['tx_id'],
                        signature=sig)

            g.session.add(ord)

            txes = []
            current_order = g.session.query(Order).order_by(Order.id.desc()).first()
            fill_order(current_order, txes)

            execute_txes(txes)
            return jsonify(True)


@app.route('/order_book')
def order_book():
    orders = [
        get_list(order)
        for order in g.session.query(Order).all()
    ]

    return jsonify({
        'data': orders
    })


if __name__ == '__main__':
    app.run(port='5002')
