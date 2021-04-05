import logging
import time
from hashlib import sha512

from redis import Redis

from block import Block
from exceptions import InsufficientBalance, UnverifiedBlock, IncorrectHash, UnverifiedTransactionSignature, \
    DuplicateBlock
from transaction import Transaction

logging.basicConfig(level=logging.DEBUG)


class Blockchain(object):
    def __init__(self):
        self.sha512hash = False
        self.file_handler = None
        self.redis_cli = Redis(host='redis')

    def get_sha512hash(self):
        delta = 0
        if self.sha512hash:
            delta = int(time.time()) - int(self.sha512hash[1])
        if not self.sha512hash or delta > 60 * 5:
            sha512hash = sha512()
            with open("blockchain.dat", "r") as f:
                while True:
                    data = f.read(65536)
                    if not data:
                        break
                    sha512hash.update(data.encode("utf-8"))
            self.sha512hash = str(sha512hash.hexdigest()), int(time.time())
        else:
            return self.sha512hash[0]
        return self.sha512hash[0]

    def read_block(self):
        while True:
            if self.file_handler:
                block_header = self.file_handler.readline().strip().split(' ')
                if len(block_header) < 3:
                    return False
                transaction_count = int(block_header[2])
                blockchain_snapshot = str(block_header[3])
                block = Block(data='', magic_number=int(block_header[1]),
                              sha512hash=str(block_header[0]), blockchain_snapshot=blockchain_snapshot)
                transactions = dict()
                for _ in range(0, transaction_count):
                    line = self.file_handler.readline().strip()
                    transaction = Transaction()
                    transaction = transaction.from_string(line)
                    transactions[transaction.id] = str(transaction)
                block.data = block.block_to_serialized(transactions)
                yield block
            else:
                break

    @staticmethod
    def verify_block_transactions(wallets, block, new_block=False):
        block.get_block_transactions()
        for transaction in block.transactions:
            # For each transaction in the blockchain, build up a balance for each wallet
            if new_block:
                if transaction.initiator in wallets.keys():
                    wallets[transaction.initiator] -= float(transaction.amount)
                if transaction.recipient in wallets.keys():
                    wallets[transaction.recipient] += float(transaction.amount)

            # Verify the transaction signature
            if not transaction.verify_signature():
                raise UnverifiedTransactionSignature

    @staticmethod
    def verify_block(block):
        # Verify the proof of work on the block
        verified_hash = block.sha512hash
        sha512hash = block.generate_hash()
        if sha512hash != verified_hash:
            raise IncorrectHash
        block.check_proof_of_work()
        if not block.check_proof_of_work():
            raise UnverifiedBlock

    # Todo: Verify there are no duplicate transactions
    def verify_blockchain(self, new_block=None):
        tracked_wallets = dict()
        with open("blockchain.dat", "r") as self.file_handler:
            if new_block:
                tracked_wallets = new_block.get_associated_wallets()
            while True:
                try:
                    block = next(self.read_block())
                    if new_block and new_block.sha512hash == block.sha512hash:
                        raise DuplicateBlock
                    Blockchain.verify_block(block)
                    Blockchain.verify_block_transactions(tracked_wallets, block, new_block=new_block)
                except StopIteration:
                    break

            if new_block:

                new_block.get_block_transactions()
                # For each transaction in the new block
                for transaction in new_block.transactions:
                    # Verify the RSA signature on the transaction string
                    if not transaction.verify_signature():
                        raise UnverifiedTransactionSignature

                    # Check the the necessary wallet has the correct balance from blockchain history
                    if tracked_wallets[transaction.initiator] < float(transaction.amount):
                        raise InsufficientBalance

                sha512hash = new_block.generate_hash()
                if sha512hash != new_block.sha512hash:
                    raise IncorrectHash
            return True

    def write_new_block(self, block):
        with open("blockchain.dat", "a") as self.file_handler:
            transactions = block.data.split('\n')
            self.file_handler.write("{} {} {} {}\n".format(block.sha512hash, block.magic_number,
                                                           len(block.transactions), block.blockchain_snapshot))
            for transaction in transactions:
                if transaction != '':
                    transaction = transaction.strip()
                    self.file_handler.write(str(transaction) + '\n')
        logging.debug("New blockchain hash: {}".format(self.get_sha512hash()))

    @staticmethod
    def serialize_block(transactions):
        transactions_data = str()
        for transaction in transactions:
            transaction = transaction.split(' ')
            transaction = Transaction(
                recipient=transaction[0],
                initiator=transaction[1],
                amount=float(transaction[2]),
                timestamp=transaction[3],
                id=transaction[4],
                public_key=int(transaction[5]),
                n=int(transaction[6]),
                signature=int(transaction[7])
            )
            transactions_data = transactions_data + str(transaction) + "\n"
        return transactions_data
