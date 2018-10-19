#! /usr/bin/env python

from time import sleep
from pydynamixel import dynamixel as dyn_raw
import ssc32

from utils import Input, Output, DirectMapping, FakeSinMapping, dyn
import utils


SSC32_PORT = '/dev/cu.usbserial'  # 'COM9' Grey serial lead
# SSC32_PORT = '/dev/tty.usbserial'  # 'COM9' Grey serial lead
DYNAMIXEL_PORT = '/dev/tty.usbserial-A9007E5k'  # 'COM4' Black USB lead


class Charles:

    def __init__(self, mirror=False):

        # A dictionary mapping names to servo outputs

        self.outputs = {

            # BROW MOVEMENTS
            "CENTER_BROW": Output(1, default=1550, min=2025, max=1175, type="SSC32"),
            "INNER_BROW_RIGHT": Output(2, default=1750, min=2225, max=1450, type="SSC32"),
            "INNER_BROW_LEFT": Output(3, default=1275, min=800, max=1800, type="SSC32"),
            "OUTER_BROW_RIGHT": Output(4, default=1225, min=1775, max=975, type="SSC32"),
            "OUTER_BROW_LEFT": Output(5, default=1500, min=1175, max=1750, type="SSC32"),

            # EYE MOVEMENTS
            "RIGHT_EYE_TURN": Output(6, default=1560, range=500, type="SSC32"),
            "LEFT_EYE_TURN": Output(7, default=1460, range=450, type="SSC32"),
            "UPPER_EYE_LIDS": Output(8, min=1075, max=2025, default=1665, type="SSC32"),
            "LOWER_EYE_LIDS": Output(9, min=1350, max=1950, default=1575, type="SSC32"),
        #    "EYES_UP_DOWN": Output(10, min=1225, max=2200, default=1700, type="SSC32"),
            "EYES_UP_DOWN": Output(10, min=1225, max=1800, default=1500, type="SSC32"),

            # MID FACIAL MOVEMENTS
            "SQUINT_RIGHT": Output(11, min=1225, max=1600, default=1600, type="SSC32", reverse=True),
            "SQUINT_LEFT": Output(12, min=1300, max=1625, default=1300, type="SSC32"),
            "SNEER_RIGHT": Output(13, min=1425, max=1950, default=1425, type="SSC32"),
            "SNEER_LEFT": Output(14, min=1200, max=1625, default=1625, type="SSC32", reverse=True),

            # MOUTH MOVEMENTS
            "LOWER_LIP_RIGHT": Output(15, min=725, max=1500, default=1275, type="SSC32"),
            "LOWER_LIP_LEFT": Output(16, min=1500, max=2150, default=2075, type="SSC32"),
            "LOWER_LIP_CENTER": Output(17, min=1500, max=1900, default=1750, type="SSC32"),
            "UPPER_LIP_RIGHT": Output(18, min=1250, max=2250, default=1700, type="SSC32"),
            "UPPER_LIP_LEFT": Output(19, min=1225, max=2325, default=1950, type="SSC32", reverse=True),
            "UPPER_LIP_CENTER": Output(20, min=1125, max=1700, default=1425, type="SSC32"),
            "SMILE_FROWN_RIGHT": Output(21, min=247, max=791, default=585, type="DYNAMIXEL", reverse=True, velocity=5),
            "EE_OO": Output(22, min=310, max=511, default=448, type="DYNAMIXEL", velocity=5),
            "SMILE_FROWN_LEFT": Output(23, min=381, max=825, default=640, type="DYNAMIXEL", velocity = 5),


            # NECK MOVEMENTS
            "TURN": Output(24, range=800, default=500, type="DYNAMIXEL"),
            "TILT": Output(25, range=800, default=663, type="DYNAMIXEL"),
            "NOD": Output(26, min=147, max=905, default=200, type="DYNAMIXEL"),
            "JAW": Output(27, min=286, max=574, default=318, type="DYNAMIXEL", velocity=5),
        }

    def initialise(self):
        ##########################
        ### Init SSC-32 servos
        ##########################

        ssc = None
        try:
            ssc = ssc32.SSC32(SSC32_PORT, 115200, count=32)

        except Exception as e:
            print "Could not initialise servos: %s" % e

        ##########################
        ### Init dynamixel servos
        ##########################

        try:
            dyn.init_dynamixel_serial(DYNAMIXEL_PORT)

        ##########################
        ### Slowly move to default positions
        ##########################

            print "Initialising..."

            for o in self.outputs.values():
                o.initialise(ssc=ssc)

            for o in self.outputs.values():
                if o.type == "DYNAMIXEL":
                    while dyn_raw.get_is_moving(dyn.dyn_serial,o.id):
                        sleep(0.01)

            # This enables a pulse to the microcontroller, which
            # will then turn on the relay providing servo power
            # to the SSC32.
            ssc[0].position = 1000
            ssc.commit(0)
            print "Done"

        except Exception as e:
            print e
            raise


# A simple test to make him do something
def main():
    charles = Charles()
    charles.initialise()
    sleep(3)
    print("Waking up")
    charles.outputs["NOD"].set_float_pos(0.5, 30)
    sleep(3)
    print("Nod")
    charles.outputs["NOD"].set_float_pos(0.0, 50)
    sleep(0.7)
    charles.outputs["NOD"].set_float_pos(0.5, 40)
    sleep(1)
    charles.outputs["RIGHT_EYE_TURN"].set_float_pos(0.0, 10)
    sleep(1)
    charles.outputs["RIGHT_EYE_TURN"].set_float_pos(1.0, 10)
    sleep(1)
    charles.outputs["INNER_BROW_LEFT"].set_float_pos(1.0)
    sleep(1)
    charles.outputs["INNER_BROW_LEFT"].set_float_pos(0.0)
    sleep(1)
    print("Enigmatic smile")
    charles.outputs["SMILE_FROWN_RIGHT"].set_float_pos(0.8, 60)
    charles.outputs["SMILE_FROWN_LEFT"].set_float_pos(0.8, 60)
    sleep(2)
    charles.outputs["SMILE_FROWN_RIGHT"].set_float_pos(0.0, 60)
    charles.outputs["SMILE_FROWN_LEFT"].set_float_pos(0.0, 60)
    sleep(2)

if __name__ == '__main__':
    main()

