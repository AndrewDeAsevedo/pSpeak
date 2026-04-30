import socket
import os
import struct


# Have to implement manual STUN because pystun creates and closes it's own socket :(


def get_public_ip_stun(sock):
    stun_host = "stun.l.google.com"
    stun_port = 19302

    # 20-byte STUN Header: Type(2), Length(2), Magic Cookie(4), Transaction ID(12)
    magic_cookie = b"\x21\x12\xa4\x42"
    transaction_id = os.urandom(12)
    message = b"\x00\x01\x00\x00" + magic_cookie + transaction_id

    try:
        sock.sendto(message, (stun_host, stun_port))
        data, addr = sock.recvfrom(2048)
        # print(f"Received response from {addr} \n Data: {data}")
        parsed_data = parseData(data)
        # print(parsed_data)
        return parsed_data

    except Exception as e:
        raise "Error: {e}"


# Stole this part from Claude
def parseData(data):
    # Skip 20-byte header, walk attributes
    offset = 20
    resp_type, resp_len = struct.unpack("!HH", data[0:4])
    MAGIC = 0x2112A442
    while offset < 20 + resp_len:
        attr_type, attr_len = struct.unpack("!HH", data[offset : offset + 4])
        attr_value = data[offset + 4 : offset + 4 + attr_len]
        if attr_type == 0x0020:  # XOR-MAPPED-ADDRESS
            xor_port = struct.unpack("!H", attr_value[2:4])[0]
            port = xor_port ^ (MAGIC >> 16)
            xor_ip = struct.unpack("!I", attr_value[4:8])[0]
            ip_int = xor_ip ^ MAGIC
            ip = socket.inet_ntoa(struct.pack("!I", ip_int))
            # print(ip, port)
            return ip, port
        offset += 4 + attr_len + (4 - attr_len % 4) % 4


if __name__ == "__main__":
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)
    get_public_ip_stun(sock)
