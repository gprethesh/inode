import leveldb
import os

db = None

async def create_db(peer_id):
    global db
    dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db", peer_id)
    
    if not os.access(dir_path, os.F_OK):
        os.makedirs(dir_path, exist_ok=True)
        print(f"Created directory {dir_path}")
        
        try:
            db = leveldb.LevelDB(dir_path)
            print("Database created successfully")
        except Exception as e:
            print("Error creating or opening database:", e)
    else:
        try:
            db = leveldb.LevelDB(dir_path)
        except Exception as e:
            print("Error opening database:", e)


async def update_balance(user, amount):
    try:
        db.Put(("wallet-" + user).encode("utf-8"), str(amount).encode("utf-8"))
        print("Balance updated")
    except Exception as e:
        print(f"Failed to update balance for {user}: ", e)


async def increment_balance(user, amount):
    if amount < 0:
        print("Cannot increment by a negative amount.")
        return

    current_balance = await get_wallet_balance(user)
    if current_balance is None:
        current_balance = 0

    new_balance = current_balance + amount
    await update_balance(user, new_balance)
    return True


async def decrement_balance(user, amount):
    if amount < 0:
        print("Cannot decrement by a negative amount.")
        return False

    current_balance = await get_wallet_balance(user)
    if current_balance is None:
        print(f"User {user} does not have an existing balance.")
        return False

    if current_balance < amount:
        print(f"Insufficient funds. Cannot decrement {amount} from {current_balance}.")
        return False

    new_balance = current_balance - amount
    await update_balance(user, new_balance)
    return True


async def reg_inode(user, amount):
    # Maximum allowed inodes for a user
    MAX_INODES = 12
    
    # Check if inode is already registered for the user
    if await is_inode_registered(user):
        print(f"Inode already registered for {user}")
        return

    # Check if user has already reached the maximum inode limit
    current_inode_count = await get_inode_count(user)
    if current_inode_count >= MAX_INODES:
        print(f"{user} has already reached the maximum inode limit of {MAX_INODES}.")
        return

    # Try to decrement the balance
    if not await decrement_balance(user, amount):
        print(f"Cannot decrement balance for {user}. Inode not registered.")
        return

    # If the decrement was successful, proceed with the inode registration
    try:
        db.Put(("inode_" + user).encode("utf-8"), str(amount).encode("utf-8"))
        print("Inode Registered")
    except Exception as e:
        print(f"Failed to register inode for {user}: ", e)
        await increment_balance(user, amount)


def get_inode_count(user):
    inode_prefix = ("inode_" + user).encode("utf-8")
    
    count = 0
    for key, _ in db.RangeIter(key_from=inode_prefix):
        if key.startswith(inode_prefix):
            count += 1
        else:
            break

    return count


async def is_inode_registered(user):
    try:
        value = db.Get(("inode_" + user).encode("utf-8"))
        # If the above line does not raise an error, it means the inode exists.
        return True
    except KeyError:
        # KeyError means the inode does not exist for the user.
        return False
    except Exception as e:
        print(f"Error while checking inode for {user}: ", e)
        return False




async def get_wallet_balance(user):
    try:
        balance = db.Get(("wallet-" + user).encode("utf-8"))
        # Convert bytearray to string, remove parentheses and comma, then convert to int
        balance = int(balance.decode("utf-8").strip("(,)"))
        return balance
    except KeyError:
        return 0
    except Exception as e:
        raise e



