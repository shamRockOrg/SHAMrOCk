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
        #self.s.set_rotation_rate(230,False)

    def on_connect(self, controller):
        print "Connected"

        # Enable gestures
        controller.enable_gesture(Leap.Gesture.TYPE_CIRCLE)
        controller.config.set("Gesture.Circle.MinRadius", 10.0)
        controller.config.set("Gesture.Circle.MinArc", 7.0)

        # controller.enable_gesture(Leap.Gesture.TYPE_KEY_TAP);
        # controller.enable_gesture(Leap.Gesture.TYPE_SCREEN_TAP);
        # controller.enable_gesture(Leap.Gesture.TYPE_SWIPE);

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
                    self.s.set_heading(10, False)
                else:
                    print "rotating counterclockwise"
                    self.s.set_heading(350, False)

    #                 # Calculate the angle swept since the last frame
    #                 swept_angle = 0
    #                 if circle.state != Leap.Gesture.STATE_START:
    #                     previous_update = CircleGesture(controller.frame(1).gesture(circle.id))
    #                     swept_angle =  (circle.progress - previous_update.progress) * 2 * Leap.PI

    #                 print "  Circle id: %d, %s, progress: %f, radius: %f, angle: %f degrees, %s" % (
    #                         gesture.id, self.state_names[gesture.state],
    #                         circle.progress, circle.radius, swept_angle * Leap.RAD_TO_DEG, clockwiseness)

        else:
            deadzone = 50
            wiggleZone = 15.0
            oldSpeed = 0.0
            oldAngle = 0.0
            if len(frame.hands) > 0:
                hand = frame.hands[0]
                if self.toSetUp:
                    self.x = hand.palm_position[0]
                    self.z = hand.palm_position[2]
                    self.change = False
                    print "X %d, Z %d" % (self.x, self.z)
                    self.toSetUp = False
                if self.change:
                    print "Press enter when your hand is ready"
                    try:
                        sys.stdin.readline()
                    except KeyboardInterrupt:
                        pass
                    # wait the next frame to get the base position of the hand
                    self.toSetUp = True
                    
                xpos = float(hand.palm_position[0]-self.x)
                zpos = float(-(hand.palm_position[2]-self.z))
                print xpos, zpos
                speed = math.sqrt(xpos**2 + zpos**2) * 0.75
                if speed < deadzone:
                    speed = 0.0
                if zpos == 0.0: zpos = 0.1
                angle = (math.degrees(math.atan(xpos / zpos))) % 360
                if  zpos < 0.0:
                    if xpos < 0.0:
                        angle = angle + 180.0
                    else:
                        angle = angle - 180.0


                if  not ((oldSpeed-wiggleZone) < speed < (oldSpeed+wiggleZone) and (oldAngle-wiggleZone) < angle <(oldAngle+wiggleZone)):
                    self.s.roll(int(speed), int(angle), 1, False)
                    print "angle %f" % (angle)
                oldSpeed = speed
                oldAngle = angle
            else:
                self.s.roll(0, 0, 1, False)
                print "Stop!!!!!"
                self.change = True
                #TODO: set the heading
                #TODO: calc the angle between both positions and move in that way
                #TODO2: move with hand angle
            #     if (hand.palm_position[0] > self.x+deadzone) and (hand.palm_position[2] > self.z+deadzone):
            #         if self.lastCommand != 1:
            #             self.s.roll(speed, 135, 1, False)
            #             self.lastCommand = 1
            #             print "Go right/Down!!!!!!"
            #     elif (hand.palm_position[0] > self.x+deadzone) and (hand.palm_position[2] < self.z-deadzone):
            #         if self.lastCommand != 2:
            #             self.s.roll(speed, 45, 1, False)
            #             self.lastCommand = 2
            #             print "Go right/Up!!!!!!"
            #     elif (hand.palm_position[0] < self.x-deadzone) and (hand.palm_position[2] > self.z+deadzone):
            #         if self.lastCommand != 3:
            #             self.s.roll(speed, 225, 1, False)
            #             self.lastCommand = 3
            #             print "Go left/Down!!!!!!"
            #     elif (hand.palm_position[0] < self.x-deadzone) and (hand.palm_position[2] < self.z-deadzone):
            #          if self.lastCommand != 4:
            #             self.s.roll(speed, 315, 1, False)
            #             self.lastCommand = 4
            #             print "Go left/Up!!!!!!"

            #     elif hand.palm_position[0] > self.x+deadzone:
            #         if self.lastCommand != 5:
            #             self.s.roll(speed, 90, 1, False)
            #             self.lastCommand = 5
            #             print "Go right!!!!!!"
            #     elif hand.palm_position[0] < self.x-deadzone:
            #         if self.lastCommand != 6:
            #             self.s.roll(speed, 270, 1, False)
            #             self.lastCommand = 6
            #             print "Go left!!!!!!"
            #     elif hand.palm_position[2] > self.z+deadzone:
            #         if self.lastCommand != 7: 
            #             self.s.roll(speed, 180, 1, False)
            #             self.lastCommand = 7
            #             print "Go down!!!!!!"
            #     elif hand.palm_position[2] < self.z-deadzone:
            #         if self.lastCommand != 8:
            #             self.s.roll(speed, 0, 1, False)
            #             self.lastCommand = 8
            #             print "Go up!!!!!!"
            #     else:
            #         if self.lastCommand != 0:
            #             self.s.roll(0, 0, 1, False)
            #             self.lastCommand = 0
            #             print "Stop!!!!!"
            # else:
            #     if self.lastCommand != 0:
            #         self.s.roll(0, 0, 1, False)
            #         self.lastCommand = 0
            #         print "Stop!!!!!"
            #         self.change = True



     
   

    # def on_frame(self, controller):
    #     # Get the most recent frame and report some basic information
    #     frame = controller.frame()
        
        
    #     if (frame.id % 10 == 0):   #It is done to print slower, it should be remove for testing
    #         print "Frame id: %d, timestamp: %d, hands: %d, fingers: %d, tools: %d, gestures: %d" % (
    #               frame.id, frame.timestamp, len(frame.hands), len(frame.fingers), len(frame.tools), len(frame.gestures()))

    #         # Get hands
    #         for hand in frame.hands:

    #             handType = "Left hand" if hand.is_left else "Right hand" 

    #             if (handType == "Right hand"):
    #                 print "------Average position %d" % (self.average)
    #                 print "------i %d" % (self.i)
    #                 self.myList[self.i] = hand.palm_position[1]
    #                 self.i = self.i+1
    #                 # if (self.average>100 and self.average<200):
    #                 #     self.s.roll(100, 100, 1, False)
    #                 # else:
    #                 #     self.s.roll(100, 100, 0, False)


    #                 if (self.i == 5):
    #                     self.i = 0
    #                     self.average = (self.myList[0]+self.myList[1]+self.myList[2]+self.myList[3]+self.myList[4])/5

    #             print "  %s, id %d, position: %s" % (
    #                 handType, hand.id, hand.palm_position)

    #             # Get the hand's normal vector and direction
    #             normal = hand.palm_normal
    #             direction = hand.direction

    #             # Calculate the hand's pitch, roll, and yaw angles
    #             print "  pitch: %f degrees, roll: %f degrees, yaw: %f degrees" % (
    #                 direction.pitch * Leap.RAD_TO_DEG,
    #                 normal.roll * Leap.RAD_TO_DEG,
    #                 direction.yaw * Leap.RAD_TO_DEG)

    #             # Get arm bone
    #             arm = hand.arm
    #             print "  Arm direction: %s, wrist position: %s, elbow position: %s" % (
    #                 arm.direction,
    #                 arm.wrist_position,
    #                 arm.elbow_position)

    #             # # Get fingers
    #             # for finger in hand.fingers:

    #             #     print "    %s finger, id: %d, length: %fmm, width: %fmm" % (
    #             #         self.finger_names[finger.type()],
    #             #         finger.id,
    #             #         finger.length,
    #             #         finger.width)

    #             #     # Get bones
    #             #     for b in range(0, 4):
    #             #         bone = finger.bone(b)
    #             #         print "      Bone: %s, start: %s, end: %s, direction: %s" % (
    #             #             self.bone_names[bone.type],
    #             #             bone.prev_joint,
    #             #             bone.next_joint,
    #             #             bone.direction)

    #         # # Get tools
    #         # for tool in frame.tools:

    #         #     print "  Tool id: %d, position: %s, direction: %s" % (
    #         #         tool.id, tool.tip_position, tool.direction)

    #         # Get gestures
    #         for gesture in frame.gestures():
    #             if gesture.type == Leap.Gesture.TYPE_CIRCLE:
    #                 circle = CircleGesture(gesture)

    #                 # Determine clock direction using the angle between the pointable and the circle normal
    #                 if circle.pointable.direction.angle_to(circle.normal) <= Leap.PI/2:
    #                     clockwiseness = "clockwise"
    #                 else:
    #                     clockwiseness = "counterclockwise"

    #                 # Calculate the angle swept since the last frame
    #                 swept_angle = 0
    #                 if circle.state != Leap.Gesture.STATE_START:
    #                     previous_update = CircleGesture(controller.frame(1).gesture(circle.id))
    #                     swept_angle =  (circle.progress - previous_update.progress) * 2 * Leap.PI

    #                 print "  Circle id: %d, %s, progress: %f, radius: %f, angle: %f degrees, %s" % (
    #                         gesture.id, self.state_names[gesture.state],
    #                         circle.progress, circle.radius, swept_angle * Leap.RAD_TO_DEG, clockwiseness)

    #             if gesture.type == Leap.Gesture.TYPE_SWIPE:
    #                 swipe = SwipeGesture(gesture)
    #                 print "  Swipe id: %d, state: %s, position: %s, direction: %s, speed: %f" % (
    #                         gesture.id, self.state_names[gesture.state],
    #                         swipe.position, swipe.direction, swipe.speed)

    #             if gesture.type == Leap.Gesture.TYPE_KEY_TAP:
    #                 keytap = KeyTapGesture(gesture)
    #                 print "  Key Tap id: %d, %s, position: %s, direction: %s" % (
    #                         gesture.id, self.state_names[gesture.state],
    #                         keytap.position, keytap.direction )

    #             if gesture.type == Leap.Gesture.TYPE_SCREEN_TAP:
    #                 screentap = ScreenTapGesture(gesture)
    #                 print "  Screen Tap id: %d, %s, position: %s, direction: %s" % (
    #                         gesture.id, self.state_names[gesture.state],
    #                         screentap.position, screentap.direction )

    #         if not (frame.hands.is_empty and frame.gestures().is_empty):
    #             print ""

    def state_string(self, state):
        if state == Leap.Gesture.STATE_START:
            return "STATE_START"

        if state == Leap.Gesture.STATE_UPDATE:
            return "STATE_UPDATE"

        if state == Leap.Gesture.STATE_STOP:
            return "STATE_STOP"

        if state == Leap.Gesture.STATE_INVALID:
            return "STATE_INVALID"

def main():
    # Create a sample listener and controller
    

    listener = SampleListener()
    controller = Leap.Controller()

    # Have the sample listener receive events from the controller
    controller.add_listener(listener)
    
    while 1:
        pass
    # Keep this process running until Enter is pressed
    # print "Press Enter to quit..."
    # try:
    #     sys.stdin.readline()
    # except KeyboardInterrupt:
    #     pass
    # finally:
    #     # Remove the sample listener when done
    #     controller.remove_listener(listener)


if __name__ == "__main__":
    main()
