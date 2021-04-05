import logging
import os
import time
from math import inf
from os import environ
from threading import Thread

import requests
from redis import Redis

from block import Block
from blockchain import Blockchain
from peer2peer import PeerToPeerMessage
from transaction import Transaction

logging.basicConfig(level=logging.DEBUG)


class Miner(object):
    def __init__(self, *args, **kwargs):
        self.transactions = kwargs.get('transactions', {})
        self.block_size = 64
        self.miner = list()
        self.peers = environ.get('PEERS', 'http://localhost:8000').split(',')
        assert len(self.peers)
        self.cached_p2p_messages = dict()
        self.blockchain = Blockchain()
        self.redis_cli = Redis(host='redis')
        self.sync_to_redis()

    def get_peers_blockchain(self):
        try:
            blockchains = dict()
            _max = -inf
            best_peer = None
            with open("blockchain.dat", "rb") as f:
                blockchain_size = len(f.read())
            for peer in self.peers:
                r = requests.get("http://{}/api/blockchain".format(peer))
                if r.json().get('size'):
                    size = int(r.json().get('size'))
                    if size > _max:
                        _max = size
                        best_peer = peer
                    blockchains[peer] = r.json().get('size')
            if _max > blockchain_size:
                logging.debug("Downloading new blockchain from: {}".format(best_peer))
                os.rename('blockchain.dat', 'blockchain.backup')
                r = requests.get("http://{}/api/sync".format(best_peer))
                with open('blockchain.dat', 'wb') as f:
                    f.write(r.content)

                if self.blockchain.verify_blockchain():
                    os.remove('blockchain.backup')
                else:
                    os.remove('blockchain.dat')
                    os.rename('blockchain.backup', 'blockchain.dat')
        except requests.exceptions.ConnectionError:
            pass

    def sync_to_redis(self):
        for _, key in enumerate(self.transactions):
            self.redis_cli[key] = str(self.transactions[key])
        self.transactions = {}

    def broadcast_new_block(self, block):
        p2p = PeerToPeerMessage(block=block)
        for peer in self.peers:
            r = requests.post("http://{}/api/block".format(peer), data=p2p.to_json())
            assert r.status_code <= 299

    @staticmethod
    def ping_peer_transactions(peer, p2p_message):
        logging.debug("Forwarding transactions to nearest peer {}".format(peer))
        payload = p2p_message.to_json()
        try:
            requests.post("http://{}/api/transactions".format(peer), data=payload)
        except requests.exceptions.ConnectionError as e:
            logging.warning("Connection error {}".format(str(e)))

    @staticmethod
    def ping_peer_block(peer, p2p_message):
        logging.debug("Forwarding block to nearest peer {}".format(peer))
        payload = p2p_message.to_json()
        try:
            requests.post("http://{}/api/block".format(peer), data=payload)
        except requests.exceptions.ConnectionError as e:
            logging.warning("Connection error {}".format(str(e)))

    def forward(self, p2p, target):
        for peer in self.peers:
            t = Thread(target=target, args=(peer, p2p))
            t.start()

    # Todo: Transactions should be sorted by timestamp
    def compile_block(self):
        data = str()
        i = 0
        for transaction_id in self.redis_cli.keys():
            if i < 64:
                try:
                    transaction = self.redis_cli[transaction_id]
                    t = Transaction()
                    transaction = t.from_string(transaction.decode('utf-8'))
                    if not transaction.verify_signature():
                        logging.warning("Transaction signature not valid")
                        continue
                    data = data + str(transaction) + '\n'
                    self.redis_cli.delete(transaction.id)
                    i = i + 1
                except IndexError:
                    return False
        block = Block(data=data)
        return block

    def do_proof_of_work(self, block, first=False):
        if block:
            magic_number = 0
            while True:
                block.magic_number = magic_number
                if not first:
                    block.blockchain_snapshot = self.blockchain.get_sha512hash()
                else:
                    block.blockchain_snapshot = 'None'
                sha512hash = block.generate_hash()
                block.sha512hash = sha512hash
                if block.check_proof_of_work():
                    block.magic_number = magic_number
                    block.sha512hash = sha512hash
                    return block
                magic_number = magic_number + 1

    def routine(self):
        # Check if there is a new blockchain version
        while True:
            logging.debug("Requesting new blockchain info from P2P network")
            self.get_peers_blockchain()
            time.sleep(1)

            # Check if we have transactions
            if len(list(self.redis_cli.keys())):
                # Compile a  block
                logging.debug("Building a new block")
                block = self.compile_block()
                # Do proof of work
                logging.debug("Doing proof of work on block")
                block = self.do_proof_of_work(block)
                # Verify a block
                logging.debug("Verifying the block")
                if self.blockchain.verify_blockchain(new_block=block):
                    # Write the block
                    logging.debug("Writing a new block")
                    self.blockchain.write_new_block(block)


if __name__ == "__main__":
    miner = Miner()
    miner.routine()
