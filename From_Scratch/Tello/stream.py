import cv2

forward_video = cv2.VideoCapture('udp://@0.0.0.0:11111')

while True:
    try:
        ret, frame = forward_video.read()
        if ret:
            cv2.imshow('Forward Brut Cam', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            print('No frame received')
            break
    except cv2.error as e:
        print('error : {}'.format(e))

forward_video.release()
cv2.destroyAllWindows()
