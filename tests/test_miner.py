import os
import shutil
import unittest

from redis import Redis

from block import Block
from blockchain import Blockchain
from miner import Miner
from tests.helpers import create_batch_fake_transactions


class TestMiner(unittest.TestCase):
    def setUp(self) -> None:
        shutil.copy("blockchain.fake", "blockchain.dat")
        self.blockchain = Blockchain()
        self.redis_cli = Redis()

    def tearDown(self) -> None:
        self.redis_cli.flushall()
        os.remove('blockchain.dat')

    def test_transactions_removed_after_block(self):
        transactions = create_batch_fake_transactions()
        self.miner = Miner()
        self.assertTrue(list(self.redis_cli.keys()) == [])
        self.miner = Miner(transactions=transactions)
        self.miner.sync_to_redis()
        for _, key in enumerate(transactions):
            self.assertTrue(self.redis_cli[key])
        block = self.miner.compile_block()
        transactions = block.deserialize()
        for _, key in enumerate(transactions):
            self.assertTrue(key not in self.redis_cli.keys())

    def test_sync_redis(self):
        transactions = create_batch_fake_transactions()
        self.miner = Miner()
        self.assertTrue(list(self.redis_cli.keys()) == [])
        self.miner = Miner(transactions=transactions)
        self.miner.sync_to_redis()
        for _, key in enumerate(transactions):
            self.assertTrue(self.redis_cli[key])

    def test_compile_block(self):
        self.miner = Miner(transactions=create_batch_fake_transactions())
        block = self.miner.compile_block()
        self.assertIsInstance(block, Block)
        self.assertIsNone(block.magic_number)
        self.assertIsNone(block.sha512hash)
        block = self.miner.do_proof_of_work(block)
        self.assertIsNotNone(block.magic_number)
        self.assertIsNotNone(block.sha512hash)
        self.assertTrue(self.blockchain.verify(new_block=block))

