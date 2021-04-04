import hashlib
import time
from hashlib import sha512


class Transaction(object):
    def __init__(self, *args, **kwargs):
        self.recipient = kwargs.get('recipient')
        self.initiator = kwargs.get('initiator')
        self.amount = float(kwargs.get('amount', 0))
        self.timestamp = kwargs.get('timestamp', int(time.time()))
        self.public_key = kwargs.get('public_key')
        self.n = kwargs.get('n')
        self.id = kwargs.get('id')
        self.signature = kwargs.get('signature')

    def from_string(self, line):
        transaction = line.split(' ')
        self.recipient = transaction[0]
        self.initiator = transaction[1]
        self.amount = float(transaction[2])
        self.timestamp = int(transaction[3])
        self.id = transaction[4]
        self.public_key = int(transaction[5])
        self.n = int(transaction[6])
        self.signature = int(transaction[7])
        return self

    def verify_signature(self):
        transaction = str(self).split(' ')[0:-1]
        transaction_string = " ".join(transaction)
        msg = bytes(transaction_string, encoding='utf-8')
        sha512hash = int.from_bytes(sha512(msg).digest(), byteorder='big')
        hash_from_signature = pow(self.signature, self.public_key, self.n)
        if not sha512hash == hash_from_signature:
            return False
        else:
            return True

    def transaction_id(self):
        self.id = str(hashlib.sha512("{}{}{}{}{}{}{}".format(self.recipient, self.initiator,
                                                             self.amount, self.timestamp,
                                                             self.public_key, self.n, self.signature).encode(
            "utf-8")).hexdigest())

    def __str__(self):
        return "{} {} {} {} {} {} {} {}".format(
            self.recipient,
            self.initiator,
            float(self.amount),
            self.timestamp,
            self.id,
            self.public_key,
            self.n,
            self.signature
        )
