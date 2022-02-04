import random

from params import p
from params import g


def keygen():
    q = int((p - 1) / 2)
    sk = random.randint(1, q)
    pk = pow(g, sk, p)
    return pk, sk


def encrypt(pk, m):
#     print(m)
    q = int((p - 1) / 2)
    r = random.randint(1, q)
    c1 = pow(g, r, p)
    c2 = ((m % p) * pow(pk, r, p)) % p
    return [c1, c2]


def decrypt(sk, c):
    c1, c2 = c
#     print(c1)
    m = ((c2 % p) * pow(c1, -1 * sk, p)) % p
    return m


