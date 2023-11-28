import redis


# Initialize Redis client
r = redis.Redis(host="localhost", port=6379, db=0)


def set_last_block_height(block_height):
    r.set("last_block_height", block_height)


def get_last_block_height():
    return int(r.get("last_block_height") or 0)


def set_current_block_height(block_height):
    r.set("current_block_height", block_height)


def get_current_block_height():
    return int(r.get("current_block_height") or 0)


def set_inode_emission(emission):
    r.set("inode_emission", emission)


def get_inode_emission():
    return float(r.get("inode_emission") or 0.0)
