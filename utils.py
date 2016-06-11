import dynamixel as dyn
import time
import math

ssc = None

class Output(object):

    def __init__(self, id, default, type, min=None, max=None, range=None, reverse=False, velocity=1):
        self.id = id

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
        self.type = type
        self.velocity = velocity

    def _set_int_pos(self, int_pos, velocity=10):
        if self.type == "DYNAMIXEL":
            dyn.update_dynamixel(self.id, int_pos, velocity*self.velocity)
        elif self.type == "SSC32":
            ssc[self.id].position = int_pos
            ssc.commit(100)

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

    def initialise(self):
        if self.type == "DYNAMIXEL":
            dyn.init_dynamixel_servo(self.id)

        self._set_int_pos(self.default)



class Input(object):

    def __init__(self, map, idx, min=None, max=None, center=None, range=None, expand=False):
        self.map = map
        self.idx = idx

        if center is not None and range is not None and min is None and max is None:
            min = center-range*0.5
            max = center+range*0.5
        elif min is not None and max is not None and range is None and center is None:
            pass
        else:
            raise Exception("Must specify min,max or center,range.")

        if min > max:
            raise Exception("min must be smaller than max")

        self.min = min
        self.max = max
        self.expand = expand
        self.range = range

    def is_available(self, input_maps):
        return self.map in input_maps

    def get_float(self, input_maps):
        v = input_maps[self.map][self.idx]

        if self.expand:
            if v < self.min:
                self.min = v
            elif v > self.max:
                self.max = v

        v_frac = (v - self.min) / float(self.max-self.min)

        if v_frac > 1:
            v_frac = 1
        elif v_frac < 0:
            v_frac = 0

        return v_frac


class DirectMapping(object):

    def __init__(self, input, outputs, reverse=False, multiplier=1):
        self.input = input
        self.outputs = outputs
        self.reverse = reverse

    def update(self, input_maps):
        if self.input.is_available(input_maps):
            f = self.input.get_float(input_maps)
            if self.reverse:
                f = 1-f
            for o in self.outputs:
                o.set_float_pos(f, 60)

class FakeSinMapping(object):

    def __init__(self, output):
        self.output = output

    def update(self, input_maps):
        f = math.sin(time.clock())*0.5+0.5
        self.output.set_float_pos(f)