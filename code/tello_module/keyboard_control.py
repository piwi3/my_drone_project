import pygame 
import cv2
import time

def init_keyboard_control():
    pygame.init()
    win = pygame.display.set_mode((400,400))

def get_key(key_name):
    ans = False
    for event in pygame.event.get(): 
        pass
    key_input = pygame.key.get_pressed()
    my_key = getattr(pygame, f'K_{key_name}')
    if key_input[my_key]:
        ans = True
    pygame.display.update()
    return ans

def keyboard_control_drone(me, rc_params):
    lr, fb, ud, yv = rc_params
    speed = 50 

    # Start and land drone via keyboard
    if get_key('q') and me.is_flying:
        me.land()
        time.sleep(2)
        return (0, 0, 0, 0)
    elif get_key('e') and not me.is_flying:
        me.takeoff()
        return (0, 0, 0, 0)
    
    # Control drone via keyboard
    if get_key('RIGHT'):
        lr = speed
    elif get_key('LEFT'):
        lr = -speed

    if get_key('UP'):
        fb = speed
    elif get_key('DOWN'):
        fb = -speed

    if get_key('w'):
        ud = speed
    elif get_key('s'):
        ud = -speed

    if get_key('d'):
        yv = speed
    elif get_key('a'):
        yv = -speed
    
    return (lr, fb, ud, yv)

def save_image(img):
    if get_key('z'):
        print('z pressed')
        cv2.imwrite(f'data/saved_by_drone/{time.time()}.jpg', img)
        time.sleep(0.2)