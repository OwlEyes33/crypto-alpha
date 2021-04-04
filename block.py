import json
import logging
from hashlib import sha512
import time

from transaction import Transaction

logging.basicConfig(level=logging.DEBUG)


class Block(object):
    def __init__(self, *args, **kwargs):
        self.sha512hash = kwargs.get('sha512hash')
        self.data = kwargs.get('data')
        self.magic_number = kwargs.get('magic_number')
        self.wallets = kwargs.get('tests/wallets')
        self.transactions = list()
        self.blockchain_snapshot = str(kwargs.get('blockchain_snapshot'))

    def get_associated_wallets(self):
        transactions = self.data.split('\n')[0:-1]
        wallets = dict()
        for transaction in transactions:
            transaction = transaction.strip('\n')
            transaction = transaction.split(' ')
            wallet_from = transaction[1]
            wallets[wallet_from] = 0.0
        return wallets

    def get_block_transactions(self):
        transactions = self.data.split('\n')[0:-1]
        for transaction in transactions:
            t = Transaction()
            transaction = transaction.strip()
            transaction = t.from_string(transaction)
            self.transactions.append(transaction)

    # Difficulty increases by + 1 every 3 years
    # Todo: Change this when it goes live
    @staticmethod
    def get_current_difficulty(timestamp):
        return int(((1/93312000) * timestamp) - (138191839/10368000))

    def check_proof_of_work(self):
        now = int(time.time())
        difficulty = Block.get_current_difficulty(now)
        if self.sha512hash[-1 * difficulty:] == "0"*difficulty:
            return True
        else:
            return False

    def generate_hash(self):
        sha512hash = sha512(str(self).encode("utf-8")).hexdigest()
        return sha512hash

    def to_dict(self):
        return {'sha512hash': self.sha512hash,
                'data': self.data,
                'magic_number': self.magic_number,
                'blockchain_snapshot': self.blockchain_snapshot}

    def to_json(self):
        return json.dumps({'sha512hash': self.sha512hash,
                           'data': self.data,
                           'magic_number': self.magic_number,
                           'blockchain_snapshot': self.blockchain_snapshot})

    def __str__(self):

        return "{}{}{}".format(
            self.data,
            str(self.blockchain_snapshot),
            self.magic_number,
        )

    @staticmethod
    def block_to_serialized(block):
        assert isinstance(block, dict)
        transactions_string = str()
        for _, sha512hash in enumerate(block):
            transaction = block[sha512hash]
            transactions_string = transactions_string + str(transaction) + "\n"
        return transactions_string

    def deserialize(self):
        transactions = self.data.split("\n")
        block = dict()
        for transaction in transactions:
            elements = transaction.split(" ")
            if len(elements) > 1:
                transaction = Transaction(
                    recipient=elements[0],
                    initiator=elements[1],
                    amount=elements[2],
                    timestamp=elements[3],
                    id=elements[4],
                    public_key=int(elements[5]),
                    n=int(elements[6]),
                    signature=int(elements[7]),
                )
                block[elements[4]] = transaction
        return block