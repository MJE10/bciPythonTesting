import matplotlib.pyplot

ys = []
with open("C:/Users/micha/Documents/OpenBCI_GUI/Recordings/OpenBCISession_2021-11-13_11-12-18/OpenBCI-RAW-2021-11-13_11-12-36.txt", "r") as f:
    for line in f:
        try:
            ys.append(float(line.split(", ")[1]))
        except Exception:
            print('bad ' + line)
matplotlib.pyplot.plot(range(len(ys)), ys)
matplotlib.pyplot.show()

# import argparse
# import logging
# import time
#
# import matplotlib.pyplot
# import pyautogui
# from brainflow.board_shim import BoardShim, BrainFlowInputParams
# from brainflow.data_filter import DataFilter, FilterTypes, DetrendOperations
# from pyqtgraph.Qt import QtGui, QtCore
#
#
# class InputAcceptor:
#     def __init__(self, board_id, serial_port, f1, f2):
#
#         BoardShim.enable_dev_board_logger()
#         logging.basicConfig(level=logging.DEBUG)
#
#         params = BrainFlowInputParams()
#         params.ip_port = 0
#         params.serial_port = serial_port
#         params.mac_address = ''
#         params.other_info = ''
#         params.serial_number = ''
#         params.ip_address = ''
#         params.ip_protocol = 0
#         params.timeout = 0
#         params.file = ''
#
#         try:
#             self.board_shim = BoardShim(board_id, params)
#             self.board_shim.prepare_session()
#             self.board_shim.start_stream(450000, '')
#         except BaseException as e:
#             logging.warning('Exception', exc_info=True)
#
#         self.board_id = self.board_shim.get_board_id()
#         self.board_shim = self.board_shim
#         self.exg_channels = BoardShim.get_exg_channels(self.board_id)
#         self.sampling_rate = BoardShim.get_sampling_rate(self.board_id)
#         self.update_speed_ms = 50
#         self.window_size = 4
#         self.num_points = self.window_size * self.sampling_rate
#
#         self.lastnum = 0
#         self.starttime = time.time()
#
#         self.xs = []
#         self.ys = []
#
#         self.flexed = [False]*len(self.exg_channels)
#         self.stage = "RELAX"
#
#         self.app = QtGui.QApplication([])
#
#         self.timer = QtCore.QTimer()
#         self.timer.timeout.connect(self.update)
#         self.timer.start(self.update_speed_ms)
#         QtGui.QApplication.instance().exec_()
#
#
#
#     def update(self):
#         data = self.board_shim.get_current_board_data(self.num_points)
#         for count, channel in enumerate(self.exg_channels):
#             if len(data[channel]) > 0:
#                 # plot timeseries
#                 DataFilter.detrend(data[channel], DetrendOperations.CONSTANT.value)
#                 DataFilter.perform_bandpass(data[channel], self.sampling_rate, 51.0, 100.0, 2,
#                                             FilterTypes.BUTTERWORTH.value, 0)
#                 DataFilter.perform_bandpass(data[channel], self.sampling_rate, 51.0, 100.0, 2,
#                                             FilterTypes.BUTTERWORTH.value, 0)
#                 DataFilter.perform_bandstop(data[channel], self.sampling_rate, 50.0, 4.0, 2,
#                                             FilterTypes.BUTTERWORTH.value, 0)
#                 DataFilter.perform_bandstop(data[channel], self.sampling_rate, 60.0, 4.0, 2,
#                                             FilterTypes.BUTTERWORTH.value, 0)
#         [self.ys.append(x) for x in data[0]]
#         if (time.time() - self.starttime) > 10:
#             self.close()
#             matplotlib.pyplot.plot(range(len(self.ys)), self.ys)
#         # shortData = [data[i].tolist()[:-10:-1] for i in self.exg_channels]
#         # # print(len(self.exg_channels))
#         # num = [sum([abs(x) for x in l])/len([abs(x) for x in l]) for l in shortData]
#         # with open("data.csv", "a") as f:
#         #     f.write(",".join([str(x) for x in ([self.stage, time.time() - self.starttime]+num)]))
#         #     f.write('\n')
#         # if num[0] != self.lastnum:
#         #     print(num[0])
#         #     self.lastnum = num[0]
#         #     for x in range(len(num)):
#         #         pass
#
#     def close(self):
#         logging.info('End')
#         if self.board_shim.is_prepared():
#             logging.info('Releasing session')
#             self.board_shim.release_session()
#
#
# if __name__ == '__main__':
#     InputAcceptor(0, "COM4", lambda: pyautogui.write('a'), lambda: pyautogui.write('b'))