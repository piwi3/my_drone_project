# Required imports for controlling tello drone
from djitellopy import tello
import tello_module as tm

# Required imports for video streaming, face tracking and keyboard control
import cv2
import time

# Required imports for speech detection
from ssl import ALERT_DESCRIPTION_UNKNOWN_PSK_IDENTITY
import pyaudio
import websockets
import asyncio
import base64
import json

# Main program

if __name__ == '__main__':

    # Varibales for video streaming and drone control
    WIDTH, HEIGHT = 360, 240
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
    frames_per_buffer=FRAMES_PER_BUFFER
    )

    # Starts videostream
    me.streamon()
    img = me.get_frame_read().frame
    drone_is_on = True

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
                                if text.split()[0].lower() == 'spicy':
                                    command = ' '.join(text.split()[1:])
                                    print(command)
                    except websockets.exceptions.ConnectionClosedError as e:
                        print(e)
                        assert e.code == 4008
                        break
                    except Exception as e:
                        assert False, "Not a websocket 4008 error"
                
            async def video_stream():
                global img, drone_is_on
                while drone_is_on:
                    # Get and resize image from drone
                    img = me.get_frame_read().frame
                    img = cv2.resize(img, RES)

                    # Show video and save image (use 'z' key)
                    cv2.imshow("Image", img)
                    cv2.waitKey(1)

                    # Escape loop, i.e. land drone and stop program
                    if cv2.waitKey(1) & 0xFF == 27:  # use ESC to quit
                        print('Landing drone and stopping program...')
                        me.land()
                        me.streamoff
                        cv2.destroyAllWindows()
                        drone_is_on = False
                    
                    # Giving the other processes time to work
                    await asyncio.sleep(0.01)
            
            async def drone_control():
                global img, command, drone_is_on, prv_error, PID, FB_CENTER, RES
                while drone_is_on:
                    # Fallback control settings
                    rc_params = (0, 0, 0, 0)
                    rc_duration = 0.001
                    
                    # Derive control signals for face tracking (prio 3)
                    img, face_data = tm.find_face(img)
                    error = tm.get_error(face_data, FB_CENTER, RES)
                    rc_params = tm.track_face(rc_params, face_data, PID, error, prv_error)
                    prv_error = error
                    
                    # Implement speech control (prio 2)
                    print('before -> ', command)
                    rc_params, rc_duration, command = tm.speech_control_drone(me, rc_params, rc_duration, command)
                    print('after -> ', command)
                    print('____')
                    
                    # Implement keyboard control (prio 1)
                    rc_params, rc_duration = tm.keyboard_control_drone(me, rc_params, rc_duration)
                    
                    # Send control signal to drone
                    lr, fb, ud, yv = rc_params
                    # print(rc_params) # only for testing
                    me.send_rc_control(lr, fb, ud, yv)
                    await asyncio.sleep(rc_duration)
            
            send_result, receive_result, video_result, control_result = await asyncio.gather(send(), receive(), video_stream(), drone_control())

    asyncio.run(main())
