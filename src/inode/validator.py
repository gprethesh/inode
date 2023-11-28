import socket
import json


class MessageType:
    VALIDATEMODEL = "validateModel"


def send_data_to_inode(
    job_id, miner_pool_wallet, validator_wallet, job_details, message_type
):
    # Structure data based on message type
    if message_type == MessageType.VALIDATEMODEL:
        data = {
            "type": MessageType.VALIDATEMODEL,
            "content": {
                "job_id": job_id,
                "miner_pool_wallet": miner_pool_wallet,
                "validator_wallet": validator_wallet,
                "job_details": job_details,
            },
        }
    else:
        raise ValueError("Invalid message type")

    serialized_data = json.dumps(data)

    # Constants for server connection
    SERVER_IP = "127.0.0.1"
    SERVER_PORT = 65432
    BUFFER_SIZE = 1024

    # Create a socket object
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to the server
    client.connect((SERVER_IP, SERVER_PORT))

    # Send the serialized data
    client.send(serialized_data.encode("utf-8"))

    # Wait for the server's response
    response = client.recv(BUFFER_SIZE).decode("utf-8")

    # Close the connection
    client.close()

    return response


job_id = "12345"
miner_pool_wallet = "miner_wallet_idx"
validator_wallet = "wallet1"
job_details = {"detail_key": "detail_value"}
message_type = MessageType.VALIDATEMODEL

response = send_data_to_inode(
    job_id, miner_pool_wallet, validator_wallet, job_details, message_type
)
print("Response from inode:", response)
