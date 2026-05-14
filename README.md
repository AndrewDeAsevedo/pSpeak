# pSpeak

A peer-to-peer encrypted terminal chat. Two users connect directly over UDP — no server in the middle during the conversation. A lightweight signaling server brokers introductions via room codes, then gets out of the way.

**Status:** WIP — local encrypted chat works, internet NAT traversal in progress.

## Installation

**Signaling server (Node.js):**

```bash
cd server
npm install
```

**Client (Python 3.12+):**

```bash
cd pspeak
python3 -m venv venv
source venv/bin/activate
pip install cryptography websockets
```

## How to Use

### 1. Start the signaling server

```bash
cd server
node server.js
```

The server runs on `ws://localhost:8765` by default.

### 2. Peer A — Create a room

```bash
cd pspeak
source venv/bin/activate
python3 connection.py 1 --local
```

A room code like `alpha-bravo-charlie` will appear. Share it with your peer.

### 3. Peer B — Join the room

```bash
cd pspeak
source venv/bin/activate
python3 connection.py 2 --local
```

Enter the room code when prompted.

### 4. Chat

Type messages and press Enter. They're encrypted end-to-end before leaving your machine. Type `/quit` or press Ctrl+C to disconnect.

> Use `--local` for same-machine testing (skips STUN and hole punching). Omit it when connecting over the internet.

## Architecture

```
┌──────────┐       WebSocket        ┌──────────────────┐       WebSocket        ┌──────────┐
│  Peer A  │ ──── (room code) ────> │ Signaling Server │ <──── (room code) ──── │  Peer B  │
└──────────┘   exchange IP + keys   └──────────────────┘   exchange IP + keys   └──────────┘
     │                                                                                │
     │                         Server disconnects. Done.                              │
     │                                                                                │
     └──────────────── Direct encrypted UDP (after hole punch) ──────────────────────┘
```

### Project Structure


| File                   | Purpose                                                                 |
| ---------------------- | ----------------------------------------------------------------------- |
| `server/server.js`     | WebSocket signaling server — room codes, peer info swap, auto-close     |
| `pspeak/crypto.py`     | X25519 key exchange, HKDF key derivation, AES-256-GCM encrypt/decrypt   |
| `pspeak/protocol.py`   | Binary message framing — length prefix + message type + payload         |
| `pspeak/nat.py`        | Manual STUN binding request to discover public IP:port                  |
| `pspeak/connection.py` | Ties it all together — STUN, signaling, hole punch, encrypted chat loop |


### How It Works

1. **Key generation** — Each peer generates an X25519 keypair at startup
2. **STUN** — Each peer discovers their public IP:port by sending a binding request to Google's STUN server. The request is sent on the same UDP socket used for chat, so the NAT mapping stays valid
3. **Signaling** — Both peers connect to the signaling server via WebSocket. Peer A creates a room (gets a NATO phonetic room code), Peer B joins it. The server swaps their IP, port, and public key, then closes both connections
4. **Key exchange** — Each peer combines their private key with the other's public key (X25519 Diffie-Hellman) to derive the same shared secret, then runs it through HKDF. Neither side ever sends the shared secret over the network
5. **Hole punch** — Both peers send UDP packets to each other's public address to create NAT mappings that allow return traffic through
6. **Chat** — Messages are encrypted with AES-256-GCM using the shared secret, wrapped in a binary protocol frame (4-byte length + 1-byte type + payload), and sent directly over UDP. A receiver thread decrypts and prints incoming messages while the main thread handles input

## Development

This is a self-taught learning project. The goal was to understand P2P networking, NAT traversal, and cryptographic key exchange by building them from scratch rather than using high-level abstractions.

Things I learned building this:

- Why P2P over the internet is hard (NAT blocks unsolicited incoming traffic)
- How STUN works at the byte level (20-byte binding request, XOR-MAPPED-ADDRESS parsing)
- Why a signaling server is needed even for "serverless" P2P (peers need to find each other)
- How Diffie-Hellman key exchange lets two strangers derive a shared secret without ever sending it
- Why nonces matter in AES-GCM (reuse = broken encryption) and how even/odd nonce assignment prevents collisions
- Binary protocol framing — why UDP needs length prefixes and message types
- The difference between WebSocket (persistent, bidirectional) and HTTP (request-response)

### Why the length field in UDP messages?

UDP delivers whole datagrams, so in theory you know the size from `recvfrom`. The length field is still useful for validation (detect corruption/truncation), forward compatibility (future header fields), and keeping the framing logic consistent if the transport ever changes.

### TODO

- Terminal UI with `prompt_toolkit` (scrollback area + fixed input line)
- Proper CLI with `create`/`join` subcommands and `--server` flag
- PING/PONG keepalive to detect dead connections
- `requirements.txt`
- Test over the internet via homelab
- Unit tests for crypto, protocol, and NAT modules

### Use of AI

AI (Claude, via Cursor) wrote no production code in this project but was used extensively as a learning tool:

- Provided example files (`example_crypto.py`, `example_protocol.py`, `example_server.js`) that demonstrated concepts in a different shape, forcing me to adapt rather than copy
- Explained networking concepts from scratch (NAT, STUN, UDP vs TCP, hole punching, WebSockets)
- Explained cryptography concepts (Diffie-Hellman, AES-GCM, nonces, key derivation)
- Reviewed my code and pointed out bugs without writing the fix
- Answered questions during development ("what is `ws._room`?", "why does `.encode()` exist?", "what is an IntEnum?")

**Update:** AI implemented the encryption wiring and chat loop in `connection.py` (steps 1 and 2 of the chat integration) and the local test mode. This section will be updated if AI involvement changes further. AI also polished this readme with markdown. Very cool.