import torch
from djitellopy import Tello
import cv2
import pygame
from pygame.locals import *


def load_yolo_model():
    model = torch.hub.load('ultralytics/yolov5', 'yolov5s')  # Smallest YOLOv5 model
    return model


class FrontEnd:
    def __init__(self):
        pygame.init()
        self.tello = Tello()
        self.model = load_yolo_model()
        self.hud_size = (960, 720)  # Set size to your preference
        self.screen = pygame.display.set_mode(self.hud_size)
        pygame.display.set_caption("Drone with YOLO Object Tracking")
        self.tracking_enabled = False  # Tracking state

    def run(self):
        self.tello.connect()
        self.tello.streamon()
        print(self.tello.get_battery())
        frame_read = self.tello.get_frame_read()

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        running = False
                    elif event.key == K_TAB:
                        self.tello.takeoff()
                    elif event.key == K_LSHIFT:
                        self.tello.land()
                    elif event.key == K_t:
                        self.tracking_enabled = not self.tracking_enabled  # Toggle tracking

            frame = frame_read.frame
            frame = cv2.resize(frame, self.hud_size)
            results = self.detect_objects(frame)
            if self.tracking_enabled:
                self.control_drone(results)

            # Convert frame to Pygame surface to display it
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = frame.swapaxes(0, 1)
            frame = pygame.surfarray.make_surface(frame)
            self.screen.blit(frame, (0, 0))
            pygame.display.update()

            if cv2.waitKey(1) & 0xFF == ord('q'):
                running = False

        self.tello.end()
        cv2.destroyAllWindows()
        pygame.quit()

    def detect_objects(self, frame):
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.model([img])
        results = results.xyxy[0].to('cpu').numpy()  # Extract predictions
        for det in results:
            if int(det[5]) == 0:  # Class ID for 'person'
                x1, y1, x2, y2, conf, cls = map(int, det[:6])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, 'Person', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        return results

    def calculate_dynamic_distance(self, size_error, desired_area):
        # Ensure there's no division by zero
        if desired_area == 0:
            raise ValueError("Desired area is zero, cannot calculate dynamic distance.")

        # Scale the movement to be proportional to the size error
        proportion_of_error = abs(size_error) / desired_area
        # Ensure the movement is within the 20-500 cm range
        move_distance = int(max(20, min(100, proportion_of_error * 250)))  # Adjust scale factor as needed
        return move_distance

    def control_drone(self, detections):
        if len(detections) == 0:
            return  # If no objects detected, no movement needed

        # Assuming we track the first detected object for simplicity
        det = detections[0]
        x1, y1, x2, y2, conf, cls = det
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2

        # Calculate bounding box size
        object_width = x2 - x1
        object_height = y2 - y1
        object_area = object_width * object_height

        # Desired object area (set this based on your baseline measurement at 30 cm)
        desired_area = 0.40 * self.hud_size[0] * self.hud_size[1]  # Adjust this value based on your tests

        # Calculate error in size
        size_error = object_area - desired_area

        # Frame center
        midx, midy = self.hud_size[0] / 2, self.hud_size[1] / 2

        # Calculate error offsets
        error_x = center_x - midx
        error_y = center_y - midy

        # Define thresholds to avoid too frequent minor adjustments
        threshold_x = self.hud_size[0] * 0.05  # 5% of the frame width
        threshold_y = self.hud_size[1] * 0.05  # 5% of the frame height
        threshold_area = 0.05 * desired_area  # 5% of the desired area

        # Movement based on x and y offsets
        self.adjust_horizontal_vertical_movement(error_x, error_y, threshold_x, threshold_y)

        # Adjust forward/backward based on size error dynamically
        if abs(size_error) > threshold_area:
            move_distance = self.calculate_dynamic_distance(size_error, desired_area)
            # Check if move_distance is not None and is a valid integer
            if move_distance is not None and isinstance(move_distance, int):
                if size_error > 0:
                    self.tello.move_back(move_distance)  # Object too large, move back
                else:
                    self.tello.move_forward(move_distance)  # Object too small, move closer

    def adjust_horizontal_vertical_movement(self, error_x, error_y, threshold_x, threshold_y):
        if abs(error_x) > threshold_x:
            if error_x < 0:
                self.tello.move_left(25)  # Adjust left/right based on standard increment
            else:
                self.tello.move_right(25)
        if abs(error_y) > threshold_y:
            if error_y < 0:
                self.tello.move_up(20)  # Adjust up/down based on standard increment
            else:
                self.tello.move_down(20)




if __name__ == '__main__':
    frontend = FrontEnd()
    frontend.run()