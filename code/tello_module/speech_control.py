import re 
import time

def speech_control_drone(me, rc_params, rc_duration, mode, command):
    lr, fb, ud, yv = rc_params
    speed = 30

    command = command.lower()

    # Change modes
    # Take pictures?
    if re.findall(r'take pictures|take Images', command):
        mode['take_pics'] = True
        command = ''
        return (0, 0, 0, 0), rc_duration, command
    
    # Track faces?
    # ...

    # Start and land drone via voice
    if re.findall(r'land|stop|finish', command) and me.is_flying:
        me.land()
        rc_duration = 2
        command = ''
        return (0, 0, 0, 0), rc_duration, command
    elif re.findall(r'takeoff|take off', command) and not me.is_flying:
        me.takeoff()
        command = ''
        return (0, 0, 0, 0), rc_duration, command
    
    # Move drone via voice (change rc-params)
    if re.findall(r'move right|go right', command):
        lr = speed
    elif re.findall(r'move left|go left', command):
        lr = -speed

    if re.findall(r'move forward|go forward', command):
        fb = speed
    elif re.findall(r'move back|go back', command):
        fb = -speed

    if re.findall(r'move up|go up', command):
        ud = speed
    elif re.findall(r'move down|go down', command):
        ud = -speed

    if re.findall(r'turn right|head right', command):
        yv = speed
    elif re.findall(r'turn left|head left', command):
        yv = -speed

    if (lr, fb, ud, yv) != rc_params:
        rc_duration = 2
        command = ''

    return (lr, fb, ud, yv), rc_duration, command

    
    

    
