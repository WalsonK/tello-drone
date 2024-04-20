import tello

tello = tello.Tello()

while True:
    try:
        command = input("Command :")
        tello.send_command(command)
        if not command:
            break
    except KeyboardInterrupt:
        print('\n . . .\n')
        break
