
def encrypt(key,plaintext):
    ciphertext=""
    #YOUR CODE HERE
    for ch in plaintext:
        enCh = ord(ch) + (key % 26)
        if enCh > ord('Z'):
            enCh = ord('A') + (enCh - ord('Z') - 1)
        elif enCh < ord('A'):
            enCh = ord('Z') + (ord('A') - enCh - 1)
        ciphertext += chr(enCh)
    return ciphertext

def decrypt(key,ciphertext):
    plaintext=""
    #YOUR CODE HERE
    for ch in ciphertext:
        deCh = ord(ch) - (key % 26)
        if deCh < ord('A'):
            deCh = ord('Z') - (ord('A') - deCh - 1)
        plaintext += chr(deCh)
    return plaintext

