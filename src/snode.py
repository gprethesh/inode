import socket
import threading
import redis

# Constants
IP = socket.gethostbyname(socket.gethostname())
PORT = 65432
BUFFER_SIZE = 1024

# Connect to Redis
r = redis.Redis(host=IP, port=6379, db=0)

def handle_client(client_socket, client_address):
    try:
        # Receive wallet ID from the peer
        wallet_id = client_socket.recv(BUFFER_SIZE).decode('utf-8')
        
        print("client_address", client_address)
        # Create entry in Redis
        r.hset(wallet_id, "ProjectID", "0")
        r.hset(wallet_id, "Data", "chunck0.zip")
        r.hset(wallet_id, "Status", "Download")
        r.hset(wallet_id, "client_address", "ok")
        
        
        # Wait for some time (you can adjust this) and then send a message
        # In a real-world scenario, you might want to use a more dynamic approach
        # but for the sake of this example, we're using sleep
        import time
        time.sleep(5)
        
        client_socket.send("chunck0.zip".encode('utf-8'))
    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        client_socket.close()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((IP, PORT))
server.listen(5)

print(f"Server started on {IP}:{PORT}")

while True:
    client_socket, client_address = server.accept()
    client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address))
    client_handler.start()
