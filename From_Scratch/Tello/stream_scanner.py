import cv2

forward_video = cv2.VideoCapture('udp://@0.0.0.0:11111')

while True:
    try:
        ret, frame = forward_video.read()
        if ret:
            # Convertir l'image en niveaux de gris
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Appliquer un flou pour réduire le bruit
            blurred_frame = cv2.GaussianBlur(gray_frame, (5, 5), 0)
            # Détection des contours
            edges = cv2.Canny(blurred_frame, 50, 150)
            # Trouver les contours dans l'image
            contours, _ = cv2.findContours(edges.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            # Sélectionner le contour du mur le plus loin
            farthest_wall_contour = max(contours, key=cv2.contourArea)
            # Dessiner le contour du mur le plus loin sur l'image originale
            cv2.drawContours(frame, [farthest_wall_contour], -1, (0, 255, 0), 2)
            # Afficher l'image avec le contour du mur le plus loin
            cv2.imshow('Farthest Wall Detection', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    except Exception as e:
        print('error : {}'.format(e))

forward_video.release()
cv2.destroyAllWindows()
