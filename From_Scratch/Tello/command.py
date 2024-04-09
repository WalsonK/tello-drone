import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
address = ('192.168.10.1', 8889)
sock.bind(('', 9000))

while True:
    try:
        cmd = input('Enter command: ')
        if not cmd: break
        if 'end' in cmd:
            sock.close()
            break
        cmd = cmd.encode('utf-8')
        sock.sendto(cmd, address)
    except KeyboardInterrupt as e:
        print('error : {}'.format(e))
        sock.close()
        break
