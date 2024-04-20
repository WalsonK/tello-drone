import socket
import sys
import cv2


class Drone:
    def __init__(self):
        self.CMD_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.CMD_ADDRESS = ('192.168.10.1', 8889)
        self.CMD_SOCKET.bind(('', 9000))
        self.IS_FLYING = False
        self.FWD_VIDEO = None
        self.send("command")
        print("DRONE - Command mode : ON")

    def start(self):
        while True:
            try:
                cmd = input('Enter command: ')
                if cmd == 'exit':
                    break
                if cmd == 'takeoff':
                    self.takeoff()
                if cmd == 'land':
                    self.landing()
                if cmd == 'streamon':
                    self.video_on()
                if cmd == 'streamoff':
                    self.video_off()

            except (KeyboardInterrupt, Exception) as e:
                print('error : {}'.format(e))
                self.CMD_SOCKET.close()
                break

    def send(self, cmd: str):
        if 'end' in cmd:
            if self.IS_FLYING:
                self.landing()
            self.CMD_SOCKET.close()

        cmd = cmd.encode('utf-8')
        self.CMD_SOCKET.sendto(cmd, self.CMD_ADDRESS)

    def takeoff(self):
        self.send("takeoff")
        self.IS_FLYING = True

    def landing(self):
        self.send("land")
        self.IS_FLYING = False

    def video_on(self):
        self.send("streamon")
        self.FWD_VIDEO = cv2.VideoCapture('udp://@0.0.0.0:11111')
        while True:
            try:
                ret, frame = self.FWD_VIDEO.read()
                if ret:
                    cv2.imshow('Forward Brut Cam', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            except Exception as e:
                print('error : {}'.format(e))

    def video_off(self):
        self.send("streamoff")
        self.FWD_VIDEO.release()
        cv2.destroyAllWindows()

