from time import sleep

import auth_manager
import receiver
import wifi_manager
import uasyncio as asyncio
from machine import Pin
import time

def blink_led():
    led_onboard = Pin("LED", Pin.OUT)
    for i in range(0,100):
        led_onboard.on()
        sleep(0.1)
        led_onboard.off()
        sleep(0.1)

async def main():
    wlan = wifi_manager.get_connection()
    if wlan is None:
        print("Could not initialize the network connection.")
        blink_led()
        while True:
            pass  # you shall not pass :D
    print(wlan)


    jwt = create_jwt()
    receiver_obj = connect_receiver(jwt)

    await asyncio.gather(
        receiver_obj.listen(),
        check_button_pressed()
    )

def create_jwt():
    jwt = auth_manager.get_jwt()
    if jwt is None:
        print("Could not create JWT.")
        blink_led()
        while True:
            pass  # you shall not pass :D
    print(jwt)
    return jwt

def connect_receiver(jwt):
    rec = receiver.receiver()
    rec.connect(jwt)
    return rec

async def check_button_pressed():
    while True:
        print("Tue andere Dinge...")
        await asyncio.sleep(2)

asyncio.run(main())