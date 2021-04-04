import logging
import sys
import time
from hashlib import sha512
from random import randint

from Crypto.PublicKey import RSA

from transaction import Transaction

logging.basicConfig(level=logging.DEBUG)


class Wallet(object):
    def __init__(self, *_, **kwargs):
        self.public_key = kwargs.get('public_key')
        self.private_key = kwargs.get('private_key')
        self.n = kwargs.get('seed')

    def generate_id(self):
        return sha512(str(self.public_key).encode('utf-8')).hexdigest()

    def send_transaction(self, amount, recipient):
        transaction = Transaction(
            recipient=recipient,
            initiator=self.generate_id(),
            amount=float(amount),
            timestamp=int(time.time()),
            public_key=self.public_key,
            n=self.n
        )
        transaction, signature = self.sign_transaction(transaction)
        return transaction, signature

    def sign_transaction(self, transaction):
        transaction.transaction_id()
        transaction_string = str(transaction).split(" ")[0:-1]
        transaction_string = " ".join(transaction_string)
        msg = bytes(transaction_string, encoding='utf-8')
        sha512hash = int.from_bytes(sha512(msg).digest(), byteorder='big')
        signature = pow(sha512hash, self.private_key, self.n)
        transaction.signature = signature
        return transaction, signature

    def random_e(self):
        e = randint(65537, sys.maxsize)
        if e % 2 == 0:
            e = e + 1
        return e

    def generate_keypair(self):
        keys = RSA.generate(bits=2048, e=self.random_e())
        self.n = keys.n
        self.public_key = keys.e
        self.private_key = keys.d

    def write_keys(self):
        with open('private_key.asc', 'w') as f:
            f.write(str(self.private_key))

        with open('public_key.asc', 'w') as f:
            f.write(str(self.public_key))

        with open('seed', 'w') as f:
            f.write(str(self.n))
