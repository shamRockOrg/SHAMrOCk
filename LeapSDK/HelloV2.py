#import C:\Pervasive Computing\LeapSDK\lib\Leap

################################################################################
# Copyright (C) 2012-2013 Leap Motion, Inc. All rights reserved.               #
# Leap Motion proprietary and confidential. Not for distribution.              #
# Use subject to the terms of the Leap Motion SDK Agreement available at       #
# https://developer.leapmotion.com/sdk_agreement, or another agreement         #
# between Leap Motion and you, your company or other organization.             #
################################################################################

import Leap, sys, thread, time, math
import spheroDriver, bluetooth
from Leap import CircleGesture, KeyTapGesture, ScreenTapGesture, SwipeGesture


CONST_DEADZONE = 50
CONST_DELTA = 15.0
CONST_SPEEDFACTOR = 1
SPHEROVERSION = ""

class SampleListener(Leap.Listener):
    finger_names = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
    bone_names = ['Metacarpal', 'Proximal', 'Intermediate', 'Distal']
    state_names = ['STATE_INVALID', 'STATE_START', 'STATE_UPDATE', 'STATE_END']
    myList=[0,0,0,0,0]
    average = 0
    i = 0
    change = True
    x,z = 0,0
    lastCommand = 0
    toSetUp = False
    oldSpeed = 0.0
    oldAngle = 0.0
    isStop = False

    def on_init(self, controller):
        print "Initialized"
        self.s = spheroDriver.Sphero()
        try:
            self.s.connect()
            
        except IOError:
            self.s.disconnect()

            try:
                self.s.connect()
        
            except bluetooth.btcommon.BluetoothError as error:
                sys.stdout.write(error)
                sys.stdout.flush()
                time.sleep(5.0)
                sys.exit(1)

        self.s.set_back_led(255,False)


    def on_connect(self, controller):
        print "Connected"

        # Enable gestures
        controller.enable_gesture(Leap.Gesture.TYPE_CIRCLE)
        controller.config.set("Gesture.Circle.MinRadius", 10.0)
        controller.config.set("Gesture.Circle.MinArc", 7.0)


    def on_disconnect(self, controller):
        # Note: not dispatched when running in a debugger.
        print "Disconnected"

    def on_exit(self, controller):
        print "Exited"

    def on_frame(self, controller):
        # Get the most recent frame and report some basic information
        frame = controller.frame()

        #we only have circule gestures
        if len(frame.gestures()) > 0:
            circle = CircleGesture(frame.gestures()[0])
            if self.lastCommand != 0:
                self.s.roll(0, 0, 1, False)
                self.lastCommand = 0
                
            # Determine clock direction using the angle between the pointable and the circle normal
            if (frame.id % 15 == 0): 
                if circle.pointable.direction.angle_to(circle.normal) <= Leap.PI/2:
                    print "rotating clockwise"
                    #self.s.set_heading(10, False)
                    self.s.roll(0, 10, 1, False)
                    self.s.roll(0, 10, 1, False)
                    self.s.roll(0, 10, 1, False)
                    self.s.roll(0, 10, 1, False)
                else:
                    print "rotating counterclockwise"
                    #self.s.set_heading(350, False)
                    self.s.roll(0, 350, 1, False)
                    self.s.roll(0, 350, 1, False)
                    self.s.roll(0, 350, 1, False)
                    self.s.roll(0, 350, 1, False)
                self.s.set_heading(0, False)
        else:
            if len(frame.hands) > 0:
                hand = frame.hands[0]
                
                if self.toSetUp:
                    # set origin
                    self.x = hand.palm_position[0]
                    self.z = hand.palm_position[2]
                    self.change = False
                    print "X:", self.x, "Z:", self.z
                    self.toSetUp = False

                if self.change:
                    print "Press enter when your hand is ready"
                    try:
                        sys.stdin.readline()
                    except KeyboardInterrupt:
                        pass
                    # wait the next frame to get the base position of the hand
                    self.toSetUp = True
                
                xpos = float(  hand.palm_position[0]-self.x)
                zpos = float(-(hand.palm_position[2]-self.z))

                # length of polar vector
                speed = math.sqrt(xpos**2 + zpos**2) * CONST_SPEEDFACTOR
                if speed < CONST_DEADZONE:
                    speed = 0.0

                if zpos == 0.0:
                    # Fix division by 0
                    zpos = 0.1

                # angle of polar vector
                angle = (math.degrees(math.atan(xpos / zpos))) % 360
                
                if  zpos < 0.0:
                    if xpos < 0.0:
                        angle = angle + 180.0
                    else:
                        angle = angle - 180.0

                if not self.inside_deadzone(speed, angle):
                    # all good
                    self.s.roll(int(speed), int(angle), 1, False)
                    self.isStop = False
                    print "angle: %f and speed %f" % (angle, speed)
                
                self.oldSpeed = speed
                self.oldAngle = angle
            else:
                # Look, no hands!
                if not self.isStop:
                    self.s.roll(0, 0, 1, False)
                    self.isStop = True
                    print "Stop!!!!!"
                    self.change = True
      
    def state_string(self, state):
        if state == Leap.Gesture.STATE_START:
            return "STATE_START"

        if state == Leap.Gesture.STATE_UPDATE:
            return "STATE_UPDATE"

        if state == Leap.Gesture.STATE_STOP:
            return "STATE_STOP"

        if state == Leap.Gesture.STATE_INVALID:
            return "STATE_INVALID"

    def inside_deadzone(self, speed, angle):
        lowerSpeed = self.oldSpeed-CONST_DELTA
        upperSpeed = self.oldSpeed+CONST_DELTA
        lowerAngle = self.oldAngle-CONST_DELTA
        upperAngle = self.oldAngle+CONST_DELTA
        return lowerSpeed < speed < upperSpeed and lowerAngle < angle < upperAngle

def main():
    # Create a sample listener and controller
    listener = SampleListener()
    controller = Leap.Controller()

    # Have the sample listener receive events from the controller
    controller.add_listener(listener)
    
    while 1:
        pass
        

if __name__ == "__main__":
    main()
