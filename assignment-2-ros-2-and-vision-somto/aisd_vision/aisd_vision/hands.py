import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import mediapipe as mp
mp_hands = mp.solutions.hands

from aisd_msgs.msg import Hand

class Hands(Node):

    def __init__(self):
        super().__init__('hands')
        # Subscribe to camera frames from ImagePublisher
        self.subscription = self.create_subscription(
            Image,
            'video_frames',
            self.listener_callback,
            1)
        self.subscription  # prevent unused variable warning
        self.br = CvBridge()
        self.hand_publisher = self.create_publisher(Hand, 'cmd_hand',10)
        # make the hand model once so it can track the hand between frames
        self.myhands = mp_hands.Hands(
            model_complexity=0,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5)

    def listener_callback(self, msg):
        image = self.br.imgmsg_to_cv2(msg)

        PINKY_FINGER_TIP = 20  # pinky landmark index
        INDEX_FINGER_TIP = 8  # index landmark index

        # mark image not writeable so it passes by reference (faster)
        image.flags.writeable = False
        # mediapipe wants RGB, opencv gives BGR
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.myhands.process(image)
        if results.multi_hand_landmarks:
            # publish the hand position in terms of index finger and pinky
            msg = Hand()
            msg.xpinky = results.multi_hand_landmarks[0].landmark[PINKY_FINGER_TIP].x
            msg.xindex = results.multi_hand_landmarks[0].landmark[INDEX_FINGER_TIP].x
            lm = results.multi_hand_landmarks[0].landmark
            # fast = only index up (tip above its middle joint), other fingers curled
            index_up = lm[8].y < lm[6].y      # index tip above its middle joint
            middle_down = lm[12].y > lm[10].y  # middle tip below its joint (curled)
            ring_down = lm[16].y > lm[14].y    # ring curled
            pinky_down = lm[20].y > lm[18].y   # pinky curled
            msg.fast = index_up and middle_down and ring_down and pinky_down
            if msg.fast:
                msg.xpinky = lm[17].x  # pinky is curled, use its knuckle instead
            if self.hand_publisher.get_subscription_count() > 0:
                self.hand_publisher.publish(msg)
            else:
                self.get_logger().info('waiting for subcriber')



def main(args=None):
    rclpy.init(args=args)

    hands = Hands()

    rclpy.spin(hands)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    hands.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
