import asyncio
from chain import create_db, update_balance, get_wallet_balance

async def find_and_add_balance(new_bal, wallet_id):
    bal0 = await get_wallet_balance(wallet_id)
    if bal0 is not None:
        balance =  bal0 + new_bal
        await update_balance(wallet_id, balance)
    else:
        print("Not enough funds")


async def find_and_minus_balance(new_bal, wallet_id):
    bal0 = await get_wallet_balance(wallet_id)
    
    if bal0 is not None:
        if new_bal > bal0:
            print("Not enough funds")
        else:
            balance = bal0 - new_bal
            await update_balance(wallet_id, balance)
    else:
        print("Error fetching balance or balance does not exist for the given wallet_id.")


# async def Inode_registration(wallet_id, amount):
    


async def mainFun():
    await create_db("hello")
    # await find_and_add_balance(215000, "cc93416f3e5e07cd1acc7da7c29dd54c3e482132b1c84f34057f9d98c5b0cd660a35eed975544c5f9819e0d00ec4d869a474439b8174e0fb4e17025d658a7295")
    # await find_and_minus_balance(215000, "cc93416f3e5e07cd1acc7da7c29dd54c3e482132b1c84f34057f9d98c5b0cd660a35eed975544c5f9819e0d00ec4d869a474439b8174e0fb4e17025d658a7295")


asyncio.run(mainFun())