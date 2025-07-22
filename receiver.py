import uasyncio as asyncio

import usocket as socket
from time import sleep
from machine import Pin
import ssl
import ubinascii
import os
import uwebsocket

async def on_message(message):
    led_onboard = Pin("LED", Pin.OUT)
    # LED einschalten
    led_onboard.on()
    # 5 Sekunden warten
    await asyncio.sleep(message / 1000)
    # LED ausschalten
    led_onboard.off()


class receiver:

    def __init__(self):
        self.host = "tcs-communication.bogner.systems"
        self.port = 443
        self.websocket_route = "/messages/receive"
        self.sock = socket.socket()
        self.jwt = ""

    def connect(self, jwt):
        self.jwt = jwt
        # Setup WebSocket
        addr_info = socket.getaddrinfo(self.host, self.port)
        addr = addr_info[0][-1]

        self.sock.connect(addr)
        self.sock.setblocking(False)
        self.sock = ssl.wrap_socket(self.sock, server_hostname=self.host)

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
        ).format(self.websocket_route, self.host, key, jwt)

        self.sock.send(handshake.encode())

        switching_protocol_confirm = self.sock.recv(1024)
        print(switching_protocol_confirm)
        if switching_protocol_confirm is None:
            print("e")
            return True
        if "101 Switching Protocols" not in switching_protocol_confirm:
            return False
        return None

    async def listen(self):
        while True:
            try:
                response = self.sock.recv(1024)
                print(response)
                if response is not None:
                    payload = response[2:]
                    text = payload.decode()
                    zahl = int(text)
                    await on_message(zahl)
                else:
                    await asyncio.sleep(0.1)
            except:
                print("error")
                try:
                    print("reconnect")
                    self.connect(self.jwt)
                except:
                    await asyncio.sleep(0.1)
