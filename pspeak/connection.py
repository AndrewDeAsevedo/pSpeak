import crypto
import nat
import protocol
import json
import sys
import socket
import time
import threading
import os

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey
from websockets.sync.client import connect
from websockets.exceptions import ConnectionClosedOK
from dotenv import load_dotenv

load_dotenv()
SIGNALLING_SERVER = os.getenv("SIGNALLING_SERVER")


def main(args, local=False):
    keys = crypto.KeyGenerator()
    public_key_hex = keys.public_key.public_bytes_raw().hex()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        sock.bind(("0.0.0.0", 0))

        # 1. Discover my address
        if local:
            my_ip = "127.0.0.1"
            my_port = sock.getsockname()[1]
            print(f"Local mode: {my_ip}:{my_port}")
        else:
            my_ip, my_port = nat.get_public_ip_stun(sock)

        # 2. Connect to signaling server and exchange IP + Keys
        data_to_transfer = {
            "ip": str(my_ip),
            "port": my_port,
            "publicKey": public_key_hex,
        }

        # if creating the room
        if args == "1":
            payload = create_signal_room(data_to_transfer)
        # if joining the room
        elif args == "2":
            room_code = input("\nWhat is your roomcode? ")
            payload = connect_to_signal_room(data_to_transfer, room_code)

        peer_addr = (payload["ip"], payload["port"])

        # 3. Derive shared encryption key from peer's public key
        peer_public_key = X25519PublicKey.from_public_bytes(
            bytes.fromhex(payload["publicKey"])
        )
        shared_key = crypto.createSharedKey(keys.private_key, peer_public_key)

        # Creator gets even nonces (0, 2, 4...), joiner gets odd (1, 3, 5...)
        my_nonce = 0 if args == "1" else 1
        encryptor = crypto.Encryptor(shared_key, my_nonce)
        decryptor = crypto.Encryptor(shared_key, 0)

        if not local:
            # 4. Start UDP hole punch (skip on localhost)
            print(f"Punching hole to {peer_addr}")
            for _ in range(10):
                sock.sendto(b"PUNCH", peer_addr)
                time.sleep(0.3)

            sock.settimeout(5)
            try:
                data, addr = sock.recvfrom(1024)
                print(f"Hole punch successful! Connected to {addr}")
            except socket.timeout:
                print("Hole punch failed - symmetric NAT or firewall blocking")
                return
        else:
            print(f"Connected to peer at {peer_addr}")

        # 5. Encrypted chat loop
        print(
            "\n--- Chat started. Type messages and press Enter. Ctrl+C to quit. ---\n"
        )
        sock.settimeout(0.5)

        # Receiver thread: listens for incoming UDP, decrypts, prints
        running = True

        def receive_loop():
            while running:
                try:
                    data, addr = sock.recvfrom(4096)
                    if data == b"PUNCH":
                        continue
                    _, msg_type, encrypted_payload = protocol.unpack(data)

                    if msg_type == protocol.MsgType.MSG:
                        plaintext = decryptor.decrypt(encrypted_payload)
                        print(f"\n  Peer: {plaintext.decode()}")
                    elif msg_type == protocol.MsgType.BYE:
                        print("\n  Peer disconnected.")
                        break
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"\n  Error receiving: {e}")
                    break

        recv_thread = threading.Thread(target=receive_loop, daemon=True)
        recv_thread.start()

        # Main thread: reads input, encrypts, sends
        try:
            while True:
                text = input()
                if text.lower() in ("/quit", "/exit"):
                    bye_packet = protocol.pack(protocol.MsgType.BYE, b"")
                    sock.sendto(bye_packet, peer_addr)
                    break
                encrypted = encryptor.encrypt(text.encode())
                packet = protocol.pack(protocol.MsgType.MSG, encrypted)
                sock.sendto(packet, peer_addr)
        except KeyboardInterrupt:
            bye_packet = protocol.pack(protocol.MsgType.BYE, b"")
            sock.sendto(bye_packet, peer_addr)
            print("\nDisconnected.")

        running = False

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
    if len(sys.argv) < 2:
        print("\n-------------ERROR: missing args-------------")
        print("Usage: python3 connection.py <1|2> [--local]")
        sys.exit(1)
    local_mode = "--local" in sys.argv
    main(sys.argv[1], local=local_mode)
