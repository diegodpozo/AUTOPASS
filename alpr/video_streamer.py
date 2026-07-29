import cv2
import time
import threading

class VideoStreamer:
    """Captura video en un hilo separado y provee acceso thread-safe al último frame."""

    def __init__(self, source, target_width=640):
        self.cap = cv2.VideoCapture(source)
        if isinstance(source, str) and source.startswith("http"):
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.target_width = target_width
        self.current_frame = None
        self.is_running = True
        self.lock = threading.Lock()

    def start(self):
        threading.Thread(target=self._update, daemon=True).start()
        return self

    def _update(self):
        while self.is_running:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    time.sleep(1)
                    continue
                h, w = frame.shape[:2]
                if w > self.target_width:
                    scale = self.target_width / w
                    new_w = self.target_width
                    new_h = int(h * scale)
                    frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
                with self.lock:
                    self.current_frame = frame
            except Exception:
                time.sleep(1)

    def get_frame(self):
        with self.lock:
            return self.current_frame.copy() if self.current_frame is not None else None

    def stop(self):
        self.is_running = False
        if self.cap and self.cap.isOpened():
            self.cap.release()
