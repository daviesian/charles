import dynamixel as dyn
import time
import math

ssc = None

class Output(object):

    def __init__(self, id, name, default, type, min=None, max=None, range=None):
        self.id = id
        self.name = name

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

        if not min < default < max and not max < default < min:
            raise Exception("Default value must be between min and max.")

        self.min = min
        self.max = max
        self.default = default
        self.type = type

    def set_int_pos(self, int_pos, velocity=10):
        if self.type == "DYNAMIXEL":
            dyn.update_dynamixel(self.id, int_pos, velocity)
        elif self.type == "SSC32":
            ssc[self.id].position = int_pos
            ssc.commit(20)

    def set_float_pos(self, float_pos, velocity=10):
        #print "Setting %s to %.4f" % (self.name, float_pos)
        int_pos = int(self.min + float_pos*(self.max-self.min))

        self.set_int_pos(int_pos, velocity)



class Input(object):

    def __init__(self, map, idx, min=None, max=None, center=None, range=None):
        self.map = map
        self.idx = idx

        if center is not None and range is not None and min is None and max is None:
            min = center-range*0.5
            max = center+range*0.5
        elif min is not None and max is not None and range is None and center is None:
            pass
        else:
            raise Exception("Must specify min,max or center,range.")

        self.min = min
        self.max = max

    def is_available(self, input_maps):
        return self.map in input_maps

    def get_float(self, input_maps):
        v = input_maps[self.map][self.idx]

        v_frac = (v - self.min) / float(self.max-self.min)

        if v_frac > 1:
            v_frac = 1
        elif v_frac < 0:
            v_frac = 0

        return v_frac


class DirectMapping(object):

    def __init__(self, input, output, reverse=False, multiplier=1):
        self.input = input
        self.output = output
        self.reverse = reverse

    def update(self, input_maps):
        if self.input.is_available(input_maps):
            f = self.input.get_float(input_maps)
            if self.reverse:
                f = 1-f
            self.output.set_float_pos(f, 60)

class FakeSinMapping(object):

    def __init__(self, output):
        self.output = output

    def update(self, input_maps):
        f = math.sin(time.clock())*0.5+0.5
        self.output.set_float_pos(f)