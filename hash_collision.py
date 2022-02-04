import hashlib
import os
import sys

def hash_collision(k):
    if not isinstance(k,int):
        print( "hash_collision expects an integer" )
        return( b'\x00',b'\x00' )
    if k < 0:
        print( "Specify a positive number of bits" )
        return( b'\x00',b'\x00' )
   
    #Collision finding code goes here
    code_dict = {}
    for i in range(sys.maxsize):
        byte_str = os.urandom(k)
        final_k_of_sha_code = bin(int(hashlib.sha256(byte_str).hexdigest(), 16))[-k:]

        if final_k_of_sha_code in code_dict:
            return byte_str, code_dict[final_k_of_sha_code]
        else:
            code_dict[final_k_of_sha_code] = byte_str





