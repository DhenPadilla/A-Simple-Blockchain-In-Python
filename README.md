# A-Simple-Blockchain-In-Python
A simple blockchain program with localhost http requests.

- Able to register new nodes to the Blockchain network
- Able to mine blocks to store new 'transactions' within the chain
- Hashes using SHA256



--- INSTRUCTIONS TO TEST: ---
1. Clone the repo
2. CD into the directory
3. Make sure Flask and requests are installed in Python using: pip install Flask==0.12.2 requests==2.18.4 
4. run: python blockchain.py in terminal
5. Fire up Postman and make POST/GET requests using: 
  
   a) http://localhost:5000/mine (GET)
  
   b) http://localhost:5000/transactions/new (POST) - This must include a body as such:
    {
      "sender": "{some-hash}"
      "recipient": "{recipient-address}"
      "amount": {amount-to-send}
    }
  
   c) http://localhost:5000/chain (GET)
