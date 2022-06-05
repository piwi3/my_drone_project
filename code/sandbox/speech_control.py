from ssl import ALERT_DESCRIPTION_UNKNOWN_PSK_IDENTITY
import pyaudio
import cv2
import websockets
import asyncio
import base64
import json
 
FRAMES_PER_BUFFER = 3200
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
p = pyaudio.PyAudio()
 
# starts recording
stream = p.open(
   format=FORMAT,
   channels=CHANNELS,
   rate=RATE,
   input=True,
   frames_per_buffer=FRAMES_PER_BUFFER
)

# Starts video stream
font = cv2.FONT_HERSHEY_SIMPLEX
command = ""
webcamIsOn = True
cap = cv2.VideoCapture(0)
 
# the AssemblyAI endpoint we're going to hit
URL = "wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000"
auth_key ='83e5c103711f4881820f2c89c2b4ab8b'

async def send_receive():
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

        async def webcam():
            global command, webcamIsOn
            while webcamIsOn:
                ret, frame = cap.read()

                if command:
                    cv2.putText(frame, command, (50, 425), font, 1, (0, 255, 255), 2, cv2.LINE_4)
                cv2.imshow("Webcam", frame)
                cv2.waitKey(1)

                if cv2.waitKey(1) & 0xFF == 27:  # use ESC to quit
                    webcamIsOn = False
                    cap.release()
                    cv2.destroyAllWindows()
                await asyncio.sleep(0.001)
      
        send_result, receive_result, webcam_result = await asyncio.gather(send(), receive(), webcam())

asyncio.run(send_receive())