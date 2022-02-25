from web3 import Web3
from hexbytes import HexBytes

IP_ADDR = '18.188.235.196'
PORT = '8545'

w3 = Web3(Web3.HTTPProvider('http://' + IP_ADDR + ':' + PORT))

#     This line will mess with our autograders, but might be useful when debugging
#     print( "Connected to Ethereum node" )
if w3.isConnected():
#    print("Connected to Ethereum node")
else:
    print("Failed to connect to Ethereum node!")


def get_transaction(tx):
    transaction = w3.eth.get_transaction(tx)  # YOUR CODE HERE
    return transaction


# Return the gas price used by a particular transaction,
#   tx is the transaction
def get_gas_price(tx):
    transaction = get_transaction(tx)  # YOUR CODE HERE
    gas_price = transaction['gasPrice']
    return gas_price


def get_gas(tx):
    transaction = w3.eth.get_transaction_receipt(tx)  # YOUR CODE HERE
    gas = transaction['gasUsed']
    return gas


def get_transaction_cost(tx):
    transaction_cost = get_gas(tx) * get_gas_price(tx)  # YOUR CODE HERE
    return transaction_cost


def get_block_cost(block_num):
    block = w3.eth.get_block(block_num)  # YOUR CODE HERE
    transactions = block['transactions']
    block_cost = 0
    for transaction in transactions:
        block_cost += get_transaction_cost(transaction.hex())
    return block_cost


# Return the hash of the most expensive transaction
def get_most_expensive_transaction(block_num):  # YOUR CODE HERE
    block = w3.eth.get_block(block_num)
    transactions = block['transactions']

    most_cost = float('-inf')
    most_cost_transaction = None

    for transaction in transactions:
        current_transaction_cost = get_transaction_cost(transaction.hex())
        if current_transaction_cost > most_cost:
            most_cost = current_transaction_cost
            most_cost_transaction = transaction

    return most_cost_transaction


# print('q1:')
# transaction_hash = '0x0dda1142828634746a8e49e707fddebd487355a172bfa94b906a151062299578'
# print(get_transaction(transaction_hash))
# transaction_cost_Wei = get_transaction_cost(transaction_hash)
# print(transaction_cost_Wei)
# transaction_cost_ETH = transaction_cost_Wei / 1e18
# per_price_ETH = 1385.02
# print(transaction_cost_ETH)
# print('$ ' + str(round(per_price_ETH * transaction_cost_ETH, 2)))
#
# print()
# print('q2:')
# fee = 0.0
# for i in range(10237100, 10237110):
#     block_cost = get_block_cost(i)
#     fee += block_cost
#     print(str(i)+' '+str(block_cost))
#
# print()
# print(fee / (10237110 - 10237100))
# print(round(fee / 1e18 / (10237110 - 10237100), 2))

# print()
# print('q3:')
# mine_fee = get_block_cost(10237208) / 1e18 + 2
# per_price_ETH=248.26
# total_fee = per_price_ETH * mine_fee
# print(total_fee)
# transaction = get_most_expensive_transaction(10237208)
# transaction_hash = transaction.hex()
# print(transaction)
# print(transaction_hash)



