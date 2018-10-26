#! /usr/bin/env python3
#
#  Capture motion information from FaceLandmarkVidZmq
#  and log it to a CSV file so we can calibrate limits etc.
#
#  Note that different readings may update at different rates
#  so each row gives the last-known value for that column, and
#  doesn't necessarily imply a new value has been received.
#

import zmq
from time import sleep
import queue
import threading
import functools
import csv
import sys

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
msg_thread.daemon=True
msg_thread.start()

au_thread = threading.Thread(target=functools.partial(get_incoming, socket_aus, incoming_aus))
au_thread.daemon=True
au_thread.start()

reset_thread = threading.Thread(target=watch_reset)
reset_thread.daemon=True
reset_thread.start()



###########################################
### Capture forever to the named CSV file.
###########################################

if len(sys.argv) < 2:
    sys.stderr.write("Usage:  {} CSV_FILE".format(sys.argv[0]))
    sys.exit(1)

csv_file = sys.argv[1]

current_vals = {}

def update_current_vals(current_vals, timeout=0.3):
    """
    Tries to read any messages in the queues,
    (which may timeout), and if it finds changes it
    updates current_vals and returns True.

    Note that here, unlike in mimic.py, we don't split the
    AUs off into a sperate sub-dictionary.
    """
    updated = False
    # Global/local messages first
    try:
        msg_string = incoming_msgs.get(timeout=timeout)
        msg_vals = msg_string.split()
        for i, f in enumerate(msg_vals[1:]):
            key = "{}_{}".format(msg_vals[0], i)
            current_vals[key] = float(f)
        updated = True
    except queue.Empty:
        pass

    # Action units
    try:
        au_string = incoming_aus.get(timeout=timeout)
        au_vals = au_string.split()
        for f in au_vals[1:]:
            fs = f.split(":")
            current_vals[fs[0]] = float(fs[1])
        updated = True
    except queue.Empty:
        pass

    return updated


with open(csv_file, "w") as csv_file:
    # Give us a chance to capture field names from the first few
    print("Initialising - waiting for readings")
    for i in range(5):
        while not update_current_vals(current_vals, 2):
            pass

    print("Capturing to {}".format(csv_file))
    csv_writer = csv.DictWriter(csv_file, current_vals.keys())
    csv_writer.writeheader()   
    while True:
        if update_current_vals(current_vals, 0.03):
            csv_writer.writerow(current_vals)
            print(".", end=" ")

