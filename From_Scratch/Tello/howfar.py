# PLAN ACTION :
# Activer la camera
# Calculer la distance à l'objet le plus loin
# 1 . focal length F of our camera: F = (P x D) / W
#           P : width of object in picture
#           D : distance
#           W : Width object
# 2 . triangle similarity : D’ = (W x F) / P
#           P : width of object in picture
#           D : distance
#           W : Width object
# Afficher la distance avec CV2

import cv2


def find_maker(img):
    # convert the image to grayscale, blur it, and detect edges
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(gray, 35, 125)
    # find the contours in the edged image and keep the largest one;
    # we'll assume that this is our piece of paper in the image
    cnts = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    c = max(cnts, key=cv2.contourArea)
    # compute the bounding box of the of the paper region and return it
    return cv2.minAreaRect(c)


def distance_to_camera(known_width, focal_length, per_width):
    # compute and return the distance from the maker to the camera
    return (known_width * focal_length) / per_width


FOCAL_LENGTH = 950.0
KNOWN_WIDTH = 11.0


cam = cv2.VideoCapture(1)

if not cam.isOpened():
    print("Could not open camera")
    exit()

while True:
    try:
        ret, frame = cam.read()
        if ret:
            marker = find_maker(frame)
            marker_width = marker[1][0]

            distance = distance_to_camera(KNOWN_WIDTH, FOCAL_LENGTH, marker_width)

            # Display the frame with the detected marker and distance
            cv2.putText(frame, "Distance: {:.2f} inches".format(distance), (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            cv2.imshow('Brut Cam', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            print('No frame received')
            break
    except cv2.error as e:
        print('error : {}'.format(e))

cam.release()
cv2.destroyAllWindows()
