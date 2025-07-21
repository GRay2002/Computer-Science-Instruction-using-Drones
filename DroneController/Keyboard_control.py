import pygame
import cv2
import time
from easytello import tello

# Initialize Pygame
pygame.init()
pygame.display.set_mode((400, 300))

# Initialize Tello SDK
drone = tello.Tello()
print("Battery:", drone.get_battery())

# Start video stream
drone.streamon()

# Speed of the drone
SPEED = 30

def execute_command(command_function):
    """Executes a drone command function and optionally adds a small delay."""
    command_function()
    time.sleep(0.10)  # A small delay to ensure command execution does not block

# Define actions mapped to key commands
key_action_map = {
    pygame.K_SPACE: lambda: execute_command(drone.takeoff),
    pygame.K_ESCAPE: lambda: execute_command(drone.land),
    pygame.K_w: lambda: execute_command(lambda: drone.forward(SPEED)),
    pygame.K_s: lambda: execute_command(lambda: drone.back(SPEED)),
    pygame.K_a: lambda: execute_command(lambda: drone.left(SPEED)),
    pygame.K_d: lambda: execute_command(lambda: drone.right(SPEED)),
    pygame.K_UP: lambda: execute_command(lambda: drone.up(15)),
    pygame.K_DOWN: lambda: execute_command(lambda: drone.down(SPEED)),
    pygame.K_LEFT: lambda: execute_command(lambda: drone.ccw(SPEED)),
    pygame.K_RIGHT: lambda: execute_command(lambda: drone.cw(SPEED)),
    pygame.K_o: lambda : execute_command(lambda: drone.flip('b')),
    pygame.K_p: lambda : execute_command(lambda: drone.flip('f')),
}

def main():
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                action = key_action_map.get(event.key)
                if action:
                    action()  # Execute the mapped function

        # Display the video frame by continuously updating it within the while loop
        cv2.waitKey(1)

    # Clean up on exit
    drone.streamoff()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
