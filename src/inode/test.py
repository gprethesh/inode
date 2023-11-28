import time
import api_client
import redis_client
import config


def update_balance():
    # Implement the logic to update balance
    print("Update Balance")
    pass


def base():
    # Initial check for emission when the server starts
    try:
        emission = api_client.get_dobby_emission(config.INODE_WALLET_ADDRESS)
        redis_client.set_inode_emission(emission)
    except Exception as e:
        print(f"Error getting initial emission from Dobby API: {e}")
        # Handle the error appropriately (e.g., retry, exit, etc.)

    while True:
        try:
            current_block_height = api_client.get_current_block_height()
            redis_client.set_current_block_height(current_block_height)
            print("Awarding validators")
        except Exception as e:
            print(f"Error getting current block height: {e}")
            time.sleep(config.CHECK_INTERVAL)
            continue

        # current_time = time.time()
        emission = redis_client.get_inode_emission()

        if emission > 0:
            try:
                last_block_height = redis_client.get_last_block_height()
            except Exception as e:
                print(f"Error getting last block height from Redis: {e}")

            for block_height in range(last_block_height + 1, current_block_height + 1):
                try:
                    transactions = api_client.get_coinbase_transactions(block_height)
                    print(f"[{block_height}] Transactions: {transactions}")
                except Exception as e:
                    print(f"Error getting coinbase transactions: {e}")
                    continue

                for tx in transactions:
                    try:
                        if config.INODE_WALLET_ADDRESS in tx:  # Assuming tx is a dict
                            update_balance()
                    except Exception as e:
                        print(f"Error in transaction processing: {e}")

                try:
                    redis_client.set_last_block_height(block_height)
                    print(f"Updated last block height to: {block_height}")
                except Exception as e:
                    print(f"Error updating last block height in Redis: {e}")

        time.sleep(config.CHECK_INTERVAL)


base()
