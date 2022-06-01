from djitellopy import tello
import key_press_module as kp
import time
import cv2

# Definition of required functions

def show_video(img):
    cv2.imshow("Image", img)
    cv2.waitKey(1)

def save_image(img):
    if kp.get_key('z'):
        print('z pressed')
        cv2.imwrite(f'images/drone/{time.time()}.jpg', img)
        time.sleep(0.2)

def start_land_drone(me):
    if kp.get_key('q') and me.is_flying:
        me.land()
   
    if kp.get_key('e') and not me.is_flying:
        me.takeoff()
    
    time.sleep(1)

def get_rc_control(rc_params):
    lr, fb, ud, yv = rc_params
    speed = 50 

    if kp.get_key('RIGHT'):
        lr = speed
    elif kp.get_key('LEFT'):
        lr = -speed

    if kp.get_key('UP'):
        fb = speed
    elif kp.get_key('DOWN'):
        fb = -speed

    if kp.get_key('w'):
        ud = speed
    elif kp.get_key('s'):
        ud = -speed

    if kp.get_key('d'):
        yv = speed
    elif kp.get_key('a'):
        yv = -speed

    return (lr, fb, ud, yv)


# Main program

if __name__ == '__main__':

    kp.init()
    me = tello.Tello()
    me.connect()
    print(me.get_battery())
    time.sleep(0.5) # To be able to check the battery status

    me.streamon()

    while True:
        # Get and resize image from drone
        img = me.get_frame_read().frame
        res = (360, 240)
        img = cv2.resize(img, res)

        # Show video and save image if wanted
        show_video(img)
        save_image(img)

        # Start or land drone via keyboard
        start_land_drone(me)

        # Get rc-control and send to drone
        rc_params = (0, 0, 0, 0)
        rc_params = get_rc_control(rc_params)
        lr, fb, ud, yv = rc_params
        me.send_rc_control(lr, fb, ud, yv)


    