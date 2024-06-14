import os
from time import time

import cv2
from djitellopy import Tello
from qreader import QReader


def process_tello_video(drone: Tello):
    PHOTOS_DIR = "photos"
    if not os.path.exists(PHOTOS_DIR):
        os.makedirs(PHOTOS_DIR)

    last_move_time = time()
    last_capture_time = time()
    CAPTURE_INTERVAL = 2
    MOVE_INTERVAL = 5

    while True:
        frame = drone.get_frame_read().frame
        cv2.imshow("Frame", frame)  # type: ignore

        current_time = time()
        if current_time - last_capture_time >= CAPTURE_INTERVAL:
            filename = os.path.join(PHOTOS_DIR, f"frame_{int(current_time)}.jpg")
            cv2.imwrite(filename, frame)  # type: ignore
            detected_action = detect_qrcode(filename)
            os.remove(filename)
            if detected_action:
                if detected_action[0]:
                    print(f"Detected action: {detected_action[0]}")
                    if detected_action[0] == "droite":
                        drone.rotate_clockwise(90)
                    elif detected_action[0] == "gauche":
                        drone.rotate_counter_clockwise(90)
            last_capture_time = current_time

        if current_time - last_move_time >= MOVE_INTERVAL:
            drone.move_forward(50)
            last_move_time = current_time

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    drone.streamoff()
    drone.end()
    cv2.destroyAllWindows()


def detect_qrcode(image_path: str) -> tuple:
    qreader = QReader()
    image = cv2.cvtColor(cv2.imread(image_path), cv2.COLOR_BGR2RGB)
    decoded_texts = qreader.detect_and_decode(image=image)
    return decoded_texts


if __name__ == "__main__":
    try:
        drone = Tello()
        drone.connect()
        drone.streamon()
        drone.takeoff()
        drone.move_up(50)
        process_tello_video(drone)
    except Exception as e:
        print(f"An error occurred: {e}")
