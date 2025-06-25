import usocket as socket
import uselect
from time import sleep
from machine import Pin
import ssl
import ubinascii
import os

host = "tcs-communication.bogner.systems"
port = 443
websocket_route = "/messages/receive"

def on_message(message):
    led_onboard = Pin("LED", Pin.OUT)
    # LED einschalten
    led_onboard.on()
    # 5 Sekunden warten
    sleep(message / 1000)
    # LED ausschalten
    led_onboard.off()

def connect(jwt):
    # Setup WebSocket
    addr_info = socket.getaddrinfo(host, port)
    addr = addr_info[0][-1]

    sock = socket.socket()
    sock.connect(addr)
    #sock.setblocking(True)
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

    switching_protocol_confirm = sock.recv(1024)
    if "101 Switching Protocols" not in switching_protocol_confirm:
        return False

    while True:
        try:
            response = sock.recv(1024)
            print(response)
            payload = response[2:]
            text = payload.decode()  # '23'
            zahl = int(text)
            on_message(zahl)
        except:
            print("error")