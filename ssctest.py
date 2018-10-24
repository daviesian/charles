#! /usr/bin/env python
import serial
import ssc32
from time import sleep

SSC32_PORT = '/dev/cu.usbserial'

if True:
    ssc = ssc32.SSC32(SSC32_PORT, 115200, count=32)
    print("Testing SSC")
    ssc.ser.flush()
    print(ssc.ser.read(50))
    print("Flushed - input now", ssc.ser.in_waiting)
    ssc.ser.reset_input_buffer()
    ssc.ser.write('VER\r')
    ssc.ser.flush()
    sleep(0.2)
    print(ssc.ser.read(50))
    print("Done")

    print("Setting output 0")
    ssc[0].position = 1000
    ssc.commit(1)
    done = False
    while not done:
        ssc.ser.write(b'Q\r')
        ssc.ser.flush()
        r = ssc.ser.read(1)
        print("Sent Q, received", r)
        done = (r=='.')
    print("Done")

else:
    ser = serial.Serial(SSC32_PORT, 115200, timeout=1)
    # important for baudrate autodetection
    ser.write('\r'*20)
    ser.flush()
    ser.reset_input_buffer()
    ser.write(b'VER\r')
    ser.flush()
    sleep(1)
    print(ser.read(50))

    done = False
    while not done:
        ser.write('Q\r')
        ser.flush()
        r = ser.read(1)
        print("Sent Q, received", r)
        done = (r=='.')
    print("Done")
