import os
import json
import binascii
import ecdsa

ec = ecdsa.SECP256k1

balances = {}

keys_dir = os.path.join(os.path.dirname(__file__), "wallet")
keys_file = os.path.join(keys_dir, "keys.json")

def init_wallet():
    global balances
    if not os.path.exists(keys_dir):
        os.mkdir(keys_dir)

    if os.path.exists(keys_file):
        with open(keys_file, "r") as f:
            keys = json.load(f)
    else:
        private_key = generate_private_key()
        sk = ecdsa.SigningKey.from_string(binascii.unhexlify(private_key), curve=ec)
        vk = sk.get_verifying_key()
        public_key = binascii.hexlify(vk.to_string()).decode()

        keys = {
            "privateKey": private_key,
            "publicKey": public_key
        }

        with open(keys_file, "w") as f:
            json.dump(keys, f)

    return keys

def generate_private_key():
    return binascii.hexlify(ecdsa.SigningKey.generate(curve=ec).to_string()).decode()

# Initialize wallet
keys = init_wallet()
print(json.dumps(keys))