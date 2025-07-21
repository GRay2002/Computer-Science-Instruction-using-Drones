import torch
import cv2
import pygame
from pygame.locals import *
from djitellopy import Tello
from threading import Thread
import time


def calculate_dynamic_distance(size_error, desired_area):
    proportion_of_error = abs(size_error) / desired_area
    move_distance = int(max(20, min(200, proportion_of_error * 250)))
    return move_distance


def load_yolo_model():
    model = torch.hub.load('ultralytics/yolov5', 'yolov5s')
    return model


class FrontEnd:
    def __init__(self):
        pygame.init()
        self.tello = Tello()
        self.model = load_yolo_model()
        self.hud_size = (960, 720)
        self.screen = pygame.display.set_mode(self.hud_size)
        pygame.display.set_caption("Drone with YOLO Object Tracking")
        self.tracking_enabled = False
        self.run_thread = True
        self.detections = []  # Store detection results

    def run(self):
        self.tello.connect()
        self.tello.streamon()
        print(self.tello.get_battery())
        frame_read = self.tello.get_frame_read()

        control_thread = Thread(target=self.control_loop)
        control_thread.start()

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        running = False
                        self.run_thread = False
                    elif event.key == K_TAB:
                        Thread(target=self.tello.takeoff).start()
                    elif event.key == K_LSHIFT:
                        Thread(target=self.tello.land).start()
                    elif event.key == K_t:
                        self.tracking_enabled = not self.tracking_enabled

            if frame_read.frame is not None:
                frame = frame_read.frame
                frame = cv2.resize(frame, self.hud_size)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Draw detections from the latest frame
                for det in self.detections:
                    x1, y1, x2, y2, conf, cls = map(int, det[:6])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, 'Person', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

                frame = frame.swapaxes(0, 1)
                frame = pygame.surfarray.make_surface(frame)
                self.screen.blit(frame, (0, 0))
                pygame.display.update()
            else:
                print("No frame received from drone camera")

            if cv2.waitKey(1) & 0xFF == ord('q'):
                running = False

        self.tello.end()
        cv2.destroyAllWindows()
        pygame.quit()

    def control_loop(self):
        while self.run_thread:
            if self.tracking_enabled:
                frame_read = self.tello.get_frame_read()
                frame = frame_read.frame
                frame = cv2.resize(frame, self.hud_size)
                results = self.detect_objects(frame)
                self.detections = results  # Update global detection results
                self.control_drone(results)
            time.sleep(0.1)  # Reduce CPU load

    def detect_objects(self, frame):
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.model([img])
        results = results.xyxy[0].to('cpu').numpy()
        return results

    def control_drone(self, detections):
        if len(detections) == 0:
            return
        det = detections[0]
        x1, y1, x2, y2, conf, cls = det
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        object_width = x2 - x1
        object_height = y2 - y1
        object_area = object_width * object_height
        desired_area = 0.40 * self.hud_size[0] * self.hud_size[1]
        size_error = object_area - desired_area

        midx, midy = self.hud_size[0] / 2, self.hud_size[1] / 2
        error_x = center_x - midx
        error_y = center_y - midy

        threshold_x = self.hud_size[0] * 0.05
        threshold_y = self.hud_size[1] * 0.05
        threshold_area = 0.1 * desired_area

        self.adjust_horizontal_vertical_movement(error_x, error_y, threshold_x, threshold_y)

        if abs(size_error) > threshold_area:
            move_distance = calculate_dynamic_distance(size_error, desired_area)
            if size_error > 0:
                Thread(target=self.tello.move_back, args=(move_distance,)).start()
            else:
                Thread(target=self.tello.move_forward, args=(move_distance,)).start()

    def adjust_horizontal_vertical_movement(self, error_x, error_y, threshold_x, threshold_y):
        if abs(error_x) > threshold_x:
            if error_x < 0:
                Thread(target=self.tello.move_left, args=(25,)).start()
            else:
                Thread(target=self.tello.move_right, args=(25,)).start()
        if abs(error_y) > threshold_y:
            if error_y < 0:
                Thread(target=self.tello.move_up, args=(20,)).start()
            else:
                Thread(target=self.tello.move_down, args=(20,)).start()


if __name__ == '__main__':
    frontend = FrontEnd()
    frontend.run()


