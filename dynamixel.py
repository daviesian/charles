from pydynamixel import dynamixel as dyn_raw

# This is horrible. But will do for now.
dyn_serial = None


def init_dynamixel_serial(port):
    global dyn_serial
    try:
        dyn_serial = dyn_raw.get_serial_for_url(port)
        dyn_serial.baudrate = 117647
    except dyn_raw.DynamixelException as e:
        print(e)


def init_dynamixel_servo(id):
    try:
        dyn_raw.init(dyn_serial, id, False, 1)
    except dyn_raw.DynamixelException as e:
        print(e)


def update_dynamixel(id, val, velocity=10):
    dyn_raw.set_velocity(dyn_serial, id, velocity, verbose=True)
    dyn_raw.set_position(dyn_serial, id, val, verbose=True)
    dyn_raw.send_action_packet(dyn_serial)
