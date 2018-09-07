#! /usr/bin/env python

import zmq
from time import sleep
import Queue
import threading
import functools

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
### Log forever.
##########################

while True:
    string = incoming_msgs.get()
    print("MSGS: {}".format(string))
    # vals = string.split()
    # current_vals[vals[0]] = [float(f) for f in vals[1:]]

    string = incoming_aus.get()
    print("AUS: {}".format(string))

