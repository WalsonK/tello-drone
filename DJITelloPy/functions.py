import cv2


def process_video(drone):
    while True:
        frame = drone.get_frame_read().frame
        cv2.imshow('frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        cv2.destroyAllWindows()
