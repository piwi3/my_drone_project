import cv2
from matplotlib import rc_context
import numpy as np
from djitellopy import tello
import key_press_module as kp
import spy_drone as sd
import time

def show_video(img):
    cv2.imshow("Image", img)
    cv2.waitKey(1)

def find_face(img):
    face_cascade = cv2.CascadeClassifier('resources/haarcascade_frontalface_default.xml')
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(img_gray, 1.2, 8)

    face_cpoints = []
    face_areas = []

    for  (x, y, w, h) in faces:
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)
        cx = x + w // 2
        cy = y + h // 2
        area = w * h
        cv2.circle(img, (cx, cy), 5, (0, 255, 0), cv2.FILLED)
        face_cpoints.append([cx, cy])
        face_areas.append(area)
    
    if len(face_areas) != 0:
        i = face_areas.index(max(face_areas))
        return img, [face_cpoints[i], face_areas[i]]
    else:
        return img, [[0, 0], 0]

def track_face(rc_params, face_data, prv_error):
    lr, fb, ud, yv = rc_params
    [cx, cy], area = face_data
    
    # Define movement
    # Unpack error, pid values
    lr_err, fb_err, ud_err, yv_err = get_error(face_data)
    lr_err_prv, fb_err_prv, ud_err_prv, yv_err_prv = prv_error
    prp, itg, dif = PID

    # If no face is detected, no movement
    if cx == 0:
        return (lr, fb, ud, yv)
    # If face is detected, adjust rc-control using pid-control
    else:
        # Left/right
        ### Not yet used

        # Forward/backward
        fb = prp * fb_err + dif * (fb_err - fb_err_prv)
        fb = int(np.clip(fb, -10, 10))

        # Up/down
        ud = prp * ud_err + dif * (ud_err - ud_err_prv)
        ud = int(np.clip(ud, -25, 25))

        # Yaw
        yv = prp * yv_err + dif * (yv_err - yv_err_prv)
        yv = int(np.clip(yv, -25, 25))
    
    return (lr, fb, ud, yv)

def get_error(face_data):
    [cx, cy], area = face_data

    # Return 0 if no face is detected 
    error = (0, 0, 0, 0)
    # Calculate error for all dimensions (negative error should lead to positive speed!)
    if cx != 0:
        lr_err = 0
        fb_err = -1 * (area - FB_CENTER) / FB_CENTER * 100
        # fb_err = -1 * (max(area - FB_RANGE[1], 0) + min(area - FB_RANGE[0], 0)) / FB_CENTER * 100
        ud_err = -1 * (cy - HEIGHT / 2) / (HEIGHT / 2) * 100
        yv_err = (cx - WIDTH / 2) / (WIDTH / 2) * 100

        error = (lr_err, fb_err, ud_err, yv_err)

    return error


# Main program

if __name__ == '__main__':

    WIDTH, HEIGHT = 360, 240
    RES = (WIDTH, HEIGHT)
    FB_RANGE = [6200, 6800]
    FB_CENTER = 6500
    PID = [0.4, 0, 0.4]
    prv_error = (0, 0, 0, 0)

    kp.init()
    me = tello.Tello()
    me.connect()
    print(me.get_battery())
    time.sleep(0.5) # To be able to check the battery status

    me.streamon()

    while True:
        # Get and resize image from drone
        img = me.get_frame_read().frame
        img = cv2.resize(img, RES)
        
        # Start / land drone
        sd.start_land_drone(me) 

        # Perform face-tracking
        # Detect faces
        img, face_data = find_face(img)
        # Derive control signals
        rc_params = (0, 0, 0, 0)
        rc_params = track_face(rc_params, face_data, prv_error)
        # Enable keyboard control
        rc_params = sd.get_rc_control(rc_params)
        # Send control signal to drone
        lr, fb, ud, yv = rc_params
        print(rc_params)
        me.send_rc_control(lr, fb, ud, yv)
        
        # Save error for next iteration (important for pid control)
        prv_error = get_error(face_data)

        # Show video and save image (via pressing 'z', if wanted)
        sd.show_video(img)
        sd.save_image(img)
