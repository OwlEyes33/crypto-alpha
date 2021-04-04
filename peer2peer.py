import json
import logging
import socket
from hashlib import sha512
from os import environ

import requests
from redis import Redis

logging.basicConfig(level=logging.DEBUG)


class P2PNode(object):
    def __init__(self, *args, **kwargs):
        self.max_node_size = 50
        self.redis_cli = Redis()
        self.connections = json.loads(self.redis_cli['connections'])
        self.cores = 4
        self.uri = kwargs.get('uri', "{}:{}".format(socket.gethostname(),
                                                    int(environ.get('NODE_PORT', 8000))))

    def request_neighbor_connections(self, node):
        r = requests.get("http://{}/p2p/connections".format(node))
        return r.json().get('connections')

    def request_connection(self, node):
        r = requests.get("http://{}/p2p/request_connection".format(node), params={'node': self.uri})
        answer = r.json().get('answer')
        if answer:
            self.connections.append(answer)

    def neighbor_connections_request(self):
        return json.dumps(self.connections)

    def connection_request(self, node):
        if len(self.connections) < self.max_node_size:
            self.connections.append(node)
            self.sync()
            return True
        else:
            return False

    def sync(self):
        self.redis_cli['connections'] = json.dumps(self.connections)

    # Todo: make this async
    def walk_network(self):
        for connection in self.connections:
            if len(self.connections) < self.max_node_size:
                neighbors = self.request_neighbor_connections(connection)
                for peer in neighbors:
                    if len(self.connections) < self.max_node_size:
                        self.request_connection(peer)
                    else:
                        break
            else:
                break


class PeerToPeerMessage(object):
    def __init__(self, *args, **kwargs):
        self.transactions = kwargs.get('transactions')
        self.block = kwargs.get('block')
        self.timestamp = kwargs.get('timestamp')
        self.id = kwargs.get('id')
        if not self.id:
            self.id = self.generate_id()

    def generate_id(self):
        if self.transactions:
            message_id = sha512("{}{}".format(str(self.transactions),
                                              str(self.timestamp)).encode("utf-8")).hexdigest()
            return message_id
        if self.block:
            message_id = sha512("{}{}".format(str(self.block),
                                              str(self.timestamp)).encode("utf-8")).hexdigest()
            return message_id

    def to_json(self):
        return json.dumps({"id": self.id, "transactions": self.transactions,
                           "message": "p2p", "timestamp": self.timestamp, 'block': self.block})
