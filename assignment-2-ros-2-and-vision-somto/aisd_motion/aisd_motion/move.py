import rclpy
from rclpy.node import Node

from aisd_msgs.msg import Hand
from geometry_msgs.msg import Twist

COME_MARGIN = 0.3 #how far index from pinky to count as a come
COME_FRAMES = 3 #3 constant frames to initiate come (0.3sec)
TIMEOUT = 0.5 #Stop if no hand seen for this long(sec)

LINEAR_SPEED = 2.0 #use a constanct for easy change/testing
TURN_SPEED = 1.0


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
        self.timer = self.create_timer(0.1,self.timer_callback)
    
    def send_twist(self, linear, angle):
        twist = Twist()
        twist.linear.x = linear
        twist.angular.z = angle
        if self.vel_publisher.get_subscription_count()>0:
            self.vel_publisher.publish(twist)
        else:
            self.get_logger().info('waiting for subscriber')

    def listener_callback(self, msg):
        self.last_hand_time = self.get_clock().now()
        self.timed_out = False

        # index right of pinky = come, otherwise (palm) = stop
        if msg.xpinky - msg.xindex > COME_MARGIN:
            self.come_count += 1
        else:
            self.come_count = 0

        # stop everything, no moving and no turning
        if self.come_count < COME_FRAMES:
            self.get_logger().info('stay')
            self.send_twist(0.0, 0.0)
            return

        # turn towards where the index finger is
        if msg.xindex > 0.55:
            self.get_logger().info('right')
            angle = -TURN_SPEED
        elif msg.xindex < 0.45:
            self.get_logger().info('left')
            angle = TURN_SPEED
        else:
            self.get_logger().info('come')
            angle = 0.0

        self.send_twist(LINEAR_SPEED, angle)

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
