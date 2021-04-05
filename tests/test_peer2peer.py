import json
import os
import shutil
import time
import unittest

from blockchain import Blockchain
from miner import Miner
from peer2peer import PeerToPeerMessage
from tests.helpers import create_batch_fake_transactions


class TestPeer2Peer(unittest.TestCase):
    def setUp(self) -> None:
        shutil.copy("blockchain.fake", "blockchain.dat")
        transactions = create_batch_fake_transactions()
        self.miner = Miner(transactions=transactions)
        self.blockchain = Blockchain()
        self.miner.sync_to_redis()

    def tearDown(self) -> None:
        try:
            os.remove('blockchain.dat')
            os.remove('transactions.db')
        except FileNotFoundError:
            pass

    def test_peer2peer_message_block(self):
        block = self.miner.compile_block()
        block = self.miner.do_proof_of_work(block)
        if self.blockchain.verify_blockchain(new_block=block):
            p2p = PeerToPeerMessage(block=block.to_dict(), timestamp=int(time.time()))
            self.assertTrue(p2p.block)
            self.assertTrue(p2p.timestamp)
            self.assertTrue(p2p.block.get('data'))
            self.assertTrue(len(p2p.block.get('data').split('\n')))
            self.assertTrue(p2p.block.get('sha512hash'))
            self.assertTrue(p2p.block.get('magic_number'))
            self.assertIsInstance(p2p.block.get('magic_number'), int)
            self.assertIsInstance(p2p.block.get('sha512hash'), str)
            self.assertIsInstance(p2p.block.get('data'), str)
            block.get_associated_wallets()
            payload = p2p.to_json()
            self.assertIsInstance(payload, str)
            data = json.loads(payload)
            p2p = PeerToPeerMessage(**data)
            block.get_associated_wallets()
            self.assertTrue(p2p.block)
            self.assertTrue(p2p.timestamp)
            self.assertTrue(p2p.block.get('data'))
            self.assertTrue(len(p2p.block.get('data').split('\n')))
            self.assertTrue(p2p.block.get('sha512hash'))
            self.assertTrue(p2p.block.get('magic_number'))
            self.assertIsInstance(p2p.block.get('magic_number'), int)
            self.assertIsInstance(p2p.block.get('sha512hash'), str)
            self.assertIsInstance(p2p.block.get('data'), str)

