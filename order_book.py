from sqlalchemy import create_engine, null
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from models import Base, Order

engine = create_engine('sqlite:///orders.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


def process_order(order):
    # Your code here
    # create a new order object and fill the fields
    cur_order = Order(buy_currency=order['buy_currency'],
                      sell_currency=order['sell_currency'],
                      buy_amount=order['buy_amount'],
                      sell_amount=order['sell_amount'],
                      sender_pk=order['sender_pk'],
                      receiver_pk=order['receiver_pk'])

    # insert the order into the database
    session.add(cur_order)
    session.commit();

    # check if there are any existing orders that match
    existing_orders = session.query(Order).filter(Order.filled == None,
                                                  Order.buy_currency == cur_order.sell_currency,
                                                  Order.sell_currency == cur_order.buy_currency,
                                                  Order.sell_amount / Order.buy_amount >= cur_order.buy_amount / cur_order.sell_amount).first()

    # if existing_orders is null:
    #     return

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
