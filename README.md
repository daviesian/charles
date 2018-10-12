# Charles - the animatronic head

<img src="charles.jpg" width="250" style="width: 250px; float:right; margin-left:20px;">

This is the Python code used to drive Charles, an animatronic head created by Hanson Robotics for the Graphics & Interaction Group in the University of Cambridge Computer Lab.  You can see him in action in [The Emotional Computer](http://www.sms.cam.ac.uk/media/1086225).

One of the key demonstrations of his abilities involves getting him to mimic the facial expressions of a human, which is why the key source file here is called `mimic.py`.  

We do this by analysing facial expressions using [a modified version of FaceLandmarkVid](https://github.com/daviesian/OpenFace/tree/master/exe/FaceLandmarkVid), part of the [OpenFace toolkit](https://github.com/TadasBaltrusaitis/OpenFace).  Our modified version publishes a few streams of the key facial features using ZeroMQ, and this Python code subscribes to them and causes the servos in Charles's head to move in accordance with the observed movements of the human.

Both programs therefore need to be running simultaneously.

##  Notes on the hardware

Charles has 26 servos to drive the various movements of his head, eyes, mouth, cheeks etc, in two groups.  The four largest (head movements and jaw opening) are driven through one serial interface using Dynamixel servos.  The remainder are controlled by an [SSC-32 servo controller](http://www.lynxmotion.com/p-395-ssc-32-servo-controller.aspx), which has a serial interface that we connect to using a USB-to-serial converter.

The result is that two COM ports are used by the Python code; the trick (on Windows at least) is to get the right drivers installed so that both of these are recognised, and then put the appropriate COM ports into `mimic.py`.  The SSC32_PORT is for the grey serial lead coming out of Charles's back, and the DYNAMIXEL_PORT is for the USB lead coming out of the beige control box.

On a Mac, you may need to install [a driver for the Prolific USB-Serial adapter](http://www.prolific.com.tw/US/ShowProduct.aspx?p_id=229&pcid=41).

The control box also takes no less than three power supply connections! One is at 6v, one at 7.5v and one at 16v.

## Getting started

The sequence, therefore, is roughly:

* Connect up the power supplies
* Connect the USB/serial cables to the laptop (typically via a hub)
* Turn on the two power switches on the beige control box.
* Make sure that the serial drivers are working by checking them in Device Manager.  If there is a warning sign on the Prolific one, then try installing the old driver until it works.
* Put the two COM port numbers into `mimic.py`
* Run the modified FaceLandmarkVid, and check it is tracking your face through the camera
* Run `mimic.py` and Charles should start to respond.
