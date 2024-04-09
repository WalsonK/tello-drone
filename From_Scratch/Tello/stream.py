import cv2

forward_video = cv2.VideoCapture('udp://@0.0.0.0:11111')

while True:
    try:
        ret, frame = forward_video.read()
        if ret:
            cv2.imshow('Forward Brut Cam', frame)
            cv2.waitKey(1)
    except Exception as e:
        forward_video.release()
        cv2.destroyAllWindows()
        print('error : {}'.format(e))
