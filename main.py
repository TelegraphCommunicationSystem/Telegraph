import auth_manager
import receiver
import wifi_manager

wlan = wifi_manager.get_connection()
if wlan is None:
    print("Could not initialize the network connection.")
    while True:
        pass  # you shall not pass :D

print(wlan)

jwt = auth_manager.get_jwt()
if jwt is None or jwt is "No valid TOTP":
    print("Could not initialize the network connection.")
    while True:
        pass  # you shall not pass :D
print(jwt)

receiver = receiver.receiver()
receiver.connect(jwt)
receiver.listen()