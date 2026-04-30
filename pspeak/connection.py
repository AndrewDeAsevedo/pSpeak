import crypto
import nat
import json
import sys

from websockets.sync.client import connect

# TODO: move this to .env and put homelab address
SIGNALLING_SERVER = "ws://localhost:8765"


def main(args):
    keys = crypto.KeyGenerator()
    public_key = keys.public_key

    # 1. Discover my public IP via STUN
    my_ip, my_port = nat.get_public_address()

    # 2. Connect to signaling server and exchange IP + Keys
    string_to_transfer = str(my_ip) + ":" + str(my_port) + str(public_key)

    if args == "1":
        create_signal_room(string_to_transfer)
    elif args == "2":
        room_code = input("\nWhat is your roomcode? ")
        connect_to_signal_room(string_to_transfer, room_code)

    return
    # 4. Start UDP hole punch
    # 5. Once connected, encrypt and send/receive messages


def create_signal_room(string_to_transfer):
    message = None
    with connect(SIGNALLING_SERVER) as websocket:
        websocket.send(json.dumps({"action": "create", "data": string_to_transfer}))
        # await until message recieved
        while True:
            message = websocket.recv()
            print(f"Recived: {message}")

        return


def connect_to_signal_room(string_to_transfer, room_code):
    message = None
    with connect(SIGNALLING_SERVER) as websocket:
        websocket.send(
            json.dumps(
                {"action": "join", "room": room_code, "data": string_to_transfer}
            )
        )
        # await until message recieved
        print("Awaiting reply")

        while not message:
            message = websocket.recv()

        print(f"Received: {message}")

    return


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
