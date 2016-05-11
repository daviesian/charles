import zmq
from time import sleep
from pydynamixel import dynamixel as dyn_raw
import Queue
import threading
import ssc32
import functools

from utils import *
import utils

# Do we want Charles to mirror or copy?
MIRROR = True


##########################
### Define servo outputs
##########################

outputs = {
    "TURN": Output(24, "TURN", range=800, default=500, type="DYNAMIXEL"),
    "TILT": Output(25, "TILT", range=800, default=663, type="DYNAMIXEL"),
    "NOD": Output(26, "NOD", min=147, max=905, default=350, type="DYNAMIXEL"),
    "LEFT_EYE_TURN": Output(7, "LEFT_EYE_TURN", default=1460, range=450, type="SSC32"),
    "RIGHT_EYE_TURN": Output(6, "RIGHT_EYE_TURN", default=1560, range=500, type="SSC32"),
    "CENTER_BROW": Output(1, "CENTER_BROW", default=1550, min=2025, max=1175, type="SSC32"),
    "INNER_BROW_LEFT": Output(3, "CENTER_BROW", default=1275, min=800, max=1800, type="SSC32"),
    "INNER_BROW_RIGHT": Output(2, "INNER_BROW_RIGHT", default=1750, min=2225, max=1450, type="SSC32"),
    "OUTER_BROW_LEFT": Output(5, "OUTER_BROW_LEFT", default=1500, min=1175, max=1750, type="SSC32"),
    "OUTER_BROW_RIGHT": Output(4, "OUTER_BROW_RIGHT", default=1225, min=1775, max=975, type="SSC32"),
}

##########################
### Define OpenFace inputs
##########################

inputs = {
    "EULER_X": Input("GLOBAL", 1, center=-0.5, range=0.8), # +ve: Nod Down
    "EULER_Y": Input("GLOBAL", 2, center=0, range=0.8), # +ve: Turn Right
    "EULER_Z": Input("GLOBAL", 3, center=0, range=0.8), # +ve: Tilt Left
    "BROW_RAISE": Input("AU", "AU01", min=1.5, max=3)
}

##########################
### Define mappings from inputs to outputs
##########################

mappings = [
    DirectMapping(inputs["EULER_X"], outputs["NOD"], reverse=True),
    DirectMapping(inputs["EULER_Y"], outputs["TURN"], reverse=not MIRROR),
    DirectMapping(inputs["EULER_Z"], outputs["TILT"], reverse=not MIRROR),
    DirectMapping(inputs["EULER_Y"], outputs["LEFT_EYE_TURN"]),
    DirectMapping(inputs["EULER_Y"], outputs["RIGHT_EYE_TURN"]),
    DirectMapping(inputs["BROW_RAISE"], outputs["CENTER_BROW"], reverse=True),
    DirectMapping(inputs["BROW_RAISE"], outputs["INNER_BROW_LEFT"], reverse=True),
    DirectMapping(inputs["BROW_RAISE"], outputs["OUTER_BROW_LEFT"], reverse=True),
    DirectMapping(inputs["BROW_RAISE"], outputs["INNER_BROW_RIGHT"], reverse=True),
    DirectMapping(inputs["BROW_RAISE"], outputs["OUTER_BROW_RIGHT"], reverse=True),
]

##########################
### Init SSC-32 servos
##########################

ssc = None
try:
    ssc = ssc32.SSC32('COM7', 115200, count=32)
    ssc[0].position=2000
    ssc.commit(100)
    sleep(0.1)
    ssc[0].position=1000
    ssc.commit(100)
    sleep(0.1)
    ssc[0].position=0
    ssc.commit(100)
    sleep(0.1)

    utils.ssc = ssc

except Exception as e:
    print "Could not initialise servos: %s" % e

##########################
### Init dynamixel servos
##########################

try:
    dyn.init_dynamixel_serial("COM4")
    dyn.init_dynamixel_servo(24)
    dyn.init_dynamixel_servo(25)
    dyn.init_dynamixel_servo(26)

##########################
### Slowly move to default positions
##########################

    current_vals = {}

    for o in outputs.values():
        o.set_int_pos(o.default, 20)

    for o in outputs.values():
        if o.type == "DYNAMIXEL":
            while dyn_raw.get_is_moving(dyn.dyn_serial,o.id):
                sleep(0.01)
except Exception as e:
    print e




##########################
### Connect to OpenFace server through ZeroMQ
##########################

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket_aus = context.socket(zmq.SUB)

print("Connecting to OpenFace server...")
socket.connect("tcp://localhost:5556")
socket_aus.connect("tcp://localhost:5556")

# We want all messages from the server
socket.setsockopt_string(zmq.SUBSCRIBE, u"GLOBAL")
socket.setsockopt_string(zmq.SUBSCRIBE, u"LOCAL")
socket_aus.setsockopt_string(zmq.SUBSCRIBE, u"AU")


##########################
### Receive messages on a separate thread
##########################


incoming_msgs = Queue.Queue(2)
incoming_aus = Queue.Queue(2)

def get_incoming(socket, q):
    while True:
        string = socket.recv_string()
        # Drop new messages if we're not ready for them.
        if not q.full():
            q.put_nowait(string)


threading.Thread(target=functools.partial(get_incoming, socket, incoming_msgs)).start()
threading.Thread(target=functools.partial(get_incoming, socket_aus, incoming_aus)).start()



##########################
### Mimic forever.
##########################

while True:
    string = incoming_msgs.get()

    vals = string.split()
    current_vals[vals[0]] = [float(f) for f in vals[1:]]

    string = incoming_aus.get()

    vals = string.split()
    current_vals[vals[0]] = current_vals.get(vals[0], {})
    for f in vals[1:]:
        fs = f.split(":")
        current_vals[vals[0]][fs[0]] = float(fs[1])

    print current_vals["AU"]["AU01"]

    for m in mappings:
        m.update(current_vals)

