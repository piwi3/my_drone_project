import re 
import time

def speech_control_drone(me, rc_params, rc_duration, command):
    lr, fb, ud, yv = rc_params
    speed = 20 

    command = command.lower()

    # Start and land drone via voice
    if re.findall(r'land', command) and me.is_flying:
        me.land()
        time.sleep(2)
        command = ''
        return (0, 0, 0, 0), rc_duration, command
    elif (re.findall(r'takeoff', command) or re.findall(r'take off', command)) and not me.is_flying:
        me.takeoff()
        command = ''
        return (0, 0, 0, 0), rc_duration, command
    
    # Move drone via voice (change rc-params)
    if re.findall(r'move right', command):
        lr = speed
    elif re.findall(r'move left', command):
        lr = -speed

    if re.findall(r'move forward', command):
        fb = speed
    elif re.findall(r'move backwards', command):
        fb = -speed

    if re.findall(r'move up', command):
        ud = speed
    elif re.findall(r'move down', command):
        ud = -speed

    if re.findall(r'turn right', command):
        yv = speed
    elif re.findall(r'turn left', command):
        yv = -speed

    if (lr, fb, ud, yv) != rc_params:
        rc_duration = 2
        command = ''

    return (lr, fb, ud, yv), rc_duration, command

    
    

    
