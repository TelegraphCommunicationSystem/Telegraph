import re
import uasyncio as asyncio

import usocket as socket
import ssl
import ubinascii
import os

from machine import Pin, PWM
from time import sleep


# Frequenz und Duty-Cycle einstellen
async def beep(frequency=1000, duration=0.5):
    beeper = PWM(Pin(15))
    beeper.freq(frequency)     # Frequenz in Hz
    beeper.duty_u16(32768)     # 50 % Duty-Cycle (65535/2)
    sleep(duration / 1000)
    beeper.duty_u16(0)         # Ton aus

async def on_message(message):
    led_onboard = Pin("LED", Pin.OUT)
    # LED einschalten
    led_onboard.on()
    led_onboard.high()
    # 5 Sekunden warten
    await asyncio.sleep(message)
    # LED ausschalten
    led_onboard.low()
    led_onboard.off()

def extract_times(data) -> tuple[int, int]:
    """
    Extract paused and pressed times from a bytes object.

    Args:
        data (bytes): The raw byte sequence containing the pattern 'paused:<num>;pressed:<num>;'

    Returns:
        tuple[int, int]: (paused_time, pressed_time)
    """
    # If data is bytes, decode it
#    if isinstance(data, bytes):
 #       text = data.decode(errors="ignore")
  #  else:
    text = str(data)
    match = re.search(r'paused:(\d+);pressed:(\d+);', text)
    if not match:
        print("Could not find paused/pressed times in data")
        raise ValueError("Could not find paused/pressed times in data")
    return {"paused": int(match.group(1)), "pressed": int(match.group(2))}

class receiver:

    def __init__(self):
        self.host = "tcs-communication.bogner.systems"
        self.port = 443
        self.websocket_route = "/messages/receive"
        self.sock = socket.socket()
        self.jwt = ""
        self.connected = False

    def connect(self, jwt):
        self.jwt = jwt
        self.sock = socket.socket()

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
            return True
        if "101 Switching Protocols" not in switching_protocol_confirm:
            return False
        self.connected = True
        return None

    async def listen(self):
        while True:
            try:
                response = self.sock.recv(1024)
                print(response)
                if response is not None:
      #              payload = response[2:]
       #             text = payload.decode()
        #            zahl = int(text)
                    try:
                        payload = extract_times(response)
                    except Exception as e:
                        print(e)
                    print(payload)
                    asyncio.sleep(payload["paused"]/1000)
                    await on_message(payload["pressed"]/1000)
                else:
                    await asyncio.sleep(0.1)
            except:
                print("error")
                try:
                    print("reconnect")
                    self.connect(self.jwt)
                except OSError as e:
                    print(e)
                    await asyncio.sleep(1)


