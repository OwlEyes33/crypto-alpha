class UnverifiedBlock(Exception):
    def __init__(self):
        self.message = "The block cannot be verified."
        super().__init__(self.message)


class UnverifiedTransactionSignature(Exception):
    def __init__(self):
        self.message = "The signature of the transaction could  not be verified."
        super().__init__(self.message)


class IncorrectHash(Exception):
    def __init__(self):
        self.message = "The calculated hash for this block differs from input"
        super().__init__(self.message)


class InsufficientBalance(Exception):
    def __init__(self):
        self.message = "There is insufficient funds in the wallet for this transaction."
        super().__init__(self.message)


class DuplicateBlock(Exception):
    def __init__(self):
        self.message = "Attempting to add a duplicate block to the blockchain"
        super().__init__(self.message)
