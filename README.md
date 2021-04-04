# Coin v 0.3

Coin is an open source peer to peer distributed ledger, better known as a cryptocurrency.
The white paper for the blockchain implementation can be found here. The entire codebase is written in Python 3. Major influence 
for the coin's implementation was found from Satoshi's original Bitcoin paper, but it is not
a fork of Bitcoin. This codebase attempts to implement Satoshi's paper. 


### Miner
The miner for coin doubles as both a node and a miner. The program listens on the peer 2 peer network
for broadcasts of new blocks and new transactions. This program also acts as a miner,
verifying transactions and mining for blocks. This repo provides a docker container that runs
a small `alpine linux` instance. By running one of these nodes, owners make the network
stronger.

`docker-compose up node1 node2 node3 node4` This command will bring up a test, simulated
network with 4 miners running. The network starts with specific wallets in `wallets` as the first
few blocks. You can use the keys to create transactions and send them to the network.


### Wallet
The wallet is a terminal app used to generate new keys, display balance and send a transaction
to the peer 2 peer network. Take good care of your keys, please. The keys are `sha512` along with all
hashes and signatures in the implementation.


### Notes on Security

Verifying the blockchain involves verifying each block. To verify a block, we first
verify every transaction. Verifying a transaction means that the signature is valid, the addresses are valid, 
and the wallet sending the currency has sufficient balance. When all transactions are 
verified, a block is then verified by checking the proof of work. If both are valid, and we  have
never seen this block before, the block is valid. 

Transaction signatures use RSA signatures with 2048 bytes using `sha512`. The proof of work
is found by incrementing a nonce in a sha512 hash until the last n characters are `0`.
The hash `19c5a743a45a7c25f3470e1f25714c569f265ee6c198513578403b9893f6c4a881d46cea97bc629ad17ac8c80651dd1f712585c318604da7c30b93ea456f0000`
is valid, for example. 

### Testing

`python3 -m unittest tests/*.py` This will run the entire test suite. 
