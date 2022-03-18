from flask import Flask, request, jsonify
from flask_restful import Api
import json
import eth_account
import algosdk

app = Flask(__name__)
api = Api(app)
app.url_map.strict_slashes = False


@app.route('/verify', methods=['GET', 'POST'])
def verify():
    content = request.get_json(silent=True)

    # either eth or algo
    type = content['payload']['platform']
    payload = content['payload']
    pk = payload['pk']
    sk = content['sig']
    msg = json.dumps(payload)

    result = False

    # Check if signature is valid
    if type == 'Ethereum':
        # public key and secret key
        eth_pk = pk
        eth_sk = sk

        # msg and signed msg
        eth_encoded_msg = eth_account.messages.encode_defunct(text=msg)

        # verify
        if eth_account.Account.recover_message(eth_encoded_msg, signature=eth_sk) == eth_pk:
            result = True

    elif type == 'Algorand':
        # public key and secret key
        algo_pk = pk
        algo_sk = sk

        # verify
        if algosdk.util.verify_bytes(msg.encode('utf-8'), algo_sk, algo_pk):
            result = True

    return jsonify(result)


if __name__ == '__main__':
    app.run(port='5002')
    # app.run(debug=True, port=5003)
