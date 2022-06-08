import re 
import time

def speech_control_drone(me, rc_params, rc_duration, mode, command):
    lr, fb, ud, yv = rc_params
    speed = 30

    command = command.lower()

    # Change modes via voice - take pictures, face tracking, hand gesture control
    # Take pictures?
    if re.findall(r'take pictures|take Images', command):
        mode['take_pics'] = True
        command = ''
        print('Image capturing mode activated...')
        return (0, 0, 0, 0), rc_duration, command
    
    # Track face?
    if re.findall(r'track face|track my face', command):
        mode['track_face'] = True
        command = ''
        print('Face tracking mode activated...')
        return (0, 0, 0, 0), rc_duration, command

    # Track hand?
    if re.findall(r'watch my hand|wash my hand', command):
        mode['watch_hand'] = True
        command = ''
        print('Hand control mode activated...')
        return (0, 0, 0, 0), rc_duration, command

    # End all tracking modes
    if re.findall(r'stop tracking|stop watching|stop active mode', command):
        mode['track_face'] = False
        mode['watch_hand'] = False
        command = ''
        return (0, 0, 0, 0), rc_duration, command


    # Control movement of drone via voice
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
        rc_duration = 1
    elif re.findall(r'move left|go left', command):
        lr = -speed
        rc_duration = 1

    if re.findall(r'move forward|go forward', command):
        fb = speed
        rc_duration = 1
    elif re.findall(r'move back|go back', command):
        fb = -speed
        rc_duration = 1

    if re.findall(r'move up|go up', command):
        ud = speed
        rc_duration = 2
    elif re.findall(r'move down|go down', command):
        ud = -speed
        rc_duration = 2

    if re.findall(r'turn right|head right', command):
        yv = speed
        rc_duration = 3
    elif re.findall(r'turn left|head left', command):
        yv = -speed
        rc_duration = 3

    if (lr, fb, ud, yv) != rc_params:
        command = ''

    return (lr, fb, ud, yv), rc_duration, command

    
    

    
