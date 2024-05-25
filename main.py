import json
import hashlib
from datetime import datetime


class MerkleTree:
    def __init__(self, transactions, merkle_root=''):
        if merkle_root == '':
            self.merkle_root = self.create_merkle_root(transactions)
        else:
            self.merkle_root = merkle_root

    def create_merkle_root(self, transactions):
        if len(transactions) == 0:
            return ''
        if len(transactions) == 1:
            return hashlib.sha256(transactions[0].encode()).hexdigest()

        new_level = []
        for i in range(0, len(transactions) - 1, 2):
            new_level.append(self.hash_pair(transactions[i], transactions[i + 1]))

        if len(transactions) % 2 == 1:
            new_level.append(self.hash_pair(transactions[-1], transactions[-1]))

        return self.create_merkle_root(new_level)

    def hash_pair(self, left, right):
        return hashlib.sha256((left + right).encode()).hexdigest()


class Block:
    def __init__(self, transactions, previous_hash):
        self.timestamp = datetime.now()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.merkle_tree = MerkleTree([str(tx) for tx in transactions])
        self.nonce = 0
        self.hash = self.generate_hash()

    def generate_hash(self):
        block_contents = str(self.timestamp) + str(self.transactions) + str(self.previous_hash) + str(
            self.nonce) + self.merkle_tree.merkle_root
        block_hash = hashlib.sha256(block_contents.encode()).hexdigest()
        return block_hash

    def verify_transactions(self):
        new_merkle_tree = MerkleTree(transactions=[str(tx) for tx in self.transactions])
        return new_merkle_tree.merkle_root == self.merkle_tree.merkle_root

    def to_dict(self):
        return {
            'timestamp': str(self.timestamp),
            'transactions': self.transactions,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'hash': self.hash,
            'merkle_root': self.merkle_tree.merkle_root
        }


def from_dict(data):
    block = Block(data['transactions'], data['previous_hash'])
    block.timestamp = datetime.fromisoformat(data['timestamp'])
    block.nonce = data['nonce']
    block.hash = data['hash']
    block.merkle_tree = MerkleTree('', data['merkle_root'])
    return block


class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(transactions=[], previous_hash="0")
        self.chain.append(genesis_block)

    def add_block(self):
        previous_block = self.chain[-1]
        new_block = Block(transactions=self.current_transactions, previous_hash=previous_block.hash)
        new_block.hash = self.proof_of_work(new_block)
        self.chain.append(new_block)
        self.current_transactions = []

    def proof_of_work(self, block):
        while block.hash[:4] != "0000":
            block.nonce += 1
            block.hash = block.generate_hash()
        return block.hash

    def add_transaction(self, sender, receiver, amount):
        new_transaction = {
            'sender': sender,
            'receiver': receiver,
            'amount': amount
        }
        self.current_transactions.append(new_transaction)

    def get_balance(self, person):
        balance = 0
        for block in self.chain:
            for transaction in block.transactions:
                if transaction['sender'] == person:
                    balance -= transaction['amount']
                if transaction['receiver'] == person:
                    balance += transaction['amount']
        return balance

    def get_min_max_balance(self, person):
        min_balance = 0
        max_balance = float('-inf')
        balance = 0

        for block in self.chain:
            for transaction in block.transactions:
                if transaction['sender'] == person:
                    balance -= transaction['amount']
                if transaction['receiver'] == person:
                    balance += transaction['amount']
                min_balance = min(min_balance, balance)
                max_balance = max(max_balance, balance)

        return min_balance, max_balance

    def verify_chain(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            if current_block.hash != current_block.generate_hash():
                return False
            if current_block.previous_hash != previous_block.hash:
                return False
        return True

    def verify_all_transactions(self):
        for block in self.chain:
            if not block.verify_transactions():
                return False
        return True

    def get_positive_balance_users(self):
        balance = {}
        for block in self.chain:
            for transaction in block.transactions:
                sender = transaction['sender']
                receiver = transaction['receiver']
                amount = transaction['amount']
                balance[sender] = balance.get(sender, 0) - amount
                balance[receiver] = balance.get(receiver, 0) + amount
        positive_balance_users = [user for user, bal in balance.items() if bal > 0]
        return positive_balance_users

    def save_to_file(self, filename):
        with open(filename, 'w') as file:
            chain_data = [block.to_dict() for block in self.chain]
            json.dump(chain_data, file)

    def load_from_file(self, filename):
        with open(filename, 'r') as file:
            chain_data = json.load(file)
            self.chain = [from_dict(block_data) for block_data in chain_data]


if __name__ == '__main__':
    blockchain = Blockchain()
    blockchain.add_transaction('Alice', 'Bob', 50)
    blockchain.add_transaction('Bob', 'Kate', 20)
    blockchain.add_block()

    print("Balance of Alice:", blockchain.get_balance('Alice'))
    print("Balance of Bob:", blockchain.get_balance('Bob'))
    print("Balance of Kate:", blockchain.get_balance('Kate'))
    print("Balance of Mike:", blockchain.get_balance('Mike'))
    print("Balance of Jane:", blockchain.get_balance('Jane'))

    min_balance, max_balance = blockchain.get_min_max_balance('Bob')
    print("Min balance of Bob:", min_balance)
    print("Max balance of Bob:", max_balance)
    print("Positive balances:", blockchain.get_positive_balance_users())

    print("Is blockchain valid?", blockchain.verify_chain())
    print("Is all transactions valid?", blockchain.verify_all_transactions())
    blockchain.save_to_file('blockchain.json')
    print()

    blockchain.add_transaction('Alice', 'Jane', 250)
    blockchain.add_transaction('Jane', 'Bob', 60)
    blockchain.add_transaction('Jane', 'Mike', 80)
    blockchain.add_transaction('Mike', 'Jane', 20)
    blockchain.add_transaction('Jane', 'Bob', 40)
    blockchain.add_block()

    print("Balance of Alice:", blockchain.get_balance('Alice'))
    print("Balance of Bob:", blockchain.get_balance('Bob'))
    print("Balance of Kate:", blockchain.get_balance('Kate'))
    print("Balance of Mike:", blockchain.get_balance('Mike'))
    print("Balance of Jane:", blockchain.get_balance('Jane'))

    min_balance, max_balance = blockchain.get_min_max_balance('Jane')
    print("Min balance of Jane:", min_balance)
    print("Max balance of Jane:", max_balance)
    print("Positive balances:", blockchain.get_positive_balance_users())

    print("Is blockchain valid?", blockchain.verify_chain())
    print("Is all transactions valid?", blockchain.verify_all_transactions())
    blockchain.save_to_file('blockchain.json')
    print()

    new_blockchain = Blockchain()
    new_blockchain.load_from_file('blockchain.json')

    print("Is loaded blockchain valid?", new_blockchain.verify_chain())
    print("Is all transactions valid?", new_blockchain.verify_all_transactions())

    new_blockchain.add_transaction('Kate', 'Alice', 20)
    new_blockchain.add_transaction('Mike', 'Jane', 100)
    new_blockchain.add_transaction('Bob', 'Mike', 30)
    new_blockchain.add_block()

    print("Balance of Alice:", new_blockchain.get_balance('Alice'))
    print("Balance of Bob:", new_blockchain.get_balance('Bob'))
    print("Balance of Kate:", new_blockchain.get_balance('Kate'))
    print("Balance of Mike:", new_blockchain.get_balance('Mike'))
    print("Balance of Jane:", new_blockchain.get_balance('Jane'))

    min_balance, max_balance = new_blockchain.get_min_max_balance('Mike')
    print("Min balance of Mike:", min_balance)
    print("Max balance of Mike:", max_balance)
    print("Positive balances:", new_blockchain.get_positive_balance_users())

    print("Is blockchain valid?", new_blockchain.verify_chain())
    print("Is all transactions valid?", new_blockchain.verify_all_transactions())
    new_blockchain.save_to_file('blockchain.json')
    print()
