from __future__ import print_function

import time
from absl import app
from absl import flags
from multiprocessing import Process

try:
    from std_msgs.msg import Int64
except ModuleNotFoundError:
    # ROS not installed
    Int64 = int

import erdos.graph
from erdos.graph import Graph

from sum_squares_test import IntegerOp, SquareOp, SumOp

FLAGS = flags.FLAGS


class SquaredIntGraph(Graph):
    def construct(self, input_ops, number):
        int_op = self.add(IntegerOp, name='int', init_args={'number': number})
        square_op = self.add(SquareOp, name='square')
        self.connect([int_op], [square_op])
        return [square_op]


class SumSquaresGraph(Graph):
    def construct(self, input_ops):
        square1_graph = self.add(
            SquaredIntGraph, name='square1', setup_args={'number': 1})
        square2_graph = self.add(
            SquaredIntGraph, name='square2', setup_args={'number': 2})
        sum_op = self.add(SumOp, name='sum')

        self.connect([square1_graph, square2_graph], [sum_op])

        return [sum_op]


def run_graph():
    """Sums the squares of 2 numbers. """

    # Set up graph
    graph = erdos.graph.get_current_graph()

    # Add operators
    sum_squares_graph = graph.add(SumSquaresGraph, name='sum_squares')
    square_op = graph.add(SquareOp, name='square')

    # Connect Operators
    graph.connect([sum_squares_graph], [square_op])

    # Execute graph
    graph.execute(FLAGS.framework)


def main(argv):
    proc = Process(target=run_graph)
    proc.start()
    time.sleep(10)
    proc.terminate()


if __name__ == "__main__":
    app.run(main)
