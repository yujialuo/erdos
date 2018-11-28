import logging
import sys
from time import sleep


class Op(object):
    """Operator base class.

    All operators must inherit from this class, and must implement:

    1. setup_streams: Constructs the object's output data streams from the
    input data streams and arguments.

    Operators may optionally implement:

    2. __init__: Sets up operator state.
    3. execute: Invoked upon operator execution.

    Attributes:
        name (str): A unique string naming the operator.
        input_streams (list of DataStream): data streams to which the operator
            is subscribed.
        output_streams (dict of str -> DataStream): Data streams on which the
            operator publishes. Mapping between name and data stream.
        freq_actor: A Ray actor used for periodic tasks.
    """

    def __init__(self, name,
                 log_input_streams=False,
                 log_output_streams=False):
        self.name = name
        self.input_streams = []
        self.output_streams = {}
        self.freq_actor = None
        self.progress_tracker = None
        self.framework = None

        # Setup loggers.
        self.log_input = log_input_streams
        self.log_output = log_output_streams
        self.loggers = {}

    def get_output_stream(self, name):
        """Returns the output stream matching name"""
        return self.output_streams[name]

    def notify_at(self, timestamp):
        """Subscribes the operator to receive a notification."""
        self.progress_tracker.notify_at.remote(self.name, timestamp)

    def on_notify(self, timestamp):
        """Called after a timestamp completes"""
        pass

    def execute(self):
        """Invoked upon operator execution.

        User override. Otherwise, spin.
        """
        self.spin()

    @staticmethod
    def setup_streams(input_streams, **kwargs):
        """Subscribes to input data streams and constructs output data streams.

        Required user override.

        Args:
            input_streams (DataStreams): data streams from connected upstream
                operators which the operator may subscribe to.
            kwargs: Arbitrary keyword arguments used to subscribe to input
                data streams or construct output data streams.

        Returns:
            (list of DataStream): output data streams on which the operator
            publishes.
        """
        raise NotImplementedError(
            "User must define setup_streams in operators.")

    def spin(self):
        """Abstracts framework specific spin methods."""
        if self.framework == "ros":
            import rospy
            rospy.spin()
        elif self.framework == "local":
            while True:
                sleep(0.5)
        elif self.framework == "ray":
            pass
        else:
            logging.critical("Unexpected framework %s", self.framework)

    def log_event(self, processing_time, timestamp, log_message=None):
        pass

    def log_streams(self, stream_uid, msg):
        if stream_uid not in self.loggers:
            logger = logging.getLogger(self.name)
            logger.setLevel(logging.INFO)
            file_handler = logging.FileHandler(stream_uid + ".log", "a")
            logger.addHandler(file_handler)
            logger.propagate = False
            self.loggers[stream_uid] = logger
        self.loggers[stream_uid].info(msg)

    def _add_input_streams(self, input_streams):
        """Setups and updates all input streams."""
        self.input_streams = self.input_streams + input_streams

    def _add_output_streams(self, output_streams):
        """Updates the dictionary of output data streams."""
        for output_stream in output_streams:
            self.output_streams[output_stream.name] = output_stream

    def _internal_setup_streams(self):
        """Setups input and output streams."""
        # Set up output streams before input streams.
        # This prevents errors where the operator recieves a message, executes
        # the callback, and sends a message before output streams are set up.
        for output_stream in self.output_streams.values():
            output_stream.setup()
        for input_stream in self.input_streams:
            input_stream.setup()
