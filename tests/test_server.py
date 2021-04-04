import os
import shutil
import time
import unittest
from hashlib import sha512

import falcon
from falcon import testing
from redis import Redis

from block import Block
from blockchain import Blockchain
from miner import Miner
from peer2peer import PeerToPeerMessage
from server import NewBlock, NewTransactions, BlockChainData, Sync
from tests.helpers import create_batch_fake_transactions
from transaction import Transaction


def create_api():
    api = falcon.API()
    api.add_route('/api/block', NewBlock())
    api.add_route('/api/transactions', NewTransactions())
    api.add_route('/api/blockchain', BlockChainData())
    api.add_route('/api/sync', Sync())
    return api


class TestServer(unittest.TestCase):
    def setUp(self) -> None:
        shutil.copy("blockchain.fake", "blockchain.dat")
        transactions = create_batch_fake_transactions()
        self.miner = Miner(transactions=transactions)
        self.blockchain = Blockchain()
        self.miner.sync_to_redis()
        self.client = testing.TestClient(create_api())
        self.redis_cli = Redis()

    def tearDown(self) -> None:
        try:
            os.remove('blockchain.dat')
            self.redis_cli.flushall()
            os.remove('blockchain.dat2')
        except FileNotFoundError:
            pass

    def test_blockchain_sync(self):
        result = self.client.simulate_get('/api/sync',
                                          headers={'Content-Type': 'application/octet-stream'})
        f1 = open('blockchain.dat', "rb")
        data = f1.read()
        self.assertEqual(result.content, data)
        with open("blockchain.dat2", "wb") as f:
            f.write(result.content)
        time.sleep(0.5)
        f2 = open('blockchain.dat2', 'rb')
        self.assertEqual(f2.read(), data)

    def assertValidTransaction(self, transaction):
        signature = int(transaction[-1])
        public_key = int(transaction[-3])
        n = int(transaction[-2])
        msg = bytes(" ".join(transaction[0:-1]), encoding='utf-8')
        sha512hash = int.from_bytes(sha512(msg).digest(), byteorder='big')
        hash_from_signature = pow(signature, public_key, n)
        self.assertTrue(sha512hash == hash_from_signature)

    def assertIsHeader(self, line):
        line = line.strip()
        data = line.split(' ')
        self.assertTrue(len(data) == 4)
        self.assertIsInstance(data[0], str)
        self.assertEqual(data[0][-4:], '0000')
        self.assertIsInstance(int(data[1]), int)
        self.assertIsInstance(int(data[2]), int)
        return int(data[2])

    def assertIsTransaction(self, line):
        line = line.strip()
        data = line.split(' ')
        self.assertValidTransaction(data)
        self.assertTrue(len(data) == 8)
        self.assertIsInstance(data[0], str)
        self.assertIsInstance(data[1], str)
        self.assertIsInstance(float(data[2]), float)
        self.assertIsInstance(int(data[3]), int)
        self.assertIsInstance(data[4], str)
        self.assertIsInstance(int(data[5]), int)
        self.assertIsInstance(int(data[6]), int)
        self.assertIsInstance(int(data[7]), int)

    def test_blockchain_file(self):
        with open("blockchain.dat", "r") as f:
            header = f.readline()
            transaction_count = self.assertIsHeader(header)
            for _ in range(0, transaction_count):
                line = f.readline()
                self.assertIsTransaction(line)

    def test_get_blockchain_hash(self):
        result = self.client.simulate_get('/api/blockchain')
        self.assertTrue(result.json.get('sha512'))
        self.assertIsInstance(result.json.get('sha512'), str)
        self.assertTrue(result.json.get('size'))
        self.assertIsInstance(result.json.get('size'), int)
        self.assertLessEqual(result.status_code, 299)

    def test_new_transactions(self):
        transactions = create_batch_fake_transactions()
        payload = list()
        for _, key in enumerate(transactions):
            payload.append(str(transactions[key]))
        p2p = PeerToPeerMessage(transactions=payload)
        result = self.client.simulate_post('/api/transactions', body=p2p.to_json())
        self.assertLessEqual(result.status_code, 299)
        for _, key in enumerate(transactions):
            transaction = self.redis_cli[key]
            self.assertIsInstance(transaction, bytes)
            transaction = transaction.decode('utf-8')
            t = Transaction()
            self.assertTrue(t.from_string(transaction))

    def test_new_block(self):
        result = self.client.simulate_get('/api/block')
        self.assertEqual(result.status_code, 405)
        block = self.miner.compile_block()
        block = self.miner.do_proof_of_work(block)
        timestamp = int(time.time())
        if self.blockchain.verify(new_block=block):
            p2p = PeerToPeerMessage(block=block.to_json(), timestamp=timestamp)
            result = self.client.simulate_post('/api/block', body=p2p.to_json())
            self.assertLessEqual(result.status_code, 299)
        self.blockchain.verify()
        self.test_blockchain_file()

        # Test cached p2p message
        p2p = PeerToPeerMessage(block=block.to_json(), timestamp=timestamp)
        result = self.client.simulate_post('/api/block', body=p2p.to_json())
        self.assertEqual(302, result.status_code)

    def test_compile_block(self):
        block = self.miner.compile_block()
        self.assertIsInstance(block, Block)
