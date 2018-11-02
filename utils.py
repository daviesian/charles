import time
import math


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
    """ Scaled mapping from an Input to one of Charles's outputs """

    def __init__(self, input, outputs, reverse=False, multiplier=1):
        self.input = input
        self.outputs = outputs
        self.reverse = reverse

    def update(self, input_maps, velocity=25):
        if self.input.is_available(input_maps):
            f = self.input.get_float(input_maps)
            if self.reverse:
                f = 1-f
            for o in self.outputs:
                o.set_float_pos(f, velocity)


class FakeSinMapping(object):

    def __init__(self, output):
        self.output = output

    def update(self, input_maps):
        f = math.sin(time.clock())*0.5+0.5
        self.output.set_float_pos(f)