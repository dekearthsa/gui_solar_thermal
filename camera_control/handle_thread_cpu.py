import cv2
import threading

class CameraThread:

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cap = None
        self.running = True
        self.lock = threading.Lock()
        threading.Thread(target=self.update, daemon=True).start()

    def update(self, src):
        # print("on update frame")
        while self.running:
            self.cap = cv2.VideoCapture("rtsp://admin:Nu12131213@192.168.1.170:554/Streaming/Channels/101/", cv2.CAP_FFMPEG)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE,1)
            ret, frame = self.cap.read()
            with self.lock:
                self.ret, self.frame = ret, frame

    def read(self):
        with self.lock:
            return self.ret, self.frame

    def stop(self):
        self.running = False
        self.cap.release()
