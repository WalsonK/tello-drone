import cv2
from ultralytics import YOLO
import random
import numpy as np

# Check if YOLO OK
# ultralytics.checks()

""""" BASIC USE
model = YOLO("path", "v8")
output = model.predict(source="video", source_type="video", confidence=0.5)
print(output)
"""
class_list = ['person', 'Walson', 'Nicolas', 'Adrien']

# Generate random colors for class list
detection_colors = []
for i in range(len(class_list)):
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    detection_colors.append((b, g, r))

# load a pretrained YOLOv8n model
model = YOLO("models/yolov8n.pt", "v8")

cam = cv2.VideoCapture('udp://@0.0.0.0:11111')
while True:
    try:
        ret, frame = cam.read()
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        # Predict on image
        detect_params = model.predict(source=[frame], conf=0.45, save=False)

        # Convert tensor array to numpy
        dp = detect_params[0].numpy()
        print(dp)

        if len(dp) != 0:
            for i in range(len(detect_params[0])):
                print(i)

                boxes = detect_params[0].boxes
                box = boxes[i]  # returns one box
                clsID = box.cls.numpy()[0]
                conf = box.conf.numpy()[0]
                bb = box.xyxy.numpy()[0]

                cv2.rectangle(
                    frame,
                    (int(bb[0]), int(bb[1])),
                    (int(bb[2]), int(bb[3])),
                    detection_colors[int(clsID)],
                    3,
                )

                # Display class name and confidence
                font = cv2.FONT_HERSHEY_COMPLEX
                cv2.putText(
                    frame,
                    class_list[int(clsID)] + " " + str(round(conf, 3)) + "%",
                    (int(bb[0]), int(bb[1]) - 10),
                    font,
                    1,
                    (255, 255, 255),
                    2,
                )

        # Display the resulting frame
        cv2.imshow("Forward Camera", frame)

    except Exception as e:
        print('error : {}'.format(e))

cam.release()
cv2.destroyAllWindows()
