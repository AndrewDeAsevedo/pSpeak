import crypto
import nat
import json
import sys
import socket
import time

from websockets.sync.client import connect
from websockets.exceptions import ConnectionClosedOK

# TODO: move this to .env and put homelab address
SIGNALLING_SERVER = "ws://localhost:8765"


def main(args):
    keys = crypto.KeyGenerator()
    public_key_hex = keys.public_key.public_bytes_raw().hex()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        sock.bind(("0.0.0.0", 0))

        # 1. Discover my public IP via STUN and opening UDP port
        my_ip, my_port = nat.get_public_ip_stun(sock)

        # 2. Connect to signaling server and exchange IP + Keys
        data_to_transfer = {
            "ip": str(my_ip),
            "port": my_port,
            "publicKey": public_key_hex,
        }

        # TODO: this probably wont just be an args check
        # if creating the room
        if args == "1":
            payload = create_signal_room(data_to_transfer)
        # if joining the room
        elif args == "2":
            room_code = input("\nWhat is your roomcode? ")
            payload = connect_to_signal_room(data_to_transfer, room_code)

        peer_addr = (payload["ip"], payload["port"])

        # 4. Start UDP hole punch
        print(f"Punching hole to {peer_addr}")
        for _ in range(5):
            sock.sendto(b"PUNCH", peer_addr)
            time.sleep(0.1)

        sock.settimeout(5)
        try:
            data, addr = sock.recvfrom(1024)
            if data == b"PUNCH":
                print(f"Hole punch successful! Direct path to {addr}")
                # Now communicate directly
                sock.sendto(b"Hello directly!", peer_addr)
                data, _ = sock.recvfrom(1024)
                print(f"Received: {data.decode()}")
        except socket.timeout:
            print("Hole punch failed - symmetric NAT or firewall blocking")

        # 5. Once connected, encrypt and send/receive messages
    finally:
        sock.close()

    return


def create_signal_room(string_to_transfer):
    message = None
    with connect(SIGNALLING_SERVER) as websocket:
        websocket.send(json.dumps({"action": "create", "data": string_to_transfer}))

        # await until message recieved
        while True:
            try:
                message = json.loads(websocket.recv())
                print(f"Received: {message}")
                if message["event"] == "peer_joined":
                    payload = message["data"]
            except ConnectionClosedOK:
                print("Server closed connection. Transfer complete.")
                break

        return payload


def connect_to_signal_room(string_to_transfer, room_code):
    message = None
    with connect(SIGNALLING_SERVER) as websocket:
        websocket.send(
            json.dumps(
                {"action": "join", "room": room_code, "data": string_to_transfer}
            )
        )

        # await until message recieved
        while True:
            try:
                message = json.loads(websocket.recv())
                print(f"Received: {message}")
                if message["event"] == "peer_joined":
                    payload = message["data"]
            except ConnectionClosedOK:
                print("Server closed connection. Transfer complete.")
                break

    return payload


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("\n-------------ERROR: missing args-------------")
