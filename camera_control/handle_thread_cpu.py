import cv2, threading, time

class CameraThread(threading.Thread):
    def __init__(self, src=0):
        super().__init__(daemon=True)
        self.src = src
        self.running = True
        self.lock = threading.Lock()
        self.ret, self.frame = False, None
        self.start()             # run() จะทำงานอัตโนมัติ

    def run(self):
        self.cap = cv2.VideoCapture(self.src, cv2.CAP_AVFOUNDATION)
        if not self.cap.isOpened():
            raise RuntimeError("Cannot open camera (macOS)")
        
        # รอเฟรมแรก
        for _ in range(30):
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.ret, self.frame = ret, frame
                break
            time.sleep(0.03)

        while self.running:
            ret, frame = self.cap.read()
            with self.lock:
                self.ret, self.frame = ret, frame
        self.cap.release()

    def read(self):
        with self.lock:
            return self.ret, self.frame

    def stop(self):
        self.running = False
