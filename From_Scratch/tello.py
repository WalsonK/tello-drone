import time
import socket
import threading

threads_initialized = False
drones = {}
sock: socket.socket


class Tello:
    TELLO_IP = '192.168.10.1'
    CONTROl_PORT = 8889
    STATE_PORT = 8890
    UDP_IP = '0.0.0.0'
    STREAM_PORT = 11111

    def __init__(self, host=TELLO_IP, port=STREAM_PORT):
        self.is_flying = False
        global threads_initialized, sock, drones

        self.address = (host, self.CONTROl_PORT)
        self.stream_on = False
        self.last_command_timestamp = time.time()

        if not threads_initialized:
            # Create a UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(('', 9000))

            # Response
            # receive_res_thread = threading.Thread(target=self.receive_res())
            # receive_res_thread.start()
            # State
            # self.receive_state()

            threads_initialized = True

        drones[host] = {'responses': [], 'state': []}
        print('Tello initialized Host:{} Port:{}'.format(host, self.CONTROl_PORT))

    @staticmethod
    def receive_res():
        while True:
            try:
                data, address = sock.recvfrom(1518)

                address = address[0]
                print('Data received from {}'.format(address))

                if address not in drones:
                    continue

                drones[address]['responses'].append(data.decode(encoding="utf-8"))

            except Exception as e:
                print('error: {}'.format(e))
                break

    @staticmethod
    def receive_state():
        ...

    def send_command(self, command: str):
        diff = time.time() - self.last_command_timestamp
        if diff < 0.1:
            print('Waiting {} seconds'.format(diff))
            time.sleep(diff)

        print("Sending command: {}".format(command))
        timestamp = time.time()

        formatted_command = command.encode(encoding="utf-8")
        sock.sendto(formatted_command, self.address)
        responses = drones[self.address[0]]['responses']

        while not responses:
            if time.time() - timestamp > 7:
                print('Aborting command {}. No response after {} seconds'.format(command, 7))
                time.sleep(0.1)

        self.last_command_timestamp = time.time()
        first_res = responses.pop(0)
        try:
            res = first_res.decode(encoding="utf-8")
            print('Response : {}'.format(res))
        except UnicodeDecodeError as e:
            print('error: {}'.format(e))

    def connect(self):
        self.send_command("command")

    def takeoff(self):
        self.send_command("takeoff")
        self.is_flying = True

    def land(self):
        self.send_command("land")
        self.is_flying = False
