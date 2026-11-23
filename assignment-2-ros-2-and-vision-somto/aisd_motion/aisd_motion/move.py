import rclpy
from rclpy.node import Node

from aisd_msgs.msg import Hand
from geometry_msgs.msg import Twist


class Move(Node):

    def __init__(self):
        super().__init__('move')
        # Subscribe to Hand messages that the Hands node publishes on cmd_hand
        self.subscription = self.create_subscription(
            Hand,
            'cmd_hand',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning
        self.vel_publisher = self.create_publisher(Twist, 'cmd_vel', 10)

    def listener_callback(self, msg):
        # Default to no rotation and no forward motion
        angle = 0.0
        linear = 0.0

        # xindex is the index fingertip's x position, normalised 0.0 to 1.0 (right edge).
        if msg.xindex > 0.55:
            # Finger right of centre; negative angular z turns clockwise
            self.get_logger().info('right')
            angle = -0.1
        elif msg.xindex < 0.45:
            # Finger left of centre; positive angular z turns counter-clockwise
            self.get_logger().info('left')
            angle = 0.1
        else:
            # Finger in the centre band: no turning
            angle = 0.0

        # Compare index and pinky x positions to tell which way the hand is facing.
        if msg.xindex > msg.xpinky:
            self.get_logger().info('come')
            linear = 0.5  # drive forward at 0.5 m/s
        else:
            self.get_logger().info('stay')
            linear = 0.0  # stand still

        # linear.x is forward speed, angular.z is rotation about the vertical axis
        twist = Twist()
        twist.linear.x = linear
        twist.angular.z = angle

        if self.vel_publisher.get_subscription_count() > 0:
            self.vel_publisher.publish(twist)
        else:
            self.get_logger().info('waiting for subcriber')


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
