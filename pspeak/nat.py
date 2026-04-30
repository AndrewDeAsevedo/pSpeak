import stun

# TODO: Can probably make this a one liner or a helper in whatever ends up being connection


def get_public_address():
    nat_type, external_ip, external_port = stun.get_ip_info(
        stun_host="stun.l.google.com", stun_port=19302
    )

    if external_ip is None:
        raise ConnectionError("STUN failed, couldn't discover public address")

    print(nat_type, external_ip, external_port)
    return [external_ip, external_port]


if __name__ == "__main__":
    get_public_address()
