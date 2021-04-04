import unittest
from wallet import Wallet
import os


class Simulation(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        pass

    @staticmethod
    def test_create_first_wallets():
        wallets = list()
        for _ in range(0, 10):
            wallet = Wallet()
            wallets.append(wallet)
        for wallet in wallets:
            wallet.generate_keypair()
            os.mkdir(os.path.join(os.curdir, "wallets", wallet.generate_id()[0:10]))
            with open(os.path.join(os.curdir, "wallets", wallet.generate_id()[0:10], "public_key.asc"), "w") as f:
                f.write(str(wallet.public_key))
            with open(os.path.join(os.curdir, "wallets", wallet.generate_id()[0:10], "private_key.asc"), "w") as f:
                f.write(str(wallet.private_key))
            with open(os.path.join(os.curdir, "wallets", wallet.generate_id()[0:10], "seed"), "w") as f:
                f.write(str(wallet.n))
