'''
 Author: Sirvan Almasi @ Imperial College London
 August 2018
 Dissertation Project
'''

import sys, hmac, hashlib
sys.setrecursionlimit(1000000)


class almasFFS:
    def __init__(self,I,j,n):
        self.jIndices = j
        self.idRaw = I
        self.n = n
        self.publicKeys = []

    # return (g, x, y) a*x + b*y = gcd(x, y)
    def __egcd(self, a, b):
        if a == 0:
            return (b, 0, 1)
        else:
            g, x, y = self.__egcd(b % a, a)
            return (g, y - (b // a) * x, x)

    '''
    GET PUB KEYS
        from the j indices, which we generated above, get the...
        respected pub key
    '''
    def getPubKey(self, j):
        key_bytes= bytes(str(j) , 'latin-1')
        data_bytes = bytes(self.idRaw, 'latin-1')
        digest_maker = hmac.new(key_bytes, data_bytes, hashlib.sha256)
        digest = digest_maker.hexdigest()
        pubHatInt = int(digest, 16) % self.n
        pubKey = self.__egcd(pubHatInt, self.n)[1] % self.n
        return pubKey

    def getPubKeys(self):
        for j in self.jIndices:
            self.publicKeys.append(self.getPubKey(j))
        return self.publicKeys