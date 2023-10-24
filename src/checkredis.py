import redis

# Connect to Redis
r = redis.Redis(host='127.0.0.1', port=6379, db=0)

# Wallet ID to query
wallet_id = "sample_wallet_id"

# Get all fields and their values for the given wallet ID
data = r.hgetall(wallet_id)

# Convert byte keys and values to strings
data = {k.decode('utf-8'): v.decode('utf-8') for k, v in data.items()}

print(data)
