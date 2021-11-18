import logging
import turtle

from brainflow.board_shim import BoardShim, BrainFlowInputParams
from pyqtgraph.Qt import QtGui, QtCore


class InputAcceptor:
    def __init__(self, board_id, serial_port):

        # wn = turtle.Screen()
        # wn.bgcolor("black")
        # wn.title("BigBrainGraph")
        # self.turtle = turtle.Turtle()
        # self.turtle.pencolor('white')
        # self.turtle.speed(0)
        #
        # # self.turtle.reset()
        # self.turtle.forward(100)
        # self.turtle.left(90)
        # self.turtle.forward(100/50)
        # self.turtle.left(90)
        # self.turtle.forward(100)
        # self.turtle.right(90)
        # self.turtle.forward(200/50)
        # self.turtle.right(90)
        # self.turtle.forward(100)
        # self.turtle.left(90)
        # self.turtle.forward(300/50)
        # self.turtle.left(90)
        # self.turtle.forward(100)

        BoardShim.enable_dev_board_logger()
        logging.basicConfig(level=logging.DEBUG)

        params = BrainFlowInputParams()
        params.ip_port = 0
        params.serial_port = serial_port
        params.mac_address = ''
        params.other_info = ''
        params.serial_number = ''
        params.ip_address = ''
        params.ip_protocol = 0
        params.timeout = 0
        params.file = ''

        try:
            self.board_shim = BoardShim(board_id, params)
            self.board_shim.prepare_session()
            self.board_shim.start_stream(450000, '')
        except BaseException as e:
            logging.warning('Exception', exc_info=True)

        self.board_id = self.board_shim.get_board_id()
        self.board_shim = self.board_shim
        self.exg_channels = BoardShim.get_exg_channels(self.board_id)
        self.sampling_rate = BoardShim.get_sampling_rate(self.board_id)
        self.update_speed_ms = 50
        self.window_size = 4
        self.num_points = self.window_size * self.sampling_rate

        self.last_num = 0

        self.lowerThreshold = 1
        self.upperThreshold = 1
        self.acceptableLimitUV = 20_000
        self.minRange = 15
        self.creepSpeed = 0.99

        self.app = QtGui.QApplication([])

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(self.update_speed_ms)
        QtGui.QApplication.instance().exec_()

    def update(self):
        data = self.board_shim.get_current_board_data(self.num_points)
        # data = [[x for x in i] for i in data]
        averages = [sum([abs(x) for x in data[i]])/len(data[i]) for i in self.exg_channels]

        for averageIndex in [0]:
            average = averages[averageIndex]

            if average != self.last_num:
                print(average)
                self.last_num = average

            if self.upperThreshold <= average <= self.acceptableLimitUV:
                self.upperThreshold = average

            if average <= self.lowerThreshold:
                self.lowerThreshold = average

            if self.upperThreshold >= average + self.minRange:
                self.upperThreshold *= self.creepSpeed

            if self.lowerThreshold < 1:
                self.lowerThreshold = 1

            if self.lowerThreshold <= average:
                self.lowerThreshold *= 1/self.creepSpeed

            if self.upperThreshold <= self.lowerThreshold + self.minRange:
                self.upperThreshold = self.lowerThreshold + self.minRange

            activated = self.lowerThreshold < average < self.upperThreshold


            # print('---\n' + 'L: ' + str(self.lowerThreshold) + '\nA: ' + str(average) + '\nU: ' + str(self.upperThreshold) + "\n" + str(activated))


            # self.turtle.reset()
            #
            # self.turtle.pencolor('white')
            # self.turtle.speed(0)
            #
            # self.turtle.forward(100)
            # self.turtle.left(90)
            # self.turtle.forward(self.lowerThreshold / 50)
            # self.turtle.left(90)
            # self.turtle.forward(100)
            # self.turtle.right(90)
            # self.turtle.forward((average - self.lowerThreshold) / 50)
            # self.turtle.right(90)
            # self.turtle.forward(100)
            # self.turtle.left(90)
            # self.turtle.forward((self.upperThreshold - average) / 50)
            # self.turtle.left(90)
            # self.turtle.forward(100)

            # cfc.output_normalized = map(cfc.myAverage, cfc.lowerThreshold, cfc.upperThreshold, 0, 1);
            # if (cfc.output_normalized < 0){
            # cfc.output_normalized = 0; // always make sure this value is >= 0
            # }
            # cfc.output_adjusted = ((-0.1 / (cfc.output_normalized * 255.0)) + 255.0);



    def close(self):
        logging.info('End')
        if self.board_shim.is_prepared():
            logging.info('Releasing session')
            self.board_shim.release_session()


if __name__ == '__main__':
    i = InputAcceptor(0, "COM4")