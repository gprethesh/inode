import socket
import threading
import redis
import json
from datetime import datetime
import random
import signal
import sys
import logging
import requests
import config


from validator_utils import start_periodic_update


class MessageType:
    VALIDATEMODEL = "validateModel"
    REQUESTJOB = "requestJob"


# Constants
IP = socket.gethostbyname(socket.gethostname())
PORT = 65432
BUFFER_SIZE = 1024

# Connect to Redis
r = redis.Redis(host="localhost", port=6379, db=0)

# Dictionary with wallet addresses and their associated percentages
valid_wallet_addresses = {
    "wallet1": 20,
    "wallet2": 30,
    "wallet3": 2.22,
    "wallet4": 50,
    "wallet5": 100,
}

logging.basicConfig(
    level=logging.INFO, format=" %(asctime)s %(levelname)s:%(message)s "
)


def create_job():
    # Generate a 7-digit random ID
    random_id = random.randint(1000000, 9999999)
    job_name = f"jobInode{random_id}"

    # Sample wallet address and status
    wallet_address = (
        None  # You can replace this with actual wallet address generation logic
    )
    status = "pending"

    # Job details as a dictionary
    job_details = {
        "jobname": job_name,
        "wallet_address": wallet_address,
        "status": status,
    }

    # Serialize job details to JSON and add to the 'jobInode' list in Redis
    r.rpush("jobInode", json.dumps(job_details))

    return job_name


def job_processed(data):
    content = data.get("content", {})
    print("data", data)

    wallet_address = content.get("wallet_id")

    # Retrieve the list named 'jobInode' from Redis
    job_inode_list = r.lrange("jobInode", 0, -1)

    # Convert byte strings to Python dictionaries
    job_inode_list = [json.loads(job.decode("utf-8")) for job in job_inode_list]

    # Iterate through jobs to perform updates and deletions
    index = 0
    while index < len(job_inode_list):
        job = job_inode_list[index]

        # Delete jobs with status 'complete'
        if job["status"] == "complete":
            r.lrem("jobInode", 0, json.dumps(job))
            print(f"Deleted completed job: {job['jobname']}")
            job_inode_list.pop(index)
            # Continue to next iteration without incrementing index
            continue

        # Update the first job with a null wallet address
        elif job["wallet_address"] is None:
            job["wallet_address"] = wallet_address
            r.lset("jobInode", index, json.dumps(job))
            print(
                f"Updated job: {job['jobname']} with wallet address: {wallet_address}"
            )
            return job["jobname"]  # Return the job name of the updated job

        index += 1
    else:
        print("No job with null wallet address found.")
        return None  # Return None if no job is updated


def handle_client(client_socket, client_address):
    try:
        # Constants for server connection
        BUFFER_SIZE = 1024

        # Receive data from client
        data = client_socket.recv(BUFFER_SIZE).decode("utf-8")
        data = json.loads(data)

        # Determine action based on message type
        if data.get("type") == MessageType.VALIDATEMODEL:
            validator_(client_socket, data)
        elif data.get("type") == MessageType.REQUESTJOB:
            job_name = job_processed(data)
            if job_name:
                response_message = job_name  # Send job name as response

            else:
                response_message = "No job updated"

        else:
            raise ValueError("Unknown message type")

        # response_messageX = "Data processed successfullyX"

        client_socket.send(response_message.encode("utf-8"))

    except Exception as e:
        print(f"Error handling client: {e}")
        client_socket.send(f"Error: {str(e)}".encode("utf-8"))
    finally:
        client_socket.close()


def validator_(client_socket, data):
    # Extract data from client's message
    content = data.get("content", {})
    print("data", data)

    job_id = content.get("job_id")
    miner_pool_wallet = content.get("miner_pool_wallet")
    validator_wallet = content.get("validator_wallet")
    job_details = content.get("job_details")

    # Check if the validator wallet is valid and get its percentage
    validator_percentage = valid_wallet_addresses.get(validator_wallet)
    if validator_percentage is None:
        client_socket.send("Invalid validator wallet".encode("utf-8"))
        return

    # Check if the validator wallet exists in the database
    validator_details = r.hget("validators_list", validator_wallet)
    if validator_details:
        details = json.loads(validator_details)
    else:
        client_socket.send("Validator wallet not found".encode("utf-8"))
        return

    # Create or update job entry
    if not r.hexists(f"job_{job_id}", "miner_pool_wallet"):
        r.hset(f"job_{job_id}", "miner_pool_wallet", miner_pool_wallet)
        r.hset(f"job_{job_id}", "job_details", json.dumps(job_details))
        r.hset(f"job_{job_id}", "status", "processing")
        r.hset(f"job_{job_id}", "percentage", 0)  # Initialize percentage to 0
        r.hset(
            f"job_{job_id}", "validators", json.dumps([])
        )  # Initialize validators list

    # Check current percentage and validators list
    current_percentage = float(r.hget(f"job_{job_id}", "percentage") or 0)
    existing_validators = json.loads(r.hget(f"job_{job_id}", "validators") or "[]")

    if current_percentage < 100:
        if validator_wallet not in existing_validators:
            # Add validator wallet and update percentage
            existing_validators.append(validator_wallet)
            r.hset(f"job_{job_id}", "validators", json.dumps(existing_validators))

            new_percentage = min(current_percentage + validator_percentage, 100)
            r.hset(f"job_{job_id}", "percentage", new_percentage)

            # Update score and last active time for the validator
            details["score"] = 1
            details["last_active_time"] = datetime.now().isoformat()
            r.hset("validators_list", validator_wallet, json.dumps(details))

            # Check if the job is now completed
            if new_percentage == 100:
                r.hset(f"job_{job_id}", "status", "completed")
        else:
            client_socket.send(
                "Validator has already validated this job".encode("utf-8")
            )
            return
    else:
        client_socket.send("Job has reached maximum percentage".encode("utf-8"))
        return


def signal_handler(sig, frame):
    logging.info(" Shutting down the server...")
    sys.exit(0)


def start_server(IP, PORT):
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((IP, PORT))
        server.listen(5)
        logging.info(f" Server started on {IP}:{PORT}")
        # create_job()

        # Start the periodic update thread here, outside the while loop
        start_periodic_update()

        while True:
            client_socket, client_address = server.accept()
            logging.info(f" Accepted connection from {client_address}")
            client_handler = threading.Thread(
                target=handle_client, args=(client_socket, client_address)
            )
            client_handler.start()

    except Exception as e:
        logging.error(f" An error occurred: {e}")
    finally:
        server.close()
        logging.info(" Server closed.")


# Start the server
start_server(IP, PORT)
