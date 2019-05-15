#! /usr/bin/env python

from __future__ import division
from __future__ import print_function
from future import standard_library

standard_library.install_aliases()
from past.utils import old_div
import zmq
from time import sleep
import queue
import sys
import threading
import functools

from utils import Input, DirectMapping, FakeSinMapping
from charles import Charles

# Do we want Charles to mirror or copy?
MIRROR = True

#######################################################
# Set up Charles and initialise him to central position
#######################################################

charles = Charles(mirror=MIRROR)
charles.initialise()

##########################
### Define OpenFace inputs
##########################

# AU Intensity is 0-5 or 0-1

inputs = {
    "EULER_X": Input("GLOBAL", 1, center=-0.2, range=0.8),  # -ve: Nod Down
    "EULER_Y": Input("GLOBAL", 2, center=0, range=0.8),  # +ve: Turn Right
    "EULER_Z": Input("GLOBAL", 3, center=0, range=0.8),  # +ve: Tilt Left
    "INNER_BROW_RAISE": Input("AU", "AU01", min=0, max=5, expand=True),
    "OUTER_BROW_RAISE": Input("AU", "AU02", min=0, max=4.5),
    "BROW_LOWERER": Input("AU", "AU04", min=0, max=2.5),
    "UPPER_LID_RAISER": Input("AU", "AU05", min=-0.5, max=1.4),
    "CHEEK_RAISER": Input("AU", "AU06", min=0, max=2.6),
    # "LID_TIGHTENER": Input("AU", "AU07", min=0, max=5),
    "NOSE_WRINKLER": Input("AU", "AU09", min=0, max=1.8),
    "UPPER_LIP_RAISER": Input("AU", "AU10", min=0, max=4),
    "LIP_CORNER_PULLER": Input("AU", "AU12", min=0, max=3.2),
    # "DIMPLER": Input("AU", "AU14", min=1.5, max=3),
    # "LIP_CORNER_DEPRESSOR": Input("AU", "AU15", min=1.5, max=3),
    # "CHIN_RAISER": Input("AU", "AU17", min=1.5, max=3),
    "LIP_STRETCHER": Input("AU", "AU20", min=1.5, max=3),
    # "LIP_TIGHTENER": Input("AU", "AU23", min=0, max=3),
    # "LIPS_PART": Input("AU", "AU25", min=1.5, max=3),
    "JAW_DROP": Input("AU", "AU26", min=0.1, max=2.6),
    # "BLINK": Input("AU", "AU45", min=0, max=1),
}

##########################################
### Define mappings from inputs to outputs
##########################################

# For brevity:
outputs = charles.outputs

mappings = [
    # Head pose and eyes
    DirectMapping(inputs["EULER_X"], [outputs["NOD"], outputs["EYES_UP_DOWN"]], reverse=True),
    DirectMapping(
        inputs["EULER_Y"], [outputs["TURN"], outputs["LEFT_EYE_TURN"], outputs["RIGHT_EYE_TURN"]], 
        reverse=not MIRROR
    ),
    DirectMapping(inputs["EULER_Z"], [outputs["TILT"]], reverse=not MIRROR),
    DirectMapping(inputs["UPPER_LID_RAISER"], [outputs["UPPER_EYE_LIDS"]]),
    DirectMapping(inputs["UPPER_LID_RAISER"], [outputs["LOWER_EYE_LIDS"]], reverse=True),
    # Brows
    DirectMapping(
        inputs["INNER_BROW_RAISE"],
        [
            outputs["CENTER_BROW"],
            outputs["INNER_BROW_LEFT"],
            outputs["OUTER_BROW_LEFT"],
            outputs["INNER_BROW_RIGHT"],
            outputs["OUTER_BROW_RIGHT"],
        ],
        reverse=True,
    ),
    # Mid face
    DirectMapping(inputs["CHEEK_RAISER"], [outputs["SQUINT_RIGHT"], outputs["SQUINT_LEFT"]]),
    DirectMapping(inputs["NOSE_WRINKLER"], [outputs["CENTER_BROW"], outputs["SNEER_RIGHT"], outputs["SNEER_LEFT"]]),
    # Mouth
    DirectMapping(inputs["LIP_CORNER_PULLER"], [outputs["EE_OO"]]),
    DirectMapping(
        inputs["UPPER_LIP_RAISER"],
        [
            outputs["UPPER_LIP_LEFT"],
            outputs["UPPER_LIP_CENTER"],
            outputs["UPPER_LIP_RIGHT"],
            outputs["SMILE_FROWN_RIGHT"],
            outputs["SMILE_FROWN_LEFT"],
        ],
    ),
    DirectMapping(inputs["JAW_DROP"], [outputs["JAW"]]),
]


#############################################
### Connect to OpenFace server through ZeroMQ
#############################################

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


##########################################################
### Receive messages from each socket on a separate thread
### and add them to queues for processing by main thread.
##########################################################


incoming_msgs = queue.Queue(2)
incoming_aus = queue.Queue(2)
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


msg_thread = threading.Thread(target=functools.partial(get_incoming, socket, incoming_msgs))
msg_thread.daemon = True
msg_thread.start()

au_thread = threading.Thread(target=functools.partial(get_incoming, socket_aus, incoming_aus))
au_thread.daemon = True
au_thread.start()

reset_thread = threading.Thread(target=watch_reset)
reset_thread.daemon = True
reset_thread.start()


##########################
### Mimic forever.
##########################

# How fast should he try to react?
# You can give a velocity as a parameter if wanted.
velocity = 20
if len(sys.argv) > 1:
    velocity = int(sys.argv[1])

current_vals = {}
while True:
    updated = False
    # Global messages first
    try:
        msg_string = incoming_msgs.get(timeout=0.1)
        msg_vals = msg_string.split()
        current_vals[msg_vals[0]] = [float(f) for f in msg_vals[1:]]
        updated = True
    except queue.Empty:
        print("Empty msgs")
        pass

    # Action units
    try:
        au_string = incoming_aus.get(timeout=0.1)
        # print(au_string)
        au_vals = au_string.split()
        # Make a dictionary for AUs called 'AU' if it doesn't exist
        current_vals[au_vals[0]] = current_vals.get(au_vals[0], {})
        for f in au_vals[1:]:
            fs = f.split(":")
            current_vals[au_vals[0]][fs[0]] = float(fs[1])
        updated = True
    except queue.Empty:
        print("Empty AUs")
        pass

    if updated:
        for m in mappings:
            m.update(current_vals, velocity)

    if reset:
        inputs["EULER_X"].min = current_vals["GLOBAL"][1] - inputs["EULER_X"].range / 2
        inputs["EULER_X"].max = current_vals["GLOBAL"][1] + inputs["EULER_X"].range / 2
        reset = False

