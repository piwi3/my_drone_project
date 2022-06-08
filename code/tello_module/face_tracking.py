import cv2
import numpy as np
import os

def find_face(img):
    os.listdir('tello_module/models')
    face_cascade = cv2.CascadeClassifier('tello_module/models/haarcascade_frontalface_default.xml')
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

def track_face(rc_params, face_data, pid, error, prv_error):
    lr, fb, ud, yv = rc_params
    [cx, cy], area = face_data
    
    # Define movement
    # Unpack error, pid values
    lr_err, fb_err, ud_err, yv_err = error
    lr_err_prv, fb_err_prv, ud_err_prv, yv_err_prv = prv_error
    prp, itg, dif = pid

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

def get_alignment_error(object_data, fb_center, res):
    [cx, cy], area = object_data
    width, height = res

    # Return 0 if no face is detected 
    error = (0, 0, 0, 0)
    # Calculate error for all dimensions (negative error should lead to positive speed!)
    # Warning: lr and yv errors should not be used at the same time!!!
    if cx != 0:
        lr_err = (cx - width / 2) / (width / 2) * 100
        fb_err = -1 * (area - fb_center) / fb_center * 100
        # fb_err = -1 * (max(area - FB_RANGE[1], 0) + min(area - FB_RANGE[0], 0)) / FB_CENTER * 100
        ud_err = -1 * (cy - height / 2) / (height / 2) * 100
        yv_err = (cx - width / 2) / (width / 2) * 100

        error = (lr_err, fb_err, ud_err, yv_err)

    return error