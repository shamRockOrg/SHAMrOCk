
################################################################################
# Copyright (C) 2012-2013 Leap Motion, Inc. All rights reserved.               #
# Leap Motion proprietary and confidential. Not for distribution.              #
# Use subject to the terms of the Leap Motion SDK Agreement available at       #
# https://developer.leapmotion.com/sdk_agreement, or another agreement         #
# between Leap Motion and you, your company or other organization.             #
################################################################################

###############################################################################
# Created a LeapMotion driver based on the developer's driver                 #
# in order to control Sphero through its driver (used unofficial driver)      #
###############################################################################


import Leap, sys, thread, time, math
import driver, bluetooth
from Leap import CircleGesture


CONST_DEADZONE = 40 #Radius in mm from the center point where the ball will not move
CONST_DELTA = 15.0  #If the hand position changes more than CONST_DELTA (mm). A different command will be send.
                    #This avoids that small shakes of our hand modify unintentionally direction.
CONST_SPEEDFACTOR = 0.75  #Final speed will be multiplied
#SPHEROVERSION = ""

class SampleListener(Leap.Listener):
    state_names = ['STATE_INVALID', 'STATE_START', 'STATE_UPDATE', 'STATE_END']
    change = True   #If the speed or direction has changed
    x,z = 0,0   #Center position
    lastCommand = 0
    toSetUp = False
    oldSpeed = 0.0
    oldAngle = 0.0
    isStop = False
    version = 2     #Sphero version

    #Initialize Sphero
    def on_init(self, controller):
        print "Initialized"
        self.s = driver.Sphero()
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

        self.s.set_back_led(255)
        self.s.set_rgb_led(0,0,0,0)


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

    #Every frame executes:
    def on_frame(self, controller):
        # Get the most recent frame and report some basic information
        frame = controller.frame()

        #we only have circule gestures to set the heading
        if len(frame.gestures()) > 0 and self.isStop:
            circle = CircleGesture(frame.gestures()[0])
            if self.lastCommand != 0:
                self.rollAndColor(0, 0, 1)
                self.lastCommand = 0
                
            # Determine clock direction using the angle between the pointable and the circle normal
            if (frame.id % 15 == 0): 
                if circle.pointable.direction.angle_to(circle.normal) <= Leap.PI/2:
                    print "rotating clockwise"
                    if self.version == 1:
                        self.s.set_heading(10)
                    else:
                        self.rollAndColor(0, 10, 1)
                        self.rollAndColor(0, 10, 1)
                        self.rollAndColor(0, 10, 1)
                        self.rollAndColor(0, 10, 1)
                        self.s.set_heading(0)
                else:
                    print "rotating counterclockwise"
                    if self.version == 1:
                        self.s.set_heading(350)
                    else:
                        self.rollAndColor(0, 350, 1)
                        self.rollAndColor(0, 350, 1)
                        self.rollAndColor(0, 350, 1)
                        self.rollAndColor(0, 350, 1)
        
                        self.s.set_heading(0)
        #If there is not any gesture
        else:
            if len(frame.hands) > 0:
                hand = frame.hands[0]
                
                #We set the hand center position when we press enter
                if self.toSetUp:
                    # set origo
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
                
                #Coordinate of our hand with the center position
                xpos = float(  hand.palm_position[0]-self.x)
                zpos = float(-(hand.palm_position[2]-self.z))

                # length of polar vector
                speed = math.sqrt(xpos**2 + zpos**2)
                if speed > CONST_DEADZONE:
                    #outside deadzone
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
                    if self.version == 1:
                        if not self.inside_deadzone(speed, angle): #value has changed, this is not to calc if it is inside deadzone
                            # all good
                            self.rollAndColor(int(speed * CONST_SPEEDFACTOR), int(angle), 1)
                            self.isStop = False
                            print "angle: %f and speed %f" % (angle, speed)
                            self.oldSpeed = speed
                            self.oldAngle = angle
                    else:
                        self.rollAndColor(int(speed * CONST_SPEEDFACTOR), int(angle), 1)
                        self.isStop = False
                        print "angle: %f and speed %f" % (angle, speed)
                        self.oldSpeed = speed
                        self.oldAngle = angle
                else:
                    #inside the deadzone
                    if not self.isStop:
                        self.rollAndColor(0, 0, 1)
                        self.isStop = True
                        print "Stop!!!!!"
                        

            else:
                # Look, no hands!
                if not self.isStop:
                    self.rollAndColor(0, 0, 1)
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

    def rollAndColor(self,speed,angle,mode):
        # 0 speed -> blue
        # gradient between
        # full speed -> red
        red = int((speed*1.5+50)%255)
        blue = int((-speed%255+200)%255)
        print "red %d,      blue %d" %(red,blue)
        self.s.set_rgb_led(red,0,blue,0)
        self.s.roll(speed,angle,mode)

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
