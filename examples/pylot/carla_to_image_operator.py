from cv_bridge import CvBridge

from erdos.data_stream import DataStream
from erdos.message import Message
from erdos.op import Op
from erdos.utils import setup_logging

from carla.image_converter import to_bgra_array
from sensor_msgs.msg import Image


class CarlaToImageOperator(Op):
    def __init__(self, name, log_file_name=None):
        super(CarlaToImageOperator, self).__init__(name)
        self._logger = setup_logging(self.name, log_file_name)
        self._bridge = CvBridge()

    @staticmethod
    def setup_streams(input_streams, op_name, filter_name=None):
        if filter_name:
            input_streams = input_streams.filter_name(filter_name)
        input_streams.add_callback(CarlaToImageOperator.on_msg)
        return [DataStream(data_type=Image,
                           name='{}_output'.format(op_name),
                           labels={'camera': 'true',
                                   'ros': 'true'})]

    def on_msg(self, msg):
        bgra_image = to_bgra_array(msg.data)
        image = self._bridge.cv2_to_imgmsg(bgra_image, "bgra8")
        output_msg = Message(image, msg.timestamp)
        self.get_output_stream('{}_output'.format(self.name)).send(output_msg)

    def execute(self):
        self.spin()
