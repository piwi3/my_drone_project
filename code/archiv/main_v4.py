# Required imports for controlling tello drone
from djitellopy import tello
from matplotlib import image
import tello_module as tm

# Required imports for video streaming, face tracking and keyboard control
import cv2
import time
import uuid
import os
import re

# Required imports for speech detection
from ssl import ALERT_DESCRIPTION_UNKNOWN_PSK_IDENTITY
import pyaudio
import websockets
import asyncio
import base64
import json

# Required imports for hand gesture control
import mediapipe as mp
from tensorflow.python.keras.models import load_model

# Main program

if __name__ == '__main__':

    # Varibales for video streaming and drone control
    WIDTH, HEIGHT = 640, 480
    RES = (WIDTH, HEIGHT)
    FB_RANGE = [6200, 6800]
    FB_CENTER = 6500
    PID = [0.4, 0, 0.4]
    prv_error = (0, 0, 0, 0)

    # Variables for speech detection (with AssemblyAI API and pyaudio)
    FRAMES_PER_BUFFER = 3200
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    p = pyaudio.PyAudio()
    URL = "wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000" # AssemblyAI endpoint that is used
    auth_key ='83e5c103711f4881820f2c89c2b4ab8b' # AssemblyAI key

    # Import relevant models
    holistic = mp.solutions.holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5)
    hand_model = load_model('tello_module/models/hand_gesture_model.h5')

    # Starts drone and keyboard control
    tm.init_keyboard_control()
    me = tello.Tello()
    me.connect()
    command = ""
    print(me.get_battery())
    time.sleep(0.5) # To be able to check the battery status

    # Starts audio recording
    stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=FRAMES_PER_BUFFER,
    input_device_index=2 # 0 = MacBook Air, 2 = Airpods
    )

    # Starts videostream
    me.streamon()
    img = me.get_frame_read().frame
    drone_is_on = True
    mode = {}

    async def main():
        print(f'Connecting websocket to url ${URL}')
        async with websockets.connect(
            URL,
            extra_headers=(("Authorization", auth_key),),
            ping_interval=5,
            ping_timeout=20) as _ws:
            
            await asyncio.sleep(0.1)
            print("Receiving SessionBegins ...")
            session_begins = await _ws.recv()
            print(session_begins)
            print("Sending messages ...")
        
            async def send():
                while True:
                    try:
                        data = stream.read(FRAMES_PER_BUFFER, exception_on_overflow = False)
                        data = base64.b64encode(data).decode("utf-8")
                        json_data = json.dumps({"audio_data":str(data)})
                        await _ws.send(json_data)
                    except websockets.exceptions.ConnectionClosedError as e:
                        print(e)
                        assert e.code == 4008
                        break
                    except Exception as e:
                        assert False, "Not a websocket 4008 error"
                    await asyncio.sleep(0.01)
            
                return True
        
            async def receive():
                global command
                while True:
                    try:
                        result_str = await _ws.recv()
                        if json.loads(result_str)['message_type']=='FinalTranscript':
                            text = json.loads(result_str)['text']
                            if text != '':
                                print('-> ', text)
                                if re.findall('spicy|slightly|i', text.split()[0].lower()):
                                    command = ' '.join(text.split()[1:])
                                    print(command)
                    except websockets.exceptions.ConnectionClosedError as e:
                        print(e)
                        assert e.code == 4008
                        break
                    except Exception as e:
                        assert False, "Not a websocket 4008 error"
                
            async def video_stream():
                global img, img_mod, drone_is_on, mode
                while drone_is_on:
                    # Get and resize image from drone, adjust RES accordingly
                    img = me.get_frame_read().frame
                    img = cv2.resize(img, RES)

                    # Giving the other processes time to work
                    # Placed before imshow to incoporate model output
                    await asyncio.sleep(1. / 30)

                    # Show video
                    cv2.imshow("Image", img_mod)
                    cv2.waitKey(1)

                    # Escape loop, i.e. land drone and stop program
                    if cv2.waitKey(1) & 0xFF == 27:  # use ESC to quit
                        print('Landing drone and stopping program...')
                        me.land()
                        me.streamoff()
                        cv2.destroyAllWindows()
                        drone_is_on = False

            async def drone_control():
                global img, img_mod, command, drone_is_on, mode, prv_error, PID, FB_CENTER, RES
                while drone_is_on:
                    # Define img_mod in case no 'tracking' mode is active
                    img_mod = img

                    # Fallback control settings
                    rc_params = (0, 0, 0, 0)
                    rc_duration = 0.01 # Required for voice control of drone 
                    
                    # Determine control signals for face tracking (prio 3)
                    if mode.get('track_face', False):
                        img_mod, face_data = tm.find_face(img)
                        error = tm.get_alignment_error(face_data, FB_CENTER, RES)
                        rc_params = tm.track_face(rc_params, face_data, PID, error, prv_error)
                        prv_error = error

                    # Determine control signals for hand tracking (joint prio 3)
                    if mode.get('watch_hand', False):
                        img_mod, hand_pred, hand_data = tm.predict_hand_gesture(img, holistic, hand_model, RES)
                        error = tm.get_alignment_error(hand_data, FB_CENTER, RES)
                        rc_params = tm.convert_hand_signal_to_rc_params(rc_params, hand_pred, hand_data, PID, error, prv_error)
                        prv_error = error
                        
                    # Determine control signals from voice control (prio 2)
                    rc_params, rc_duration, command = tm.speech_control_drone(me, rc_params, rc_duration, mode, command)
                    
                    # Determine control signals from keyboard control (prio 1, i.e. overwrites all other signals)
                    rc_params = tm.keyboard_control_drone(me, rc_params)
                    
                    # Send control signal to drone
                    lr, fb, ud, yv = rc_params
                    me.send_rc_control(lr, fb, ud, yv)
                    await asyncio.sleep(rc_duration)

            async def image_and_video_recording():
                # Particularly video recording needs to be seperated 
                # to avoid blocking of new frames (see djitellopy doc example)
                global img, img_mod, mode, drone_is_on
                # Variables for video recording
                out = None
                # Variables for image taking
                last_time = time.time()
                img_num = 1
                n_pics = 50
                dir_path = ''
                while drone_is_on:
                    # Save a video 
                    if mode.get('video_capt', False):
                        # Record video if mode 'video_capt' is True
                        out = tm.video_capt(img_mod, out)
                    else:
                        # If 'video_capt' = False, 
                        # release out and set it to None again
                        if out != None:
                            out.release()
                            out = None
                    
                    # Save images every 1 sec, if mode 'take_pics' is True
                    if mode.get('take_pics', False) and (time.time() >= last_time + 1):
                        img, img_num, dir_path, last_time = tm.image_capt(img_mod, img_num, dir_path)
                    if img_num > n_pics:
                        img_num = 1
                        mode['take_pics'] = False
                        print('{n_pics} images saved to disk!')

                    # Wait in alignment with frames per second = 30 
                    await asyncio.sleep(1. / 30)
            
            send_result, receive_result, video_result, control_result, record_result = await asyncio.gather(send(), receive(), video_stream(), drone_control(), image_and_video_recording())

    asyncio.run(main())
