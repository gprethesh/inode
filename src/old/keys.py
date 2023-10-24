import os
import zmq

def generate_keys(base_dir, name):
    """Generate a pair of public and private keys and store them in the specified directory."""
    public_key, private_key = zmq.curve_keypair()
    
    # Ensure the base directory exists
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    # Save public key
    with open(os.path.join(base_dir, f"{name}.key"), 'w') as public_file:
        public_file.write(public_key.decode('utf-8'))

    # Save private key ONLY (no need to store public key here)
    with open(os.path.join(base_dir, f"{name}.key_secret"), 'w') as secret_file:
        secret_file.write(private_key.decode('utf-8'))

# Generate server keys
generate_keys("server", "server")

# Generate client keys
generate_keys("client", "client")

print("Keys generated and stored successfully!")
