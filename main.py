from time import sleep

import machine

import receiver
from manager import wifi_manager, auth_manager
import uasyncio as asyncio
from machine import Pin
from manager.update_manager import update_firmware

def blink_led():
    led_onboard = Pin("LED", Pin.OUT)
    for i in range(0,100):
        led_onboard.on()
        sleep(0.1)
        led_onboard.off()
        sleep(0.1)

async def main():
    led_onboard = Pin("LED", Pin.OUT)
    led_onboard.off()

    #Status zeichen wenn wifi manager an
    wlan = wifi_manager.get_connection()
    if wlan is None:
        print("Could not initialize the network connection.")
        blink_led()
        while True:
            pass  # you shall not pass :D
    print(wlan)

    update_firmware()

    jwt = create_jwt()
    receiver_obj = connect_receiver(jwt)

    #status pi hochgefahren und aktiv
    await asyncio.gather(
        receiver_obj.listen(),
        check_button_pressed(),
        receiver_obj.ping_pong()
    )

def create_jwt():
    try:
        jwt = auth_manager.get_jwt()
    except:
        #Falls eine Exception fliegt, ist es wahrscheinlich ein Timeout, das kommt vor, wenn ein Socket noch offen ist
        machine.reset()
    if jwt is None:
        print("Could not create JWT.")
        machine.soft_reset()
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