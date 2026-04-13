import stun

#TODO: Can probably make this a one liner or a helper in whatever ends up being main

def main():
    nat_type, external_ip, external_port = stun.get_ip_info()
    return [external_ip, external_port]

if __name__ == '__main__':
    main()
