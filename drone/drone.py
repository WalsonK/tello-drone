import os
from re import S
from time import sleep, time

import cv2
import requests
from djitellopy import Tello
from qreader import QReader


def predict_user(image):
    url = "http://localhost:8001/api/predict"
    files = {"file": ("frame.jpg", open(image, "rb"), "image/jpeg")}
    response = requests.post(url, files=files)
    print(response.json())
    print(len(response.json()))
    if len(response.json()) > 0:
        return 1
    return 0


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

            if predict_user(filename) == 1:
                print("User predicted! Performing flip and landing...")
                drone.flip_forward()
                drone.flip_back()
                drone.land()
                sleep(5)
                drone.takeoff()
                drone.go_xyz_speed(0, 70, 0, 10)
                drone.land()
                break

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
        drone.move_up(70)
        process_tello_video(drone)
    except Exception as e:
        print(f"An error occurred: {e}")
