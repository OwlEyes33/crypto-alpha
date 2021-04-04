import time
import unittest
from wallet import Wallet
import os
import random
from peer2peer import PeerToPeerMessage
import requests


class TestSimulation(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        pass

    @staticmethod
    def open_wallet(wallet):
        with open('tests/wallets/{}/{}'.format(wallet, 'public_key.asc'), 'r') as f:
            public_key = int(f.read())
        with open('tests/wallets/{}/{}'.format(wallet, 'private_key.asc'), 'r') as f:
            private_key = int(f.read())
        with open('tests/wallets/{}/{}'.format(wallet, 'seed'), 'r') as f:
            seed = int(f.read())
        wallet = Wallet(public_key=public_key, private_key=private_key, seed=seed)
        return wallet

    @staticmethod
    def generate_transactions():
        wallets = os.listdir(os.path.join('tests', 'wallets'))
        transactions = list()
        for wallet in wallets:
            wallet = TestSimulation.open_wallet(wallet)
            wallet2 = random.choice(wallets)
            wallet2 = TestSimulation.open_wallet(wallet2)
            transaction, signature = wallet.send_transaction(5, wallet2.generate_id())
            transactions.append(str(transaction))
        p2p = PeerToPeerMessage(transactions=transactions, timestamp=int(time.time()))
        r = requests.post("http://node1:8000/api/transactions", data=p2p.to_json())
        assert r.status_code <= 299

    def test_run_simulation(self):
        while True:
            TestSimulation.generate_transactions()
            time.sleep(10)
