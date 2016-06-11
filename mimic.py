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

SSC32_PORT = 'COM9'
DYNAMIXEL_PORT = 'COM7'


##########################
### Define servo outputs
##########################

outputs = {

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
    "EYES_UP_DOWN": Output(10, min=1225, max=2200, default=1700, type="SSC32"),

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
    "NOD": Output(26, min=147, max=905, default=350, type="DYNAMIXEL"),
    "JAW": Output(27, min=286, max=574, default=318, type="DYNAMIXEL", velocity=5),
}

##########################
### Define OpenFace inputs
##########################

# AU Intensity is 0-5 or 0-1

inputs = {
    "EULER_X": Input("GLOBAL", 1, center=0, range=0.8), # +ve: Nod Down
    "EULER_Y": Input("GLOBAL", 2, center=0, range=0.8), # +ve: Turn Right
    "EULER_Z": Input("GLOBAL", 3, center=0, range=0.8), # +ve: Tilt Left
    "INNER_BROW_RAISE": Input("AU", "AU01", min=3, max=4, expand=True),
    #"OUTER_BROW_RAISE": Input("AU", "AU02", min=1.5, max=3),
    #"BROW_LOWERER": Input("AU", "AU04", min=1.5, max=3),
    #"UPPER_LID_RAISER": Input("AU", "AU05", min=1.5, max=3),
    "CHEEK_RAISER": Input("AU", "AU06", min=0, max=2),
    "NOSE_WRINKLER": Input("AU", "AU09", min=0, max=2),
    "UPPER_LIP_RAISER": Input("AU", "AU10", min=0, max=1),
    #"LIP_CORNER_PULLER": Input("AU", "AU12", min=1.5, max=3),
    #"DIMPLER": Input("AU", "AU14", min=1.5, max=3),
    #"LIP_CORNER_DEPRESSOR": Input("AU", "AU15", min=1.5, max=3),
    #"CHIN_RAISER": Input("AU", "AU17", min=1.5, max=3),
    #"LIP_STRETCHER": Input("AU", "AU20", min=1.5, max=3),
    #"LIPS_PART": Input("AU", "AU25", min=1.5, max=3),
    "JAW_DROP": Input("AU", "AU26", min=0.5, max=1.5),
    #"BLINK": Input("AU", "AU45", min=0, max=1),
}

##########################
### Define mappings from inputs to outputs
##########################

mappings = [

    # Head pose and eyes

    DirectMapping(inputs["EULER_X"], [outputs["NOD"], outputs["EYES_UP_DOWN"]], reverse=True),
    DirectMapping(inputs["EULER_Y"], [outputs["TURN"],
                                      outputs["LEFT_EYE_TURN"],
                                      outputs["RIGHT_EYE_TURN"]], reverse=not MIRROR),
    DirectMapping(inputs["EULER_Z"], [outputs["TILT"]], reverse=not MIRROR),

    # Brows

    DirectMapping(inputs["INNER_BROW_RAISE"], [outputs["CENTER_BROW"],
                                               outputs["INNER_BROW_LEFT"],
                                               outputs["OUTER_BROW_LEFT"],
                                               outputs["INNER_BROW_RIGHT"],
                                               outputs["OUTER_BROW_RIGHT"]], reverse=True),

    # Mid face

    DirectMapping(inputs["CHEEK_RAISER"], [outputs["SQUINT_RIGHT"], outputs["SQUINT_LEFT"]]),
    DirectMapping(inputs["NOSE_WRINKLER"], [outputs["SNEER_RIGHT"], outputs["SNEER_LEFT"]]),

    # Mouth

    DirectMapping(inputs["UPPER_LIP_RAISER"], [outputs["UPPER_LIP_LEFT"],
                                               outputs["UPPER_LIP_CENTER"],
                                               outputs["UPPER_LIP_RIGHT"],
                                               outputs["SMILE_FROWN_RIGHT"],
                                               outputs["SMILE_FROWN_LEFT"]]),
    DirectMapping(inputs["JAW_DROP"], [outputs["JAW"]]),
]

##########################
### Init SSC-32 servos
##########################

ssc = None
try:
    ssc = ssc32.SSC32(SSC32_PORT, 115200, count=32)
    utils.ssc = ssc

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
    current_vals = {}

    for o in outputs.values():
        o.initialise()

    for o in outputs.values():
        if o.type == "DYNAMIXEL":
            while dyn_raw.get_is_moving(dyn.dyn_serial,o.id):
                sleep(0.01)

    ssc[0].position = 1000
    ssc.commit(0)
    print "Done"
except Exception as e:
    print e




##########################
### Connect to OpenFace server through ZeroMQ
##########################

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket_aus = context.socket(zmq.SUB)
socket_reset = context.socket(zmq.SUB)

print("Connecting to OpenFace server...")
socket.connect("tcp://localhost:5556")
socket_aus.connect("tcp://localhost:5556")
socket_reset.connect("tcp://localhost:5556")

# We want all messages from the server
socket.setsockopt_string(zmq.SUBSCRIBE, u"GLOBAL")
socket.setsockopt_string(zmq.SUBSCRIBE, u"LOCAL")
socket_aus.setsockopt_string(zmq.SUBSCRIBE, u"AU")
socket_reset.setsockopt_string(zmq.SUBSCRIBE, u"RESET")


##########################
### Receive messages on a separate thread
##########################


incoming_msgs = Queue.Queue(2)
incoming_aus = Queue.Queue(2)
reset = False

def get_incoming(socket, q):
    while True:
        string = socket.recv_string()
        # Drop new messages if we're not ready for them.
        if not q.full():
            q.put_nowait(string)

def watch_reset():
    global reset
    while True:
        socket_reset.recv_string()
        reset = True

threading.Thread(target=functools.partial(get_incoming, socket, incoming_msgs)).start()
threading.Thread(target=functools.partial(get_incoming, socket_aus, incoming_aus)).start()
threading.Thread(target=watch_reset).start()



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

    for m in mappings:
        m.update(current_vals)

    if reset:
        inputs["EULER_X"].min = current_vals["GLOBAL"][1]-inputs["EULER_X"].range/2
        inputs["EULER_X"].max = current_vals["GLOBAL"][1]+inputs["EULER_X"].range/2
        reset = False

