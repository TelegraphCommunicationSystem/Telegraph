import auth_manager
import wifi_manager
import usocket as socket
import uselect
from time import sleep
from machine import Pin
import ssl
import ubinascii
import os

wlan = wifi_manager.get_connection()
if wlan is None:
    print("Could not initialize the network connection.")
    while True:
        pass  # you shall not pass :D

jwt = auth_manager.get_jwt()
if jwt is None or jwt is "No valid TOTP":
    print("Could not initialize the network connection.")
    while True:
        pass  # you shall not pass :D
print(jwt)

host = "tcs-communication.bogner.systems"
port = 443
websocket_route = "/messages/receive"

# Setup WebSocket
addr_info = socket.getaddrinfo(host, port)
addr = addr_info[0][-1]

sock = socket.socket()
sock.connect(addr)
# sock.setblocking(False)
sock = ssl.wrap_socket(sock, server_hostname=host)

key = ubinascii.b2a_base64(os.urandom(16)).strip().decode()

handshake = (
    "GET {} HTTP/1.1\r\n"
    "Host: {}\r\n"
    "Upgrade: websocket\r\n"
    "Connection: Upgrade\r\n"
    "Sec-WebSocket-Key: {}\r\n"
    "Sec-WebSocket-Version: 13\r\n"
    "Authorization: Bearer {}\r\n"
    "\r\n"
).format(websocket_route, host, key, jwt)

sock.send(handshake.encode())

response = sock.recv(40960)
while True:
    response = sock.recv(40960)
    payload = response[2:]
    text = payload.decode()  # '23'
    zahl = int(text)
    print(zahl)


    led_onboard = Pin("LED", Pin.OUT)
    # LED einschalten
    led_onboard.on()
    # 5 Sekunden warten
    sleep(zahl/1000)
    # LED ausschalten
    led_onboard.off()
