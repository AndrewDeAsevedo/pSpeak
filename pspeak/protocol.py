from enum import IntEnum
import struct
# importing encryptor to use in main for testing, later make this file recieve the content not encrypt it itself.

class MsgType(IntEnum):
    HELLO = 0
    BYE = 1
    MSG = 2
    ACK = 3
    PING = 4
    PONG = 5

# Will recieve the type, and the body it wants to transmit, and return bytes containing type, len, content. 
def pack(msg_type: MsgType, msg_content: bytes) -> bytes:
    msg_len = 1 + len(msg_content)
    msg_len_bytes = struct.pack("!I", msg_len)
    msg_type_bytes = int(msg_type).to_bytes(1, "big")

    packed_msg =  msg_len_bytes + msg_type_bytes + msg_content
    return packed_msg

# Will recieve the dataset and unpack it from bytes to its type, len and content.
def unpack(content: bytes) -> tuple[int, MsgType, bytes]:
    msg_len_bytes = content[0:4]
    msg_type_bytes = content[4:5]
    msg_content_bytes = content[5:]

    msg_type = MsgType(int.from_bytes(msg_type_bytes, byteorder='big'))
    payload_len = int.from_bytes(msg_len_bytes, byteorder='big') - 1
    
    # TODO: make this a try except block
    if payload_len != len(msg_content_bytes):
        raise ValueError("Length mismatch")
    

    return (payload_len, msg_type, msg_content_bytes)


def main():

    msg = pack(MsgType.MSG, b'test')
    unpacked_msg = unpack(msg)
    print(msg.hex(), unpacked_msg)


if __name__ == "__main__":
    main()
