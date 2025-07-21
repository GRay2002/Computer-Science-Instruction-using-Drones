import cv2
import numpy as np
import torch
from djitellopy import Tello
from threading import Thread
import time

def preprocess_frame(frame):
    """Convert frame to grayscale and normalize."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.equalizeHist(gray)

def detect_objects(tello, model_manager):
    global stop_thread
    while not stop_thread:
        frame = tello.get_frame_read().frame
        if frame is None or np.array(frame).size == 0:
            continue

        resized_frame = cv2.resize(frame, (640, 480))
        processed_frame = preprocess_frame(resized_frame)
        results = model_manager['model'](processed_frame)
        predictions = results.pandas().xyxy[0]

        original_height, original_width = frame.shape[:2]
        scale_x = original_width / 640
        scale_y = original_height / 480

        for _, row in predictions.iterrows():
            x1 = int(row['xmin'] * scale_x)
            y1 = int(row['ymin'] * scale_y)
            x2 = int(row['xmax'] * scale_x)
            y2 = int(row['ymax'] * scale_y)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"{row['name']} {row['confidence']:.2f}"
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        cv2.putText(frame, f"Current Model: {model_manager['label']}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        cv2.imshow('Tello Detection', frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('0'):
            break
        handle_key_press(key, tello, model_manager)

    cv2.destroyAllWindows()
    tello.end()

def handle_key_press(key, tello, model_manager):
    # Movement controls
    if key == ord('l'):
        tello.land()
    elif key == ord('t'):
        tello.takeoff()
    elif key == ord('w'):
        tello.move_forward(30)
    elif key == ord('s'):
        tello.move_back(30)
    elif key == ord('a'):
        tello.move_left(30)
    elif key == ord('d'):
        tello.move_right(30)
    elif key == ord('y'):
        tello.move_up(30)
    elif key == ord('h'):
        tello.move_down(30)
    elif key == ord('q'):
        tello.rotate_counter_clockwise(30)
    elif key == ord('e'):
        tello.rotate_clockwise(30)

    # Model switching
    elif key == ord('1'):
        model = torch.hub.load('ultralytics/yolov5', 'yolov5s')
        model_manager['model'] = model
        model_manager['label'] = "Default"
    elif key == ord('2'):
        model = torch.hub.load('yolov5', 'custom', path='colegi_best.pt', source='local')
        model_manager['model'] = model
        model_manager['label'] = "Custom-Epic-Teammates"
    elif key == ord('3'):
        model = torch.hub.load('yolov5', 'custom', path='profesori_best.pt', source='local')
        model_manager['model'] = model
        model_manager['label'] = "Cool-FILS-Professors"

def main():
    tello = Tello()
    tello.connect()
    tello.streamon()
    print(tello.get_battery())

    model = torch.hub.load('ultralytics/yolov5', 'yolov5s')
    model_manager = {'model': model, 'label': "Default"}

    global stop_thread
    stop_thread = False
    thread = Thread(target=detect_objects, args=(tello, model_manager))
    thread.start()
    try:
        while thread.is_alive():
            time.sleep(1)  # Keep the main thread running while the detection thread is active
    except KeyboardInterrupt:
        stop_thread = True
        thread.join()

if __name__ == "__main__":
    main()
