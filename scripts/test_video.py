import os
import cv2
import time

src = os.getenv('VIDEO_SOURCE', '0')
print(f'[TEST] Raw VIDEO_SOURCE env="{src}"')
if isinstance(src, str) and src.isdigit():
    src = int(src)

print(f'[TEST] Using source: {src}')
cap = cv2.VideoCapture(src)
# algunos backends necesitan tiempo
time.sleep(1.0)
if not cap.isOpened():
    print('[TEST] capture not opened')
    exit(2)

ret, frame = cap.read()
if not ret or frame is None:
    print('[TEST] initial read failed, trying multiple reads')
    for i in range(5):
        ret, frame = cap.read()
        print(f'[TEST] read attempt {i+1}: ret={ret}')
        if ret and frame is not None:
            break

if ret and frame is not None:
    h, w = frame.shape[:2]
    print(f'[TEST] frame read OK size={w}x{h}')
    # guardar thumbnail
    try:
        out_path = os.path.join('static', 'uploads', 'camera_test.jpg')
        cv2.imwrite(out_path, frame)
        print(f'[TEST] Thumbnail saved to {out_path}')
    except Exception as e:
        print(f'[TEST] Error saving thumbnail: {e}')
    cap.release()
    exit(0)
else:
    print('[TEST] failed to read frame after attempts')
    cap.release()
    exit(3)
