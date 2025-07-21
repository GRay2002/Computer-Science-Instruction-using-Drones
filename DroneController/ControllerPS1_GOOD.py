import pygame
import cv2
import time
from easytello import tello


# Initialize Pygame and Joystick
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
    time.sleep(0.10)  # A small delay to ensure command execution

# Initialize Joystick
pygame.joystick.init()
if pygame.joystick.get_count() > 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
else:
    print("No joystick found. Please connect a joystick.")
    exit()

def handle_joystick_input(event):
    if event.type == pygame.JOYBUTTONDOWN:
        if event.button == 3:  # Square for takeoff
            execute_command(drone.takeoff)
        elif event.button == 1:  # Circle for land
            execute_command(drone.land)
        elif event.button == 0:  # Triangle for up
            execute_command(lambda: drone.up(15))
        elif event.button == 2:  # X for down
            execute_command(lambda: drone.down(15))
        elif event.button == 6:  # L trigger for cw
            execute_command(lambda: drone.cw(SPEED))
        elif event.button == 7:  # R trigger for ccw
            execute_command(lambda: drone.ccw(SPEED))
        elif event.button == 4:
            execute_command(lambda: drone.flip('f'))
        elif event.button == 5:
            execute_command(lambda: drone.flip('b'))

    elif event.type == pygame.JOYAXISMOTION:
        if event.axis == 0:  # X axis
            if event.value < 0:
                execute_command(lambda: drone.left(SPEED))
            elif event.value > 0:
                execute_command(lambda: drone.right(SPEED))
        elif event.axis == 1:  # Y axis
            if event.value < 0:
                execute_command(lambda: drone.forward(SPEED))
            elif event.value > 0:
                execute_command(lambda: drone.back(SPEED))

def main():
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type in [pygame.JOYAXISMOTION, pygame.JOYBUTTONDOWN]:
                handle_joystick_input(event)

        cv2.waitKey(1)

    # Clean up on exit
    drone.streamoff()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
