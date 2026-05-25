# pokeydevice.py
import time

class PoKeysDevice:
    def __init__(self, dev_id, ip, start_id, end_id):
        self.id = dev_id
        self.ip = ip
        self.start_id = start_id
        self.end_id = end_id
        self.online = False
        # self.pin_order = [
        #     0, 1, 4, 5, 8, 10, 14, 15, 18, 19,
        #     20, 21, 22, 23, 24, 25, 26, 27,
        #     40, 41, 42, 43, 45, 47, 48
        # ]
        self.last_online_ts = 0
        self.sensors = []

    def mark_online(self):
        self.online = True
        self.last_online_ts = time.time()

    def mark_offline(self):
        self.online = False
