from djitellopy import tello
from time import sleep

me = tello.Tello()
me.connect()

print(me.get_battery())

me.takeoff()
me.send_rc_control(0,0,0,50)
sleep(5)
me.send_rc_control(0,0,0,0)
sleep(0.5)
me.land()
