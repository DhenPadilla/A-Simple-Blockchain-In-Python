"""

A simple localhost implementation of a Blockchain transaction
system written in Python by Dhen Padilla

Uses a simple consensus (Longest matching blockchain with correct proofs)

Easy Hash as the first 4 characters must be zeroes

"""


import hashlib
import json
from textwrap import dedent
from time import time
from uuid import uuid4
from flask import Flask, jsonify, request
from urllib.parse import urlparse
import requests

class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.new_block(previous_hash=1, proof=100)
        self.nodes = set()

    def register_node(self, address):
        """
        Add a new node to the list of nodes

        :param address: <str> address of the node. E.g: 'http://192.168.0.5:5000"
        :return: None
        """

        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)


    def proof_of_work(self, last_proof):
        """
        A simple proof of work algorithm:
        - Find a number p' s.t hash(pp') contains leading 4 zeroes
        - Where p is the previous proof, and p' is the new proof

        :param last_proof: <int>
        :return: <int>
        """

        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, new_proof):

        """
        Validates the Proof via: Hash(last_proof, new_proof)
         and checks whether the hash contains 4 leading zeroes

        :param last_proof: <int> Previous Proof
        :param new_proof: <int> Current Proof
        :return: <bool> Returns True if Correct, False if not
        """

        guess = f'{last_proof}{new_proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()

        return guess_hash[:4] == "0000"


    def new_block(self, proof, previous_hash = None):
        """
        Creates a new block within the chain

        :param proof: <int> The proof given by the Proof Of Work algorithm
        :param previous_hash: (Optional) <str> Hash of previous Block
        :return: <dict> New block (JSON OBJECT)
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }

        # Reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        # Adds new transaction to the list of transactions
        """
        Creates a new transaction to go into the next mined Block

        :param sender: <str> Address of the sender
        :param recipient: <str> Address of the recipient
        :param amount: <int> Amount
        :return: <int> The index of the block that will hold this transaction
        """

        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        })

        return self.last_block['index'] + 1

    @property
    def last_block(self):
        # Returns the last block in the chain
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 Hash of a full block

        :param block: <Dict> A block
        :return: <str> Hash
        """

        # We must make sure that the dictionary is ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def valid_chain(self, chain):
        """
        Determine if a given chain is valid

        :param chain: <list> A blockchain
        :return: <bool> True if valid, false if invalid.
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-------\n")

            # Check if the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                # If the previous_hash of the given block is not the same as
                # the hash of the last_block in the chain - return False
                return false

            # Check if the PoW is correct
            if not self.valid_proof(last_block['proof'], block['proof']):
                return false

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        This is the consensus algorithm, it resolves conflicts by replacing our chain
        with the longest one available in the network

        :return: <bool> Returns True if our chain was replaced, false OW
        """

        neighbours = self.nodes
        new_chain = None

        # We look for chains with longer length than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all other nodes in our network
        for node in neighbours:
            response in requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if the length is greater than the length of the current chain
                # Also check if the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain with the new chain, if there is one:
        if new_chain:
            self.chain = new_chain
            return True

        return False


# Instantiate our Flask node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the blockchain
blockchain = Blockchain()

@app.route('/mine', methods=['GET'])
def mine():
    # We run the proof of algorithm to get the next proof...
    lastblock = blockchain.last_block
    last_proof = lastblock['proof']
    proof = blockchain.proof_of_work(last_proof)

    # We must recieve an award for finding the proof.
    # The sender is "0" to signify that this node has mined a new coin.
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1
    )

    # Forge the new block by adding it to the chain
    previous_hash = blockchain.hash(blockchain.last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_has': block['previous_hash'],
    }
    return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount']

    if not all(k in values for k in required):
        return 'Missing Values', 400

    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message' : f'Transaction will be added to Block {index}' }
    return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def full_blockchain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response)


@app.route('/nodes/register', methods=["POST"])
def new_node():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201

@app.route('/nodes/resolve', methods=['GET'])
def find_consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Your chain was replaced',
            'new_chain': blockchain.chain
        }

    else:
        response = {
            'message': 'Your chain is authoritative - Chain replacement unnecessary',
            'chain': blockchain.chain
        }

    return jsonify(response), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)
