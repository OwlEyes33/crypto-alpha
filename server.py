import json
import logging
from hashlib import sha512
from os import environ
from wsgiref import simple_server

import falcon
from redis import Redis

from block import Block
from blockchain import Blockchain
from exceptions import DuplicateBlock
from miner import Miner
from peer2peer import PeerToPeerMessage, P2PNode
from transaction import Transaction

logging.basicConfig(level=logging.DEBUG)


class NewTransactions(object):

    def __init__(self):
        self.miner = Miner()
        self.redis_cli = Redis(host='redis')

    def handle_p2p_request(self, resp, data):
        if data.get('message') == 'p2p':
            p2p = PeerToPeerMessage(**data)
            if p2p.id in self.miner.cached_p2p_messages:
                resp.status = falcon.HTTP_200
                return
            else:
                self.miner.cached_p2p_messages[p2p.id] = 1
            return p2p
        else:
            return False

    def handle_new_transactions(self, transactions):
        new_transactions = dict()
        for transaction in transactions:
            t = Transaction()
            t.from_string(transaction)
            t.verify_signature()
            new_transactions[t.id] = t
        logging.debug("Adding new transactions to redis...")
        for _, transaction_id in enumerate(new_transactions):
            if transaction_id in self.redis_cli.keys():
                continue  # We already have this transaction in the cache
            else:
                # New transaction
                self.redis_cli[transaction_id] = str(new_transactions[transaction_id])

    def on_post(self, req, resp):
        logging.debug("Incoming new transactions....")
        try:
            payload = req.bounded_stream.read()
            data = json.loads(payload)
            # If the message is Peer to Peer, load the object
            p2p = self.handle_p2p_request(resp, data)
            if p2p:
                self.miner.forward(p2p, self.miner.ping_peer_transactions)
                self.handle_new_transactions(p2p.transactions)
        except json.decoder.JSONDecodeError:
            resp.status = falcon.HTTP_400
            return


class NewBlock(object):

    def __init__(self):
        self.miner = Miner()
        self.blockchain = Blockchain()

    def handle_p2p_request(self, data):
        if data.get('message') == 'p2p':
            p2p = PeerToPeerMessage(**data)
            if not p2p.timestamp:
                return False
            if p2p.id in self.miner.cached_p2p_messages:
                return False
            else:
                self.miner.cached_p2p_messages[p2p.id] = 1
            return p2p

    def handle_new_block(self, block):
        logging.debug("Recieved a new block from P2P request")
        if self.blockchain.verify_blockchain(new_block=block):
            logging.debug("Block is verified, writing.")
            self.blockchain.write_new_block(block)
            logging.debug("Wrote block.")
            return True
        return False

    def on_post(self, req, resp):
        try:
            payload = req.bounded_stream.read()
            data = json.loads(payload)
            p2p = self.handle_p2p_request(data)
            if p2p:
                self.miner.forward(p2p, self.miner.ping_peer_block)
                p2p.block = json.loads(p2p.block)
                block = Block(**p2p.block)
                logging.debug("New block: {} {}".format(block.sha512hash, block.magic_number))
                if self.handle_new_block(block):
                    resp.status = falcon.HTTP_200
                else:
                    resp.status = falcon.HTTP_400
            else:
                resp.status = falcon.HTTP_302
                return
            resp.status = falcon.HTTP_200
        except DuplicateBlock:
            resp.status = falcon.HTTP_400
            return
        except json.decoder.JSONDecodeError:
            resp.status = falcon.HTTP_400
        return


class BlockChainData(object):
    def __init__(self):
        self.miner = Miner()
        self.blockchain = Blockchain()

    def on_get(self, req, resp):
        sha512hash = sha512()
        size = 0
        with open("blockchain.dat", "r") as f:
            while True:
                data = f.read(65536)
                size += len(data)
                if not data:
                    break
                sha512hash.update(data.encode("utf-8"))
        _hash = str(sha512hash.hexdigest())
        logging.debug("Hash:{}".format(_hash))
        resp.body = json.dumps({"sha512": _hash, "size": size})
        resp.status = falcon.HTTP_200
        return


class Sync(object):
    def __init__(self):
        self.miner = Miner()
        self.blockchain = Blockchain()

    def on_get(self, req, resp):
        f = open('blockchain.dat', 'rb')
        resp.stream = f
        resp.status = falcon.HTTP_200
        return


class Connections(object):
    def on_get(self, req, resp):
        node = P2PNode()
        connections = node.neighbor_connections_request()
        resp.body = json.dumps({'connections': connections})
        resp.status = falcon.HTTP_200
        return


class ConnectionRequest(object):
    def on_get(self, req, resp):
        node = P2PNode()
        answer = node.connection_request(node.uri)
        resp.body = json.dumps({'answer': answer})
        resp.status = falcon.HTTP_200
        return


api = falcon.API()
api.add_route('/api/transactions', NewTransactions())
api.add_route('/api/block', NewBlock())
api.add_route('/api/blockchain', BlockChainData())
api.add_route('/api/sync', Sync())
api.add_route('/api/p2p/connections', Connections())
api.add_route('/api/p2p/request_connection', ConnectionRequest())

if __name__ == '__main__':
    logging.debug("Node coming online....")
    httpd = simple_server.make_server('0.0.0.0', int(environ.get('NODE_PORT', 8000)), api)
    logging.debug("Port opened: {}".format(int(environ.get('NODE_PORT', 8000))))
    httpd.serve_forever()
