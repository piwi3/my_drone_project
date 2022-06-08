from djitellopy import tello
import tello_module as tm
import cv2
import time

# Main program

if __name__ == '__main__':

    WIDTH, HEIGHT = 360, 240
    RES = (WIDTH, HEIGHT)
    FB_RANGE = [6200, 6800]
    FB_CENTER = 6500
    PID = [0.4, 0, 0.4]
    prv_error = (0, 0, 0, 0)

    tm.init_keyboard_control()
    me = tello.Tello()
    me.connect()
    print(me.get_battery())
    time.sleep(0.5) # To be able to check the battery status

    me.streamon()

    while True:
        # Get and resize image from drone
        img = me.get_frame_read().frame
        img = cv2.resize(img, RES)

        # Perform face-tracking
        # Detect faces
        img, face_data = tm.find_face(img)
        # Derive control signals
        rc_params = (0, 0, 0, 0)
        # Implement face tracking
        error = tm.get_error(face_data, FB_CENTER, RES)
        rc_params = tm.track_face(rc_params, face_data, PID, error, prv_error)
        prv_error = error
        # Enable keyboard control
        rc_params = tm.keyboard_control_drone(me, rc_params)
        # Send control signal to drone
        lr, fb, ud, yv = rc_params
        print(rc_params)
        me.send_rc_control(lr, fb, ud, yv)
        
        # Save error for next iteration (important for pid control)
        prv_error = tm.get_error(face_data, FB_CENTER, RES)

        # Show video and save image (via pressing 'z', if wanted)
        cv2.imshow("Image", img)
        cv2.waitKey(1)
        
        tm.save_image(img)