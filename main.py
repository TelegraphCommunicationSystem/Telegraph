import auth_manager
import receiver
import wifi_manager
import uasyncio as asyncio

async def main():
    wlan = wifi_manager.get_connection()
    if wlan is None:
        print("Could not initialize the network connection.")
        while True:
            pass  # you shall not pass :D

    print(wlan)

    jwt = auth_manager.get_jwt()
    if jwt is None:
        print("Could not create JWT.")
        while True:
            pass  # you shall not pass :D
    print(jwt)

    receiver_obj = await connect_receiver(jwt)

    await asyncio.gather(
        receiver_obj.listen(),
        check_button_pressed()
    )

async def connect_receiver(jwt):
    rec = receiver.receiver()
    rec.connect(jwt)
    return rec

async def check_button_pressed():
    while True:
        print("Tue andere Dinge...")
        await asyncio.sleep(2)

asyncio.run(main())