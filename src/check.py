import asyncio

# Assuming create_db and get_wallet_balance are defined somewhere else
from chain import create_db, get_wallet_balance

async def bal():
    await create_db("hello")
    bal1 = await get_wallet_balance("cc93416f3e5e07cd1acc7da7c29dd54c3e482132b1c84f34057f9d98c5b0cd660a35eed975544c5f9819e0d00ec4d869a474439b8174e0fb4e17025d658a7295")
    bal2 = await get_wallet_balance("a8c2b097c5fbbfc2953090a56687b6aaa51b07946768deccacc5ba51890474afcdac4c602b09451ecc16a48f1ddf31bd89c8855d8010b8b11431d547d3a0bf79")
    bal3 = await get_wallet_balance("04a8bc99fdb9c5f8a2c1b1a6660ea96ba233317901a9927544c23de6a1926f3c8ffdb37e9ca7b3c8858289209cdea8fb6ff1b15daf7d508b0c859e0e9fea11f508")
    Miner = await get_wallet_balance("04c590a6b268f13a042e1b0f9c52f291db78f042659ad257a39fead537452b6657d161b988cd5b90b29c16192ecc139ff48b181c7b99555514d6ec375308c19bbd")

    print(f"GENESIS WALLET: {bal1}")
    print(f"USER: {bal2}")
    print(f"2ND USER: {bal3}")
    print(f"Miner: {Miner}")

# Run the async function
asyncio.run(bal())
