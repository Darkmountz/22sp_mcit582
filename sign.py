from fastecdsa.curve import secp256k1
from fastecdsa.keys import export_key, gen_keypair

from fastecdsa import curve, ecdsa, keys, point
from hashlib import sha256

def sign(m):
	#generate public key
	sk, pk = keys.gen_keypair(curve.secp256k1)
	# print(pk)

	#sign msg
	r, s = ecdsa.sign(m, sk, curve.secp256k1, sha256)

	valid = ecdsa.verify((r, s), m, pk, curve.secp256k1, sha256)
	# print(valid)

	assert isinstance( pk, point.Point )
	assert isinstance( r, int )
	assert isinstance( s, int )
	return( pk, [r,s] )



