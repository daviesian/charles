#! /usr/bin/env python3

from __future__ import print_function
# from builtins import object
from time import sleep
from pydynamixel import dynamixel as dyn_raw
import dynamixel as dyn
import ssc32

from utils import Input, DirectMapping, FakeSinMapping
import utils


SSC32_PORT = '/dev/cu.usbserial'  # 'COM9' Grey serial lead
# SSC32_PORT = '/dev/tty.usbserial'  # 'COM9' Grey serial lead
DYNAMIXEL_PORT = '/dev/tty.usbserial-A9007E5k'  # 'COM4' Black USB lead


class Output(object):

    def __init__(self, id, default, min=None, max=None, range=None, reverse=False, velocity=1, ssc=None):
        self.id = id
        self.ssc = ssc

        if range is not None:
            if min is None and max is None:
                min = default - range*0.5
                max = default + range*0.5
            elif min is not None:
                max = min+range
            elif max is not None:
                min = max-range
            else:
                raise Exception("If range is specified, must specify zero or one of min,max.")
        else:
            if min is None or max is None:
                raise Exception("If range is not specified, must specify min,max.")

        if not min <= default <= max and not max <= default <= min:
            raise Exception("Default value must be between min and max.")

        self.min = min
        self.max = max
        self.default = default
        self.reverse = reverse
        self.velocity = velocity

    def _set_int_pos(self, int_pos, velocity=10):
        # Needs to be implemented by subclass
        raise NotImplementedError()

    def set_float_pos(self, float_pos, velocity=10):
        if float_pos > 1:
            float_pos = 1
        elif float_pos < 0:
            float_pos = 0

        if self.reverse:
            float_pos = 1 - float_pos
        #print "Setting %s to %.4f" % (self.name, float_pos)
        int_pos = int(self.min + float_pos*(self.max-self.min))

        self._set_int_pos(int_pos, velocity)

    def initialise(self, interface=None):
        self._set_int_pos(self.default)


class SSC32Output(Output):

    def initialise(self, interface=None):
        self.ssc = interface
        super(SSC32Output, self).initialise(interface)

    def _set_int_pos(self, int_pos, velocity=10):
        """Velocity not very well tested for SSC"""
        self.ssc[self.id].position = int_pos
        # argument of commit is time in ms
        # Converting to something velocity-based to compare with dynamixel
        self.ssc.commit(10000//(velocity*self.velocity))


class DynamixelOutput(Output):

    def initialise(self, interface=None):
        dyn.init_dynamixel_servo(self.id)
        super(DynamixelOutput, self).initialise(interface)

    def _set_int_pos(self, int_pos, velocity=10):
        """ Move to position in range 0-1023 """
        dyn.update_dynamixel(self.id, int_pos, velocity*self.velocity)
        # print("Dynamixel {} set to {}".format(self.id, int_pos))

    def is_moving(self):
        return dyn_raw.get_is_moving(dyn.dyn_serial, self.id)


class Charles(object):

    def __init__(self, mirror=False):

        # The serial ports
        self.ssc = None

        # A dictionary mapping names to servo outputs
        self.outputs = {

            # BROW MOVEMENTS
            "CENTER_BROW": SSC32Output(1, default=1550, min=2025, max=1175),
            "INNER_BROW_RIGHT": SSC32Output(2, default=1750, min=2225, max=1450),
            "INNER_BROW_LEFT": SSC32Output(3, default=1275, min=800, max=1800),
            "OUTER_BROW_RIGHT": SSC32Output(4, default=1225, min=1775, max=975),
            "OUTER_BROW_LEFT": SSC32Output(5, default=1500, min=1175, max=1750),

            # EYE MOVEMENTS
            "RIGHT_EYE_TURN": SSC32Output(6, default=1560, range=500),
            "LEFT_EYE_TURN": SSC32Output(7, default=1460, range=450),
            "UPPER_EYE_LIDS": SSC32Output(8, min=1080, max=1900, default=1595),
            "LOWER_EYE_LIDS": SSC32Output(9, min=1380, max=1890, default=1590),
        #   SSC32 "EYES_UP_DOWN": Output(10, min=1225, max=2200, default=1700),
            "EYES_UP_DOWN": SSC32Output(10, min=1225, max=1800, default=1500),

            # MID FACIAL MOVEMENTS
            "SQUINT_RIGHT": SSC32Output(11, min=1225, max=1600, default=1600, reverse=True),
            "SQUINT_LEFT": SSC32Output(12, min=1300, max=1625, default=1300),
            "SNEER_RIGHT": SSC32Output(13, min=1425, max=1950, default=1425),
            "SNEER_LEFT": SSC32Output(14, min=1200, max=1625, default=1625, reverse=True),

            # MOUTH MOVEMENTS
            "LOWER_LIP_RIGHT": SSC32Output(15, min=725, max=1500, default=1275),
            "LOWER_LIP_LEFT": SSC32Output(16, min=1500, max=2150, default=2075),
            "LOWER_LIP_CENTER": SSC32Output(17, min=1500, max=1900, default=1750),
            "UPPER_LIP_RIGHT": SSC32Output(18, min=1250, max=2250, default=1700),
            "UPPER_LIP_LEFT": SSC32Output(19, min=1225, max=2325, default=1950, reverse=True),
            "UPPER_LIP_CENTER": SSC32Output(20, min=1125, max=1700, default=1425),
            "SMILE_FROWN_RIGHT": DynamixelOutput(21, min=247, max=791, default=585, reverse=True, velocity=5),
            "EE_OO": DynamixelOutput(22, min=310, max=511, default=448, velocity=5),
            "SMILE_FROWN_LEFT": DynamixelOutput(23, min=381, max=825, default=640, velocity = 5),


            # NECK MOVEMENTS
            "TURN": DynamixelOutput(24, range=800, default=500, velocity=2),
            "TILT": DynamixelOutput(25, range=800, default=663, velocity=2),
            "NOD": DynamixelOutput(26, min=147, max=905, default=200, velocity=3),
            "JAW": DynamixelOutput(27, min=286, max=574, default=318, velocity=7),
        }

    def initialise(self):
        ##########################
        ### Init SSC-32 servos
        ##########################

        try:
            self.ssc = ssc32.SSC32(SSC32_PORT, 115200, count=32)
            print("Testing SSC")
            print("Firmware version: {}".format(self.ssc.version()))
            print("Done")

        except Exception as e:
            print("Could not initialise servos: %s" % e)
            raise

        ##########################
        ### Init dynamixel servos
        ##########################

        try:
            dyn.init_dynamixel_serial(DYNAMIXEL_PORT)

        ##########################
        ### Slowly move to default positions
        ##########################

            print("Initialising...")

            for o in list(self.outputs.values()):
                o.initialise(interface=self.ssc)

            # This enables a pulse to the microcontroller, which
            # will then turn on the relay providing servo power
            # to the SSC32.
            print("Powering up face servos")
            self.ssc[0].position = 1000
            self.ssc.commit(1)
            while not self.ssc.is_done():
                print("Waiting for SSC")
                sleep(0.5)
            
            print("Waiting until still")
            self.wait_until_still()
            print("Done")            

        except Exception as e:
            print(e)
            raise
    
    def is_moving(self):
        """
        Are any of the servos moving?
        """
        # The SSC32 gives a response for the whole board.
        if not self.ssc.is_done():
            return True


        for o in list(self.outputs.values()):
            if isinstance(o, DynamixelOutput) and o.is_moving():
                return True

        return False

    def wait_until_still(self):
        while self.is_moving():
            sleep(0.1)

# A simple test to make him do something
def main():
    charles = Charles()
    charles.initialise()
    sleep(2)

    print("Waking up")
    charles.outputs["NOD"].set_float_pos(0.5, 30)
    charles.wait_until_still()

    print("Blink")
    charles.outputs["UPPER_EYE_LIDS"].set_float_pos(0.0, 100)
    charles.outputs["LOWER_EYE_LIDS"].set_float_pos(0.8, 100)
    charles.wait_until_still()
    charles.outputs["UPPER_EYE_LIDS"].set_float_pos(0.4, 100)
    charles.outputs["LOWER_EYE_LIDS"].set_float_pos(0.6, 100)
    charles.wait_until_still()
    charles.outputs["UPPER_EYE_LIDS"].set_float_pos(0.0, 100)
    charles.outputs["LOWER_EYE_LIDS"].set_float_pos(0.8, 100)
    charles.wait_until_still()
    charles.outputs["UPPER_EYE_LIDS"].set_float_pos(0.6, 40)
    charles.outputs["LOWER_EYE_LIDS"].set_float_pos(0.4, 40)
    charles.wait_until_still()

    print("Nod")
    charles.outputs["NOD"].set_float_pos(0.0, 50)
    charles.wait_until_still()
    charles.outputs["NOD"].set_float_pos(0.5, 40)
    charles.wait_until_still()

    print("Look around")
    charles.outputs["TURN"].set_float_pos(0.0, 50)
    charles.wait_until_still()
    charles.outputs["TURN"].set_float_pos(1.0, 50)
    charles.wait_until_still()
    charles.outputs["TURN"].set_float_pos(0.5, 40)
    charles.wait_until_still()

    print("Quizzical")
    charles.outputs["TILT"].set_float_pos(0.0, 50)
    charles.wait_until_still()
    charles.outputs["TILT"].set_float_pos(1.0, 50)
    charles.wait_until_still()
    charles.outputs["TILT"].set_float_pos(0.5, 40)
    charles.wait_until_still()

    print("Eye wiggle")
    charles.outputs["RIGHT_EYE_TURN"].set_float_pos(0.0, 20)
    charles.outputs["LEFT_EYE_TURN"].set_float_pos(0.0, 20)
    charles.wait_until_still()
    charles.outputs["RIGHT_EYE_TURN"].set_float_pos(1.0, 20)
    charles.outputs["LEFT_EYE_TURN"].set_float_pos(1.0, 20)
    charles.wait_until_still()
    charles.outputs["RIGHT_EYE_TURN"].set_float_pos(0.5, 10)
    charles.outputs["LEFT_EYE_TURN"].set_float_pos(0.5, 10)
    charles.wait_until_still()

    print("Roger Moore")
    charles.outputs["INNER_BROW_LEFT"].set_float_pos(1.0, 20)
    charles.outputs["INNER_BROW_RIGHT"].set_float_pos(0.0, 20)
    charles.wait_until_still()
    charles.outputs["INNER_BROW_LEFT"].set_float_pos(0.0, 20)
    charles.outputs["INNER_BROW_RIGHT"].set_float_pos(1.0, 20)
    charles.wait_until_still()
    charles.outputs["INNER_BROW_RIGHT"].set_float_pos(0.5, 10)
    charles.outputs["INNER_BROW_RIGHT"].set_float_pos(0.5, 10)
    charles.wait_until_still()

    print("Enigmatic smile")
    charles.outputs["SMILE_FROWN_RIGHT"].set_float_pos(0.8, 60)
    charles.outputs["SMILE_FROWN_LEFT"].set_float_pos(0.8, 60)
    charles.wait_until_still()
    charles.outputs["SMILE_FROWN_RIGHT"].set_float_pos(0.0, 60)
    charles.outputs["SMILE_FROWN_LEFT"].set_float_pos(0.0, 60)
    charles.wait_until_still()

    print("Squint right, left, both and none")
    charles.outputs["SQUINT_RIGHT"].set_float_pos(0.95, 60)
    charles.outputs["SQUINT_LEFT"].set_float_pos(0.5, 60)
    charles.wait_until_still()
    sleep(1)
    charles.outputs["SQUINT_RIGHT"].set_float_pos(0.5, 60)
    charles.outputs["SQUINT_LEFT"].set_float_pos(0.95, 60)
    charles.wait_until_still()
    sleep(1)
    charles.outputs["SQUINT_RIGHT"].set_float_pos(0.95, 60)
    charles.outputs["SQUINT_LEFT"].set_float_pos(0.95, 60)
    charles.wait_until_still()
    sleep(1)
    charles.outputs["SQUINT_RIGHT"].set_float_pos(0, 60)
    charles.outputs["SQUINT_LEFT"].set_float_pos(0, 60)
    charles.wait_until_still()
    sleep(1)

    print("Lip movements")
    charles.outputs["UPPER_LIP_RIGHT"].set_float_pos(0.9, 60)
    charles.outputs["UPPER_LIP_CENTER"].set_float_pos(0.8, 60)
    charles.outputs["UPPER_LIP_LEFT"].set_float_pos(0.9, 60)
    charles.outputs["LOWER_LIP_RIGHT"].set_float_pos(0.8, 60)
    charles.outputs["LOWER_LIP_CENTER"].set_float_pos(0.9, 60)
    charles.outputs["LOWER_LIP_LEFT"].set_float_pos(0.8, 60)
    
    charles.wait_until_still()
    sleep(1)
    charles.outputs["UPPER_LIP_CENTER"].set_float_pos(0.3, 60)
    charles.wait_until_still()
    sleep(1)

    charles.outputs["UPPER_LIP_RIGHT"].set_float_pos(0.5, 60)
    charles.outputs["UPPER_LIP_CENTER"].set_float_pos(0.5, 60)
    charles.outputs["UPPER_LIP_LEFT"].set_float_pos(0.5, 60)
    charles.outputs["LOWER_LIP_RIGHT"].set_float_pos(0.5, 60)
    charles.outputs["LOWER_LIP_CENTER"].set_float_pos(0.5, 60)
    charles.outputs["LOWER_LIP_LEFT"].set_float_pos(0.5, 60)
    charles.wait_until_still()
    sleep(1)






if __name__ == '__main__':
    main()

