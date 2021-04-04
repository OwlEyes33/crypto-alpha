import time
from random import choice, randint
from uuid import uuid4

from blockchain import Blockchain
from block import Block
from miner import Miner
from transaction import Transaction
from wallet import Wallet
import os

TEST_WALLETS = [
    'd7c8b176-547f-4075-8de1-5b9d50eadffd',
    '561c568b-4642-4406-ac02-887db40e1e0d',
    '32cf2400-937f-48ad-9c74-de5fc92e4bdd'
]

GOD_WALLET = 'b2231abb-c5fd-49a7-a471-d248dd888df0'


def create_first_block():
    god_wallet = Wallet(id='b2231abb-c5fd-49a7-a471-d248dd888df0')
    god_wallet.generate_keypair()
    wallets = os.listdir(os.path.join(os.curdir, 'tests', 'wallets'))
    transactions = list()
    for wallet in wallets:
        with open('tests/wallets/{}/{}'.format(wallet, 'public_key.asc'), 'r') as f:
            public_key = int(f.read())
        with open('tests/wallets/{}/{}'.format(wallet, 'private_key.asc'), 'r') as f:
            private_key = int(f.read())
        with open('tests/wallets/{}/{}'.format(wallet, 'seed'), 'r') as f:
            seed = int(f.read())
        wallet = Wallet(public_key=public_key, private_key=private_key, seed=seed)
        transaction, signature = god_wallet.send_transaction(100000, recipient=wallet.generate_id())
        transaction.verify_signature()
        transactions.append(str(transaction))
    block = Blockchain.serialize_block(transactions)
    node = Miner()
    block = Block(data=block)
    block = node.do_proof_of_work(block, first=True)
    return block


def create_batch_fake_transactions():
    wallets = os.listdir(os.path.join(os.curdir, 'tests', 'wallets'))
    transactions = dict()
    receive = None
    for wallet in wallets:
        with open('tests/wallets/{}/{}'.format(wallet, 'public_key.asc'), 'r') as f:
            public_key = int(f.read())
        with open('tests/wallets/{}/{}'.format(wallet, 'private_key.asc'), 'r') as f:
            private_key = int(f.read())
        with open('tests/wallets/{}/{}'.format(wallet, 'seed'), 'r') as f:
            seed = int(f.read())
        assert public_key
        assert private_key
        assert seed
        wallet = Wallet(public_key=public_key, private_key=private_key, seed=seed)
        if receive:
            transaction = Transaction(recipient=receive.generate_id(),
                                      initiator=wallet.generate_id(),
                                      amount=randint(1, 5),
                                      timestamp=int(time.time()),
                                      public_key=wallet.public_key,
                                      n=wallet.n)
            transaction, signature = wallet.sign_transaction(transaction)
            transactions[transaction.id] = transaction
        receive = wallet
    return transactions
