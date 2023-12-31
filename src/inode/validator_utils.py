import requests
import json
import threading
import time
import redis
from datetime import datetime
import random
import config


# Redis connection
r = redis.Redis(host="localhost", port=6379, db=0)

# Constants for API and Timing
API_URL = "http://127.0.0.1:5501/src/inode/val.json"  # Replace with actual API endpoint
UPDATE_INTERVAL_VALIDATORS = 86400  # 24 hours in seconds
UPDATE_INTERVAL_BALANCE = 60  # 60 seconds


def get_percentage(wallet_address):
    try:
        # Fetch details for the specific wallet address
        details = r.hget("validators_list", wallet_address)

        if details is None:
            return "Wallet address not found in validators list."

        # Decode and load details
        details = json.loads(details.decode("utf-8"))

        # Fetch and return the "percentage" field
        return details.get("percentage", "Percentage field not found.")

    except redis.RedisError as e:
        # Handle Redis-specific errors
        return f"Redis error: {e}"

    except Exception as e:
        # Handle other possible errors
        return f"Error: {e}"


# Function to fetch validators from the API
def fetch_validators(validators):
    try:
        response = requests.get(validators)
        response.raise_for_status()  # This will raise an exception for HTTP errors

        return response.json()
    except requests.exceptions.HTTPError as errh:
        print("Http Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        print("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        print("OOps: Something Else", err)
    return []


def update_validators_list():
    try:
        validator_data = fetch_validators(config.VALIDATORS)
        total_stake_all_validators = sum(
            validator.get("totalStake", 0) for validator in validator_data[:60]
        )
        for validator in validator_data[:60]:  # Limit to top 60 validators
            wallet_address = validator.get("wallet_address")
            vote = validator.get("vote", {}).get(config.INODE, 0)
            totalStake = validator.get("totalStake")

            # Initialize or update validator details
            validator_details = r.hget("validators_list", wallet_address)
            if validator_details:
                details = json.loads(validator_details)
            else:
                details = {
                    "balance": 0,
                    "score": 0,
                    "ping": 0,
                    "ip": 0,
                    "port": 0,
                    "vote": vote,
                    "totalStake": totalStake,
                }

            details["vote"] = vote
            details["totalStake"] = totalStake
            if total_stake_all_validators > 0:  # Prevent division by zero
                percentage_stake = round(
                    (totalStake / total_stake_all_validators) * 100, 2
                )
                details["percentage"] = percentage_stake
            r.hset("validators_list", wallet_address, json.dumps(details))
    except Exception as e:
        print(f"An error occurred: {e}")


def fetch_miners(miners):
    try:
        response = requests.get(miners)
        if response.status_code == 200:
            return response.json()
        else:
            print("Failed to fetch Miners")
            return []
    except requests.RequestException as e:
        print(f"Error fetching miners: {e}")
        return []


def update_miners_list():
    try:
        miners_data = fetch_miners(config.MINERS)

        # Get the list of current top 12 miners' wallet addresses
        new_miner_addresses = set(
            miner.get("wallet_address") for miner in miners_data[:12]
        )

        # Get the existing miners from Redis
        existing_miners = r.hkeys("miners_list")
        existing_miner_addresses = set(
            miner.decode("utf-8") for miner in existing_miners
        )

        # Remove miners that are no longer in the top 12
        miners_to_remove = existing_miner_addresses - new_miner_addresses
        for miner_address in miners_to_remove:
            r.hdel("miners_list", miner_address)

        # Update or add new miners
        for miner in miners_data[:12]:
            wallet_address = miner.get("wallet_address")
            r.hset("miners_list", wallet_address, json.dumps(miner))
            # print(f"Updated/Added miner details for wallet: {wallet_address}")

    except redis.RedisError as e:
        print(f"Redis operation error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def passive_miner_list():
    try:
        # Fetching current miners from miners_list
        current_miners = r.lrange("miners_list", 0, -1)  # Fetching all miners

        for miner_data in current_miners:
            miner = json.loads(miner_data)

            # Extracting the wallet address
            wallet_address = miner.get("wallet_address")

            # Adding new details
            details = {
                "balance": 0,
                "score": 0,
                "last_active_time": 0,
            }

            # Store in passive_miners database
            r.hset("passive_miners", wallet_address, json.dumps(details))

        print("Passive miners list updated")
    except Exception as e:
        print(f"An error occurred: {e}")


def last_update():
    try:
        # Fetch all validators
        all_validators = r.hgetall("validators_list")

        # Get current time
        current_time = datetime.now()

        # Iterate over each validator
        for validator, details in all_validators.items():
            # Decode the byte string into a Python dictionary
            details = json.loads(details.decode("utf-8"))

            # Fetch last active time and score
            last_active_time_str = details.get("last_active_time", None)
            score = details.get("score", 0)

            # Skip if last_active_time is None or empty
            if not last_active_time_str:
                continue

            # Convert last_active_time to datetime object
            try:
                last_active_time = datetime.fromisoformat(last_active_time_str)
            except ValueError:
                print(
                    f"Invalid date format for validator {validator.decode()}: {last_active_time_str}"
                )
                continue

            # Check if more than 3 hours have passed
            time_diff = current_time - last_active_time
            if time_diff.total_seconds() > 180:  # 3 mins
                # Set score to 0 in the database
                details["score"] = 0
                r.hset("validators_list", validator, json.dumps(details))

    except Exception as e:
        print(f"An error occurred: {e}")


# Function to update the balance of validators
def update_balance(total_tokens):
    all_validators = r.hgetall("validators_list")

    # Calculate the effective stake for eligible validators and the total effective stake
    total_effective_stake = 0
    effective_stakes = {}
    for wallet_address, details in all_validators.items():
        details = json.loads(details.decode("utf-8"))
        score = details.get("score", 0)
        vote = details.get("vote", 0)
        totalStake = details.get("totalStake", 0)

        # Only consider validators with a score of 1
        if score == 1:
            # Calculate effective stake
            effective_stake = (totalStake * vote) / 10
            effective_stakes[wallet_address] = effective_stake
            total_effective_stake += effective_stake

    print("total_effective_stake", total_effective_stake)

    # Distribute rewards based on effective stake
    for wallet_address, effective_stake in effective_stakes.items():
        details = json.loads(all_validators[wallet_address])
        balance = details.get("balance", 0)

        # Compute proportion of total tokens to distribute
        proportion = (
            effective_stake / total_effective_stake if total_effective_stake > 0 else 0
        )

        # Distribute total tokens based on proportion
        tokens_to_distribute = proportion * total_tokens

        # Update balance
        new_balance = balance + tokens_to_distribute
        details["balance"] = new_balance

        print(f"Updating {wallet_address.decode()}: Balance {balance} -> {new_balance}")

        r.hset("validators_list", wallet_address, json.dumps(details))


# Function to handle periodic updates
def update_validators_periodically():
    try:
        while True:
            update_validators_list()
            update_miners_list()
            time.sleep(UPDATE_INTERVAL_VALIDATORS)
    except Exception as e:
        print(f"Error in update_validators_periodically: {e}")


def create_job():
    try:
        # Existing code for random_id and job_name
        random_id = random.randint(1000000, 9999999)
        job_name = f"jobInode{random_id}"

        # List of URLs
        urls = [
            "https://raw.githubusercontent.com/gprethesh/0/main/3/hash/hashes.csv",
            "https://raw.githubusercontent.com/gprethesh/0/main/3/hash/hashes.csv",
            "https://raw.githubusercontent.com/gprethesh/0/main/3/hash/hashes.csv",
        ]

        # Randomly select one of the URLs
        selected_url = random.choice(urls)

        # Sample wallet address and status
        wallet_address = None  # Placeholder for wallet address logic

        # Job details as a dictionary, including the selected hash
        print("Job details as a dictionary")
        job_details = {
            "jobname": job_name,
            "wallet_address": wallet_address,
            "status": "pending",
            "hash": selected_url,  # Add the selected hash here
        }

        # Serialize job details to JSON and add to the 'jobInode' list in Redis
        r.rpush("jobInode", json.dumps(job_details))

        print("New Job Created", job_name)

        return job_name
    except redis.RedisError as e:
        print(f"Redis error occurred: {e}")
    except json.JSONDecodeError as e:
        print(f"JSON serialization error: {e}")
    except requests.HTTPError as e:
        print(f"HTTP request error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def update_balance_periodically():
    try:
        while True:
            last_update()
            create_job()
            update_balance(100)
            time.sleep(UPDATE_INTERVAL_BALANCE)
    except Exception as e:
        print(f"Error in update_balance_periodically: {e}")


def start_periodic_update():
    validators_thread = threading.Thread(
        target=update_validators_periodically, daemon=True
    )
    balance_thread = threading.Thread(target=update_balance_periodically, daemon=True)
    validators_thread.start()
    balance_thread.start()
