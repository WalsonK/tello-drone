import threading
import socket
import platform

host = ''
port = 9000
loader = (host, port)


# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

tello_address = ('192.168.10.1', 8889)

sock.bind(loader)


def recv():
    count = 0
    while True:
        try:
            data, server = sock.recvfrom(1518)
            print('Drone response : {} \n'.format(data.decode(encoding="utf-8")))
        except Exception:
            print('\nExit . . .\n')
            break


print('\r\n\r\nTello Python.\r\n')

print('Tello: command takeoff land flip forward back left right \r\n       up down cw ccw speed speed?\r\n')


# recvThread create
recvThread = threading.Thread(target=recv)
recvThread.start()

while True:
    try:
        python_version = str(platform.python_version())
        version_init_num = int(python_version.partition('.')[0])
        # print(version_init_num)
        msg = ""
        if version_init_num == 3:
            msg = input("Command :")
        if not msg:
            break

        if 'end' in msg:
            print('...')
            sock.close()
            break

        # Send data
        msg = msg.encode(encoding="utf-8")
        sent = sock.sendto(msg, tello_address)
    except KeyboardInterrupt:
        print('\n . . .\n')
        sock.close()
        break

