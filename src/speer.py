import socket

# Constants
SERVER_IP = '127.0.0.1'
SERVER_PORT = 65432
BUFFER_SIZE = 1024
WALLET_ID = "sample_wallet_id"  # For example, you can change this to any other string or get it dynamically

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((SERVER_IP, SERVER_PORT))

# Send the wallet ID
client.send(WALLET_ID.encode('utf-8'))

# Wait for the server's message
response = client.recv(BUFFER_SIZE).decode('utf-8')
print(response)
