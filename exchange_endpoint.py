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
import sys

from models import Base, Order, Log
engine = create_engine('sqlite:///orders.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

app = Flask(__name__)

@app.before_request
def create_session():
    g.session = scoped_session(DBSession)

@app.teardown_appcontext
def shutdown_session(response_or_exc):
    sys.stdout.flush()
    g.session.commit()
    g.session.remove()


""" Suggested helper methods """


def fill_order(order):
    session = g.session

    # insert the order into the database
    cur_order = order

    # insert the order into the database
    session.add(cur_order)

    # check if there are any existing orders that match
    existing_orders = session.query(Order).filter(Order.filled == cur_order.filled,
                                                  Order.buy_currency == cur_order.sell_currency,
                                                  Order.sell_currency == cur_order.buy_currency,
                                                  (Order.sell_amount / Order.buy_amount) >= (
                                                              cur_order.buy_amount / cur_order.sell_amount)).first()

    # if existing_orders is null:
    #     return

    if existing_orders:
        # set the filled field to be the current timestamp on both orders
        existing_orders.filled = datetime.now()
        cur_order.filled = datetime.now()

        # set counterparty_id to be the id of the other order
        existing_orders.counterparty_id = cur_order.id
        cur_order.counterparty_id = existing_orders.id

        # if one of the orders is not completely filled
        if existing_orders.sell_amount != cur_order.buy_amount:
            remain = cur_order.buy_amount - existing_orders.sell_amount

            if remain > 0:
                convert = remain / (cur_order.buy_amount / cur_order.sell_amount)
                remaining_balance_order = Order(buy_currency=cur_order.buy_currency,
                                                sell_currency=cur_order.sell_currency,
                                                sender_pk=cur_order.sender_pk,
                                                receiver_pk=cur_order.receiver_pk,
                                                buy_amount=remain,
                                                sell_amount=convert,
                                                creator_id=cur_order.id)
            else:
                convert = abs(remain) / (existing_orders.sell_amount / existing_orders.buy_amount)
                remaining_balance_order = Order(buy_currency=existing_orders.buy_currency,
                                                sell_currency=existing_orders.sell_currency,
                                                sender_pk=existing_orders.sender_pk,
                                                receiver_pk=existing_orders.receiver_pk,
                                                buy_amount=convert,
                                                sell_amount=abs(remain),
                                                creator_id=existing_orders.id)
            session.add(remaining_balance_order)
        session.commit()
        session.close()

def log_message(d):
    # Takes input dictionary d and writes it to the Log table
    return Log(message=json.dumps(d['payload']))


def verify(content, platform):
    pk = content['payload']['sender_pk']
    sig = content["sig"]
    payload = json.dumps(content['payload'])

    is_valid = False

    if platform == 'Ethereum':
        is_valid = (pk == eth_account.Account.recover_message(eth_account.messages.encode_defunct(text=payload),
                                                              signature=sig))
    elif platform == 'Algorand':
        is_valid = algosdk.util.verify_bytes(payload.encode('utf-8'), sig, pk)

    return is_valid


def commit(content, is_valid):
    if is_valid:
        payload = content['payload']
        order = Order(
            signature=content['sig'],
            sender_pk=payload['sender_pk'],
            receiver_pk=payload['receiver_pk'],
            buy_currency=payload['buy_currency'],
            sell_currency=payload['sell_currency'],
            buy_amount=payload['buy_amount'],
            sell_amount=payload['sell_amount']
        )
        fill_order(order)
    else:
        log_message(content)
    return is_valid


"""
---------------- Endpoints ----------------
"""


@app.route('/trade', methods=['POST'])
def trade():
    if request.method == "POST":
        content = request.get_json(silent=True)
        print(f"content = {json.dumps(content)}")
        columns = ["sender_pk", "receiver_pk", "buy_currency", "sell_currency", "buy_amount", "sell_amount", "platform"]
        fields = ["sig", "payload"]
        error = False
        for field in fields:
            if not field in content.keys():
                print(f"{field} not received by Trade")
                print(json.dumps(content))
                log_message(content)
                return jsonify(False)

        error = False
        for column in columns:
            if not column in content['payload'].keys():
                print(f"{column} not received by Trade")
                error = True
        if error:
            print(json.dumps(content))
            log_message(content)
            return jsonify(False)

        # Your code here
        # Note that you can access the database session using g.session
        return jsonify(commit(content, verify(content, content['payload']['platform'])))


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
