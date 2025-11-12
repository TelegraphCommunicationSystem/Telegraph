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

    def create_ping_frame(self):
        # WebSocket ping frame: FIN=1, Opcode=9 (ping), Länge=0
        return b'\x89\x00'

    async def ping_pong(self):
        try:
            while True:
                self.sock.send(self.create_ping_frame())
                await asyncio.sleep(10)  # Alle 10 Sekunden
        except Exception as e:
            print(f"Ping-Pong-Fehler: {e}")
            self.connected = False

    def decode_websocket_frame(self, data):
        if not data:
            return None

        # Einfache WebSocket-Frame-Dekodierung
        opcode = data[0] & 0x0f
        if opcode == 0x0a:  # Pong
            return None
        elif opcode == 0x01:  # Text Frame
            payload_len = data[1] & 0x7f
            payload_start = 2
            return data[payload_start:payload_start + payload_len]
        return data

    async def listen(self):
        while True:
            try:
                response = self.sock.recv(1024)
                print(f"Received data: {response}")  # Besseres Logging



                # Ignoriere leere Nachrichten
                if not response and not response == b'':
                    await asyncio.sleep(0.1)
                    continue

                if response == b'\x8a\x00':
                    print(f"Ignoriere leere Nachrichten: {response}")
                    await asyncio.sleep(0.1)
                    continue

                if response == b'' or len(response) == 0 or response.strip() == b'':
                    print("beadslfjdsalk")
                    await self.do_reconnect()

                try:
                    payload = extract_times(response)
                    print(f"Extracted payload: {payload}")

                    sleep_time = payload["paused"] / 1000
                    # Zusätzliche Validierung
                    if sleep_time < 10:
                        await asyncio.sleep(sleep_time)
                        print(f"Sleep time too long: {sleep_time}ms")

                    await on_message(payload["pressed"] / 1000)

                except ValueError as e:
                    print(f"Parsing error: {e}")
                    await asyncio.sleep(0.1)

            except OSError as e:
                print(f"Socket error: {e}")
                try:
                    print("Attempting reconnect...")
                    self.sock.close()  # Explizit alte Verbindung schließen
                    await asyncio.sleep(1)  # Kurz warten vor Reconnect
                    self.connect(self.jwt)
                except Exception as reconnect_error:
                    print(f"Reconnect failed: {reconnect_error}")
                    await asyncio.sleep(5)  # Längere Wartezeit bei Reconnect-Fehler


    async def do_reconnect(self):
        self.connected = False
        try:
            print("Closing old connection...")
            self.sock.close()
        except:
            pass

        retry_count = 0
        max_retries = 3
        while not self.connected and retry_count < max_retries:
            try:
                retry_count += 1
                print(f"Reconnect attempt {retry_count}/{max_retries}")
                self.connect(self.jwt)
                await asyncio.sleep(3)
                if self.connected:
                    print("Reconnect successful!")
                    return True
            except Exception as reconnect_error:
                print(f"Reconnect attempt {retry_count} failed: {reconnect_error}")
                if retry_count < max_retries:
                    await asyncio.sleep(retry_count * 2)  # Exponentieller Backoff

        print("All reconnect attempts failed")
        return False