import zmq
import redis
import os

def load_keys():
    # Determine the absolute path to the directory containing node.py
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Form the absolute paths to the server keys
    secret_file = os.path.join(script_dir, 'server', 'server.key_secret')
    public_file = os.path.join(script_dir, 'server', 'server.key')
  
    server_public, server_secret = zmq.curve_keypair()
    with open(public_file, 'w') as pub, open(secret_file, 'w') as sec:
        pub.write(server_public.decode('utf-8'))
        sec.write(server_secret.decode('utf-8'))

    return server_public, server_secret

try:
    # ZeroMQ Context
    context = zmq.Context()

    # Load Server's Secure Keys
    server_public, server_secret = load_keys()
    
    # Setting up Secure Publisher Socket
    socket = context.socket(zmq.PUB)
    socket.curve_secretkey = server_secret
    socket.curve_publickey = server_public
    socket.curve_server = True  # must come before bind
    socket.bind("tcp://*:5555")
    
    # Redis setup
    r = redis.Redis(host='localhost', port=6379, db=0)
    
    topic = "project_broadcast"

    while True:
        project_id = input("Enter the project id to broadcast (or 'exit' to quit): ")
        
        if project_id == 'exit':
            break

        # Broadcasting the project availability
        socket.send_string(f"{topic} {project_id}")
        print(f"Broadcasted project {project_id} availability.")

        # Listening for download completion messages from peers
        receiver = context.socket(zmq.PULL)
        receiver.curve_secretkey = server_secret
        receiver.curve_publickey = server_public
        receiver.curve_server = True
        receiver.bind("tcp://*:5556")

        while True:
            message = receiver.recv_string()
            if message == "done":
                break
            peer_info, downloaded_project_id = message.split()
            
            # Store the peer info and project id in Redis
            r.sadd(downloaded_project_id, peer_info)

        receiver.close()

    socket.close()

except Exception as e:
    print(f"An error occurred: {e}")

