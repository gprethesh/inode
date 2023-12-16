import socket
import json
import asyncio
import websockets
from websockets.exceptions import WebSocketException
import config
import logging
from datetime import datetime


logging.basicConfig(level=logging.INFO)


class MessageType:
    VALIDATEMODEL = "validateModel"
    UPDATEINFO = "updateInfo"
    SETCONFIG = "setConfig"
    UPDATEMODEL = "updateModel"


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


# job_id = "2988473"
# miner_pool_wallet = "miner_wallet_idx"
# validator_wallet = "wallet1"
# job_details = {"detail_key": "detail_value"}
# message_type = MessageType.VALIDATEMODEL


# response = send_data_to_inode(
#     job_id, miner_pool_wallet, validator_wallet, job_details, message_type
# )
# print("Response from inode:", response)


def send_update_info(ip, port, wallet_address, message_type):
    current_time = datetime.now().isoformat()

    # Structure data based on message type
    if message_type == MessageType.SETCONFIG:
        data = {
            "type": MessageType.SETCONFIG,
            "content": {
                "ip": ip,
                "port": port,
                "ping": current_time,
                "wallet_address": wallet_address,
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

    print("ResponseXXXXX", response)

    # Close the connection
    client.close()

    return response


async def handle_client(websocket, path):
    try:
        async for message in websocket:
            try:
                parsed_message = json.loads(message)
                message_type = parsed_message.get("type")

                if message_type == "validateModel":
                    # Extract data from message
                    job_id = parsed_message.get("job_id")
                    miner_pool_wallet = parsed_message.get("miner_pool_wallet")
                    validator_wallet = parsed_message.get("validator_wallet")
                    job_details = parsed_message.get("job_details")

                    # Prepare and send response
                    message_to_send = json.dumps(
                        {
                            "job_id": job_id,
                            "validator_wallet": validator_wallet,
                            "type": MessageType.UPDATEMODEL,
                        }
                    )
                    response = send_data_to_inode(
                        job_id,
                        miner_pool_wallet,
                        validator_wallet,
                        job_details,
                        message_type,
                    )

                    await websocket.send(message_to_send)
                    logging.info(f"Response: {response}")

            except json.JSONDecodeError:
                await websocket.send("Invalid message format")
            except Exception as e:
                logging.error(f"Error processing message: {e}")
                await websocket.send("Error processing message")

    except WebSocketException as e:
        logging.warning(f"WebSocket error: {e}")
    except asyncio.CancelledError:
        logging.info("Client connection handling cancelled.")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    finally:
        logging.info("Client disconnected or connection handling stopped.")


async def periodic_update():
    while True:
        send_update_info(
            config.IP,
            config.PORT,
            config.VALIDATOR_WALLET_ADDRESS,
            MessageType.SETCONFIG,
        )
        print("Validator ping")
        await asyncio.sleep(60)


async def main():
    # Start the periodic update task
    update_task = asyncio.create_task(periodic_update())

    stop = asyncio.Future()

    server = await websockets.serve(handle_client, config.IP, config.PORT)

    await stop
    server.close()
    await server.wait_closed()
    logging.info("Server shut down successfully.")

    # Cancel the periodic update task
    update_task.cancel()
    try:
        await update_task
    except asyncio.CancelledError:
        logging.info("Periodic update task cancelled.")


try:
    asyncio.run(main())
except KeyboardInterrupt:
    logging.info("Received keyboard interrupt. Shutting down...")
