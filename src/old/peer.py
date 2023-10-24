import zmq
import time
import os

def load_keys():
    # Manually load client's public and secret keys
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    # Correct the path generation
    secret_file_path = os.path.join(base_path, 'client', 'client.key_secret')
    public_file_path = os.path.join(base_path, 'client', 'client.key')
    server_public_file_path = os.path.join(base_path, 'server', 'server.key')
    
    # Read the keys from the files and strip any whitespace
    with open(secret_file_path, 'r') as sec, open(public_file_path, 'r') as pub, open(server_public_file_path, 'r') as serv_pub:
        client_secret = sec.read().strip().encode('utf-8')
        client_public = pub.read().strip().encode('utf-8')
        server_public = serv_pub.read().strip().encode('utf-8')

    return client_public, client_secret, server_public


try:
    # ZeroMQ Context
    context = zmq.Context()

    # Load keys
    client_public, client_secret, server_public = load_keys()
    
    # Debug prints for keys
    print(f"Client Public Key: {client_public}")
    print(f"Client Secret Key: {client_secret}")
    print(f"Server Public Key: {server_public}")

    # Setting up Secure Subscriber Socket
    socket = context.socket(zmq.SUB)
    socket.curve_secretkey = client_secret
    socket.curve_publickey = client_public
    socket.curve_serverkey = server_public
    socket.connect("tcp://localhost:5555")

    # Subscribe to the topic
    topic = "project_broadcast"
    socket.setsockopt_string(zmq.SUBSCRIBE, topic)

    print("Waiting for project broadcasts...")

    while True:
        message = socket.recv_string()
        _, project_id = message.split()
        print(f"Received project {project_id} availability.")

        # Simulate downloading 
        print(f"Downloading project {project_id}...")
        time.sleep(5)  # Simulating download delay
        print(f"Downloaded project {project_id}")

        # Inform the main server of the download completion
        notifier = context.socket(zmq.PUSH)
        notifier.curve_secretkey = client_secret
        notifier.curve_publickey = client_public
        notifier.curve_serverkey = server_public
        notifier.connect("tcp://localhost:5556")
        
        peer_info = "peer_ip:port"  # Replace with actual peer info
        notifier.send_string(f"{peer_info} {project_id}")

        notifier.close()

except Exception as e:
    print(f"An error occurred: {e}")
