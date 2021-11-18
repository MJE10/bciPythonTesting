import argparse
import math
import time
import logging
import random

import pyautogui
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore

import brainflow
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds, BrainFlowError
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations, WindowFunctions, DetrendOperations


class Graph:
    def __init__(self, board_shim):
        self.board_id = board_shim.get_board_id()
        self.board_shim = board_shim
        self.exg_channels = BoardShim.get_exg_channels(self.board_id)
        self.sampling_rate = BoardShim.get_sampling_rate(self.board_id)
        self.update_speed_ms = 30
        self.window_size = 4
        self.num_points = self.window_size * self.sampling_rate

        self.time_last_change = time.time()
        self.delay_last_change = 0.25
        self.data_last_change = [0]*len(self.exg_channels)
        self.flexed = False
        self.consecutiveFalse = 0

        self.app = QtGui.QApplication([])
        self.win = pg.GraphicsWindow(title='BrainFlow Plot',size=(800, 600))

        self._init_timeseries()

        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(self.update_speed_ms)
        QtGui.QApplication.instance().exec_()


    def _init_timeseries(self):
        self.plots = list()
        self.curves = list()
        for i in range(len(self.exg_channels)):
            p = self.win.addPlot(row=i,col=0)
            p.showAxis('left', False)
            p.setMenuEnabled('left', False)
            p.showAxis('bottom', False)
            p.setMenuEnabled('bottom', False)
            if i == 0:
                p.setTitle('TimeSeries Plot')
            self.plots.append(p)
            curve = p.plot()
            self.curves.append(curve)

    def update(self):
        data = self.board_shim.get_current_board_data(self.num_points)
        avgs = []
        for count, channel in enumerate(self.exg_channels):
            # plot timeseries
            DataFilter.detrend(data[channel], DetrendOperations.CONSTANT.value)
            DataFilter.perform_bandpass(data[channel], self.sampling_rate, 51.0, 100.0, 2,
                                        FilterTypes.BUTTERWORTH.value, 0)
            DataFilter.perform_bandpass(data[channel], self.sampling_rate, 51.0, 100.0, 2,
                                        FilterTypes.BUTTERWORTH.value, 0)
            DataFilter.perform_bandstop(data[channel], self.sampling_rate, 50.0, 4.0, 2,
                                        FilterTypes.BUTTERWORTH.value, 0)
            DataFilter.perform_bandstop(data[channel], self.sampling_rate, 60.0, 4.0, 2,
                                        FilterTypes.BUTTERWORTH.value, 0)
            list_data = data[channel].tolist()
            avgs.append(sum([abs(x) for x in list_data])/len(list_data))
            if count == 0:
                percentIntoCycle = time.time() - self.time_last_change
                cycleLocation = percentIntoCycle / self.delay_last_change
                relevantValues = list_data[max(0, math.floor(cycleLocation * len(list_data) - (.5 * len(list_data)))):
                                         min(math.floor(cycleLocation * len(list_data) + (.5 * len(list_data))), len(list_data))]
                # relevantValues = list_data
                self.curves[count].setData(relevantValues)
                avgOfRelevantValues = sum([abs(x) for x in relevantValues]) / len(list_data)
                threshold = 300
                if avgOfRelevantValues > threshold and not self.flexed:
                    print('flex (delay currently ' + str(self.delay_last_change) + ' s)')
                    self.consecutiveFalse = 0
                    self.flexed = True
                    pyautogui.keyDown('d')
                    time.sleep(0.5)
                    pyautogui.keyUp('d')
                    pass
                elif avgOfRelevantValues < threshold and self.flexed:
                    self.consecutiveFalse += 1
                    if self.consecutiveFalse > 30:
                        print('unflex (delay currently ' + str(self.delay_last_change) + ' s)')
                        self.flexed = False
                elif self.flexed:
                    self.consecutiveFalse = 0
                print(avgOfRelevantValues)
        dataChanged = False
        for i in range(len([1])):
            if i >= len(self.data_last_change) or self.data_last_change[i] != avgs[i]:
                dataChanged = True
                break
        if dataChanged:
            self.delay_last_change = time.time() - self.time_last_change
            self.time_last_change = time.time()
            self.data_last_change = avgs

        # do things based on how far into the cycle we are

        self.app.processEvents()


def main():
    BoardShim.enable_dev_board_logger()
    logging.basicConfig(level=logging.DEBUG)

    board_id = 0

    params = BrainFlowInputParams()
    params.ip_port = 0
    params.serial_port = 'COM4'
    params.mac_address = ''
    params.other_info = ''
    params.serial_number = ''
    params.ip_address = ''
    params.ip_protocol = 0
    params.timeout = 0
    params.file = ''

    try:
        board_shim = BoardShim(board_id, params)
        board_shim.prepare_session()
        board_shim.start_stream(450000, '')
        g = Graph(board_shim)
    except BaseException as e:
        logging.warning('Exception', exc_info=True)
    finally:
        logging.info('End')
        if board_shim.is_prepared():
            logging.info('Releasing session')
            board_shim.release_session()


if __name__ == '__main__':
    main()