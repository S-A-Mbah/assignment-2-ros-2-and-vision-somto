import rclpy
from rclpy.node import Node

from aisd_msgs.msg import Hand
from geometry_msgs.msg import Twist

COME_MARGIN = 0.03 #how far pinky has to be right of index to count as come
COME_FRAMES = 3 #3 frames in a row to start come (0.3sec)
TIMEOUT = 0.5 #Stop if no hand seen for this long(sec)

LINEAR_SPEED = 1.5 #use a constant for easy change/testing
TURN_SPEED = 0.5 #slower turning so come is the main movement
LEFT_EDGE = 0.35 #hand centre left of this = turn left
RIGHT_EDGE = 0.65 #hand centre right of this = turn right


class Move(Node):

    def __init__(self):
        super().__init__('move')
        # Subscribe to Hand messages that the Hands node publishes on cmd_hand
        self.subscription = self.create_subscription(
            Hand,
            'cmd_hand',
            self.listener_callback,
            1)
        self.subscription  # prevent unused variable warning
        self.vel_publisher = self.create_publisher(Twist, 'cmd_vel', 10)

        self.come_count = 0
        self.last_hand_time = self.get_clock().now()
        self.timed_out = True
        #check if hand went missing
        self.timer = self.create_timer(0.1, self.timer_callback)

    def send_twist(self, linear, angle):
        twist = Twist()
        twist.linear.x = linear
        twist.angular.z = angle
        if self.vel_publisher.get_subscription_count() > 0:
            self.vel_publisher.publish(twist)
        else:
            self.get_logger().info('waiting for subscriber')

    def listener_callback(self, msg):
        self.last_hand_time = self.get_clock().now()
        self.timed_out = False

        # pinky right of index (back of hand) = come, palm = stop
        if msg.xpinky - msg.xindex > COME_MARGIN:
            self.come_count += 1
        else:
            self.come_count = 0

        # stop everything, no moving and no turning
        if self.come_count < COME_FRAMES:
            self.get_logger().info('stay')
            self.send_twist(0.0, 0.0)
            return

        # use the middle of the hand to steer, not just the index
        hand_x = (msg.xindex + msg.xpinky) / 2

        # always go forward, only turn if hand is far to one side
        if hand_x > RIGHT_EDGE:
            self.get_logger().info('come right')
            angle = -TURN_SPEED
        elif hand_x < LEFT_EDGE:
            self.get_logger().info('come left')
            angle = TURN_SPEED
        else:
            self.get_logger().info('come')
            angle = 0.0

        # double speed if only the index finger is up
        if msg.fast:
            self.get_logger().info('fast')
        self.send_twist(LINEAR_SPEED * 2 if msg.fast else LINEAR_SPEED, angle)

    def timer_callback(self):
        # no hand for a while, so stop the turtle
        elapsed = (self.get_clock().now() - self.last_hand_time).nanoseconds / 1e9
        if elapsed > TIMEOUT and not self.timed_out:
            self.get_logger().info('no hand')
            self.come_count = 0
            self.send_twist(0.0, 0.0)
            self.timed_out = True


def main(args=None):
    rclpy.init(args=args)

    # Create the Move node
    move = Move()

    rclpy.spin(move)

    # Destroy the node explicitly and shut down ROS 2
    move.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
