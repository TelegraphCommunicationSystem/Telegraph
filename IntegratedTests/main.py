from machine import Pin, PWM
from machine import ADC
import uasyncio as asyncio
from time import sleep
from sinus_generator import start_generator

# Common Anode LED
## PWM setup
red = PWM(Pin(2))
green = PWM(Pin(3))
blue = PWM(Pin(4))

## PWM frequency
red.freq(1000)
green.freq(1000)
blue.freq(1000)

def set_color(r, g, b):
    print("r:" + f"{int(r):3d}" + ", g:" + f"{int(g):3d}" + ", b:" + f"{int(b):3d}")
    red.duty_u16(65535 - int(r * 257))
    green.duty_u16(65535 - int(g * 257))
    blue.duty_u16(65535 - int(b * 257))



# 3 Pos switch
pin16 = Pin(16, Pin.IN, Pin.PULL_DOWN)
pin17 = Pin(17, Pin.IN, Pin.PULL_DOWN)

def read_state():
    if pin17.value():
        return 0
    elif pin16.value():
        return 2
    else:
        return 1

# Poti
pinAdc = ADC(28)

# Motor
# pinMotor = Pin(1, Pin.OUT, Pin.PULL_DOWN)
pinMotor = PWM(Pin(1))
pinMotor.freq(1000)

# Magnet
pinMagnet = Pin(0, Pin.OUT)

# Audio
pinSpeaker = Pin(14, Pin.OUT, Pin.PULL_DOWN)
pinHeadphones = Pin(15, Pin.OUT, Pin.PULL_DOWN)

# Inputs
pinInput0 = Pin(26, Pin.IN, Pin.PULL_DOWN)
pinInput1 = Pin(18, Pin.IN, Pin.PULL_DOWN)


# Control
## LED
redValue = 0;
greenValue = 0;
blueValue = 0;

def setLEDcolor():
    global value, redValue, blueValue, greenValue
    value = pinAdc.read_u16()
    colorValue = value * 255 / 65535

    if colorValue > 0:
        colorValue = colorValue - 1

    if (read_state() == 0):
        redValue = colorValue;
    elif (read_state() == 1):
        greenValue = colorValue;
    elif (read_state() == 2):
        blueValue = colorValue;

    # set_color(redValue, greenValue, blueValue)
    set_color(0, 0, 0)


## Motor speed
def setMotorSpeed():
    global value
    value = pinAdc.read_u16()
    pinMotor.duty_u16(value)
    # print("Pin: " + str(value))




async def main():
    timer = 0

    start_generator()

    while True:
        setLEDcolor()
        setMotorSpeed()

        timer = timer + 1

        # if(timer % 15 == 0):
        #     pinSpeaker.toggle()

        pinSpeaker.value(pinInput1.value())
        pinMagnet.value(pinInput1.value())

        # if(timer % 50 == 0):
        #     pinMagnet.toggle()

        sleep(0.05)

asyncio.run(main())