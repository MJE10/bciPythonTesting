import logging
import time

import pyautogui
from brainflow import DataFilter, DetrendOperations, FilterTypes
from brainflow.board_shim import BoardShim, BrainFlowInputParams
from pyqtgraph.Qt import QtGui, QtCore

user_board_id = 0
user_serial_port = "COM7"
user_controls = ['w', 'a', 's', 'd', ' ', 'shift', 'escape', 'ctrl']


class OpenBCIKeyboard:
    def __init__(self, board_id, serial_port, inputs):

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
        except BaseException:
            logging.warning('Exception', exc_info=True)

        self.board_id = self.board_shim.get_board_id()
        self.board_shim = self.board_shim
        self.exg_channels = BoardShim.get_exg_channels(self.board_id)
        self.sampling_rate = BoardShim.get_sampling_rate(self.board_id)
        self.update_speed_ms = 50
        self.window_size = 4
        self.num_points = self.window_size * self.sampling_rate
        self.small_sample_size = 20

        self.flexed = [False]*len(self.exg_channels)
        self.inputs = inputs
        self.thresholds = [0]*len(self.exg_channels)

        self.app = QtGui.QApplication([])

        self.calibrate_update_sample_rate()
        self.calibrate_sensitivity()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(self.update_speed_ms)
        QtGui.QApplication.instance().exec_()

    def calibrate_update_sample_rate(self):
        beforeData = self.board_shim.get_current_board_data(self.small_sample_size)
        beforeTime = time.time()
        while 1:
            afterData = self.board_shim.get_current_board_data(self.small_sample_size)
            if sum([beforeData[0][i] == afterData[0][i] for i in range(len(beforeData[0]))]) == 0:
                break
        afterTime = time.time()
        print("Approximate refresh time: " + str(afterTime - beforeTime) + " s.")

    def calibrate_sensitivity(self):
        relaxedReadings = [[]]*len(self.exg_channels)
        flexedReadings = [[]]*len(self.exg_channels)

        print("Please relax your muscles.")

        beforeTime = time.time()
        while time.time() - beforeTime < 3:
            pass
        beforeTime = time.time()
        while time.time() - beforeTime < 3:
            time.sleep(0.5)
            readings = self.get_readings()
            for channel in range(len(self.exg_channels)):
                relaxedReadings[channel].append(readings[channel])

        print("Please flex your muscles.")

        beforeTime = time.time()
        while time.time() - beforeTime < 3:
            pass
        beforeTime = time.time()
        while time.time() - beforeTime < 3:
            time.sleep(0.5)
            readings = self.get_readings()
            for channel in range(len(self.exg_channels)):
                flexedReadings[channel].append(readings[channel])

        print("You may relax")

        # lowestFlex = [min(x) for x in flexedReadings]
        # highestRelaxed = [min(x) for x in relaxedReadings]

        for channel in range(len(self.exg_channels)):
            low = 0
            high = max(max(relaxedReadings[channel]), max(flexedReadings[channel]))
            print("high: "+str(high))

            # if highestRelaxed[channel] < lowestFlex[channel]:
            #     low = highestRelaxed[channel]
            #     high = lowestFlex[channel]

            threshold = (low + high) / 2

            # if low == 0:
            #     break

            while 1:
                failsRelaxed = sum([reading > threshold for reading in relaxedReadings[channel]])
                failsFlexed = sum([reading < threshold for reading in flexedReadings[channel]])
                print(relaxedReadings[channel])
                print(flexedReadings[channel])
                if abs(high - low) < 0.000000001:
                    break
                if failsFlexed > failsRelaxed:
                    high = threshold
                else:
                    low = threshold
                print('fails relaxed: '+str(failsRelaxed))
                print('fails flexed: '+str(failsFlexed))
                print(threshold)
                time.sleep(0.3)
                threshold = (low + high) / 2

            self.thresholds[channel] = threshold

            tests = len(flexedReadings[channel]) + len(relaxedReadings[channel])
            failsRelaxed = sum([reading > threshold for reading in relaxedReadings[channel]])
            failsFlexed = sum([reading < threshold for reading in flexedReadings[channel]])

            print('fails relaxed: '+str(failsRelaxed))
            print('fails flexed: '+str(failsFlexed))
            print('tests: '+str(tests))
            print('threshold: '+str(threshold))
            print("Accuracy for channel #" + str(channel) + " is " + str((failsRelaxed + failsFlexed) / tests * 100) + " percent")

    def update(self):
        flexedNow = self.get_readings()
        print('--')
        print(flexedNow[0])
        print(flexedNow[1])
        for channel in range(len(flexedNow)):
            if flexedNow[channel] > self.thresholds[channel]:
                if not self.flexed[channel] and channel < len(self.inputs):
                    print("FLEX " + str(channel))
                    if channel == 0:
                        pyautogui.keyDown(self.inputs[channel])
            else:
                if self.flexed[channel] and channel < len(self.inputs):
                    print("NOT FLEXED " + str(channel))
                    if channel == 0:
                        pyautogui.keyUp(self.inputs[channel])
            self.flexed[channel] = flexedNow[channel] > self.thresholds[channel]

    def average(self, list):
        return sum(list) / len(list)

    def get_readings(self):
        data = self.board_shim.get_current_board_data(self.num_points)
        for count, channel in enumerate(self.exg_channels):
            # plot timeseries - what does this DO?
            DataFilter.detrend(data[channel], DetrendOperations.CONSTANT.value)
            DataFilter.perform_bandpass(data[channel], self.sampling_rate, 51.0, 100.0, 2,
                                        FilterTypes.BUTTERWORTH.value, 0)
            DataFilter.perform_bandpass(data[channel], self.sampling_rate, 51.0, 100.0, 2,
                                        FilterTypes.BUTTERWORTH.value, 0)
            DataFilter.perform_bandstop(data[channel], self.sampling_rate, 50.0, 4.0, 2,
                                        FilterTypes.BUTTERWORTH.value, 0)
            DataFilter.perform_bandstop(data[channel], self.sampling_rate, 60.0, 4.0, 2,
                                        FilterTypes.BUTTERWORTH.value, 0)
        flexedNow = [x for x in self.flexed]
        for channel in range(len(self.exg_channels)):
            flexedNow[channel] = sum([abs(x) for x in data[self.exg_channels[channel]]])
        return flexedNow

    def close(self):
        logging.info('End')
        if self.board_shim.is_prepared():
            logging.info('Releasing session')
            self.board_shim.release_session()


if __name__ == '__main__':
    OpenBCIKeyboard(user_board_id, user_serial_port, user_controls)
