import hashlib
import os
import random

def hash_preimage(target_string):
    if not all([x in '01' for x in target_string]):
        print("Input should be a string of bits")
        return

    while True:
        nonce = os.urandom(len(target_string))
        sha_code_of_nonce = bin(int(hashlib.sha256(nonce).hexdigest(), 16))
        trailing_of_code = sha_code_of_nonce[-len(nonce):]

        if trailing_of_code == target_string:
            return nonce



