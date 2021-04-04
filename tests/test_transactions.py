import logging
import time
import unittest
from hashlib import sha512
from random import randint
from uuid import uuid4

from Crypto.PublicKey import RSA
from redis import Redis

from miner import Miner
from tests.helpers import create_batch_fake_transactions
from transaction import Transaction
from wallet import Wallet

logging.basicConfig(level=logging.DEBUG)


class TestTransactions(unittest.TestCase):
    def setUp(self) -> None:
        self.wallet = Wallet()
        self.wallet.id = str(uuid4())
        self.recipient = str(uuid4())
        self.initiator = str(uuid4())
        self.amount = randint(100, 500)
        self.timestamp = int(time.time())
        self.host = 'http://localhost:8000'
        self.redis_cli = Redis()

    def tearDown(self) -> None:
        self.redis_cli.flushall()

    def test_sync_transactions(self):
        transactions = create_batch_fake_transactions()
        self.miner = Miner(transactions=transactions)
        self.miner.sync_to_redis()
        for _, key in enumerate(self.miner.transactions):
            self.assertEqual(self.miner.transactions[key], self.redis_cli[key])
        self.assertTrue(len(list(self.miner.transactions.keys())) == 0)

        transactions = create_batch_fake_transactions()
        self.miner = Miner(transactions=transactions)
        self.miner.sync_to_redis()
        for _, key in enumerate(self.miner.transactions):
            self.assertEqual(self.miner.transactions[key], self.redis_cli[key])
        self.assertTrue(len(list(self.miner.transactions.keys())) == 0)

    def test_verify_RSA_signature(self):
        key_pair = RSA.generate(bits=2048)
        msg = bytes(str('A message for signing'), encoding='utf-8')
        rsa_hash = int.from_bytes(sha512(msg).digest(), byteorder='big')
        signature = pow(rsa_hash, key_pair.d, key_pair.n)
        msg = bytes(str('A message for signing'), encoding='utf-8')
        rsa_hash = int.from_bytes(sha512(msg).digest(), byteorder='big')
        hash_from_signature = pow(signature, key_pair.e, key_pair.n)
        self.assertTrue(rsa_hash == hash_from_signature)

    def test_verify_signature(self):
        wallet = Wallet()
        wallet.generate_keypair()
        transaction = Transaction(
            recipient='foobar',
            initiator='test-1',
            amount=float(500),
            public_key=wallet.public_key,
            n=wallet.n
        )
        transaction, signature = wallet.sign_transaction(transaction)
        transaction_string = str(transaction)
        t = Transaction()
        transaction = t.from_string(transaction_string)
        self.assertTrue(transaction.signature)
        self.assertIsInstance(transaction.signature, int)
        self.assertTrue(transaction.verify_signature())

        wallet = Wallet()
        wallet.generate_keypair()
        transaction = Transaction(
            recipient='foobar',
            initiator='test-1',
            amount=float(500),
            public_key=wallet.public_key,
            n=wallet.n
        )
        transaction, signature = wallet.sign_transaction(transaction)
        self.assertTrue(transaction.signature)
        self.assertIsInstance(transaction.signature, int)
        self.assertTrue(transaction.verify_signature())
