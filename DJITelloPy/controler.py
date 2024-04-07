from djitellopy import Tello
import functions

drone = Tello()

drone.connect()
drone.streamon()
functions.process_video(drone)

drone.takeoff()

# drone.rotate_clockwise(90)

# drone.land()

