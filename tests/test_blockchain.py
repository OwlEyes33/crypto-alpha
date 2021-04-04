import logging
import os
import shutil
import time
import unittest

from block import Block
from blockchain import Blockchain
from miner import Miner
from tests.helpers import create_batch_fake_transactions, create_first_block
import pandas as pd

logging.basicConfig(level=logging.DEBUG)


class TestBlockchain(unittest.TestCase):

    def setUp(self) -> None:
        # We create a temporary, fake copy of a small blockchain to simulate new transactions
        shutil.copy("blockchain.fake", "blockchain.dat")
        self.blockchain = Blockchain()
        transactions = create_batch_fake_transactions()
        self.miner = Miner(transactions=transactions)
        self.miner.sync_to_redis()

    def tearDown(self) -> None:
        os.remove('blockchain.dat')

    def test_sha512hash(self):
        sha512hash = self.blockchain.get_sha512hash()
        self.assertIsInstance(sha512hash, str)
        self.assertIsInstance(self.blockchain.sha512hash[1], int)

    def test_dataframe_blockchain(self):
        df = pd.DataFrame([], columns=['recipient', 'initiator',
                                       'amount', 'timestamp', 'id',
                                       'public_key', 'n', 'signature'])
        with open("blockchain.dat", "r") as f:
            while True:
                line = f.readline()
                if not line:
                    break
                if len(line.split(' ')) <= 4:
                    continue
                else:
                    df2 = pd.DataFrame([line.split(' ')], columns=['recipient', 'initiator',
                                                   'amount', 'timestamp', 'id',
                                                   'public_key', 'n', 'signature'])
                    df = df.append(df2)

    def test_first_block(self):
        block = create_first_block()
        self.assertTrue(block.magic_number)

    def test_blockchain_difficulty(self):
        now = int(time.time())
        difficult = Block.get_current_difficulty(now)
        self.assertEqual(difficult, 4)

        # 3 years later
        now = now + 60 * 60 * 24 * 30 * 12 * 3
        difficult = Block.get_current_difficulty(now)
        self.assertEqual(difficult, 5)

        # 6 years later
        now = now + 60 * 60 * 24 * 30 * 12 * 6
        difficult = Block.get_current_difficulty(now)
        self.assertEqual(difficult, 7)

    def test_read_block(self):
        block = True
        while block:
            try:

                block = next(self.blockchain.read_block())
                self.assertIsInstance(block, Block)
                self.assertIsInstance(block.magic_number, int)
                self.assertIsInstance(block.data, str)
                self.assertIsInstance(block.sha512hash, str)
            except StopIteration:
                break

    def test_verify_new_block(self):
        block = self.miner.compile_block()
        block = self.miner.do_proof_of_work(block)
        self.assertTrue((self.blockchain.verify(new_block=block)))

    # Todo: Test that duplicate transactions cannot exist
    def test_verify_blockchain(self):
        self.assertTrue(self.blockchain.verify())

    def test_write_new_block(self):
        block = self.miner.compile_block()
        block = self.miner.do_proof_of_work(block)
        self.assertTrue((self.blockchain.verify(new_block=block)))
        self.blockchain.write_new_block(block)

    def test_write_multiple_blocks(self):
        for _ in range(0, 5):
            self.miner = Miner(transactions=create_batch_fake_transactions())
            block = self.miner.compile_block()
            self.assertIsInstance(block, Block)
            self.assertIsNone(block.magic_number)
            self.assertIsNone(block.sha512hash)
            block = self.miner.do_proof_of_work(block)
            self.assertIsNotNone(block.magic_number)
            self.assertIsNotNone(block.sha512hash)
            self.assertTrue(self.blockchain.verify(new_block=block))
            self.blockchain.write_new_block(block=block)
