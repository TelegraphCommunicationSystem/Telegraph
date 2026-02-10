from time import sleep, time

import machine

import receiver
from manager import wifi_manager, auth_manager
import uasyncio as asyncio
from machine import Pin
from manager.update_manager import update_firmware
import urequests


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

    global JWT
    JWT = create_jwt()
    receiver_obj = connect_receiver(JWT)

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


def make_call(pressed, paused):
    print(f"Button pressed for {pressed}s, paused for {paused}s")
    try:
        url = "https://tcs-communication.bogner.systems/messages/send"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {JWT}"
        }
        body = {
            "receiver_username": "test",
            "content": {
                "paused": str(int(paused)),
                "pressed": str(int(pressed))
            }
        }
        response = urequests.post(url, json=body, headers=headers)
        print(f"API Response: {response.status_code}")
        response.close()
    except Exception as e:
        print(f"Error making API call: {e}")


async def check_button_pressed():
    button = Pin(4, Pin.IN, Pin.PULL_UP)
    last_press_time = None
    button_press_start = None

    while True:
        # Button is pressed when pin reads 0 (active low with pull-up)
        if button.value() == 0:
            if button_press_start is None:
                # Button just pressed
                button_press_start = time()
        else:
            if button_press_start is not None:
                # Button just released
                press_end = time()
                pressed_duration = press_end - button_press_start

                if last_press_time is not None:
                    paused_duration = button_press_start - last_press_time
                else:
                    paused_duration = 0

                make_call(pressed_duration, paused_duration)

                last_press_time = press_end
                button_press_start = None

        await asyncio.sleep(0.05)


asyncio.run(main())
