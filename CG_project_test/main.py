from vpython import box, vector, rate, scene, color, cylinder, cone, sphere, label, graph, gcurve
import random
import pygame
import time
import math

# Initialize pygame mixer for sound
pygame.mixer.init()

# Load sound effects (dummy paths, replace with actual paths)
launch_sound = pygame.mixer.Sound('countdown.wav')
deploy_sound = pygame.mixer.Sound('launch1.wav')


# Set up the scene
scene.width = 1500
scene.height = 800
scene.title = "Rocket Launch and Deployment Simulation"
scene.autoscale = False
scene.range = 200

# Create the launch pad
launch_pad_base = box(pos=vector(0, -170, 0), length=60, height=1, width=60, color=color.gray(0.4))
launch_pad_support_left = box(pos=vector(-25, -150, 0), length=1, height=20, width=1, color=color.gray(0.4))
launch_pad_support_right = box(pos=vector(25, -150, 0), length=1, height=20, width=1, color=color.gray(0.4))
launch_pad_support_back = box(pos=vector(0, -150, -25), length=60, height=20, width=1, color=color.gray(0.4))

# Create the side stands
side_stand_left = box(pos=vector(-40, -150, 0), length=1, height=15, width=15, color=color.gray(0.3))
side_stand_right = box(pos=vector(40, -150, 0), length=1, height=15, width=15, color=color.gray(0.3))

# Create horizontal supports for the side stands
side_stand_horizontal_left = box(pos=vector(-40, -155, -15), length=60, height=1, width=15, color=color.gray(0.3))
side_stand_horizontal_right = box(pos=vector(40, -155, -15), length=60, height=1, width=15, color=color.gray(0.3))

# Create the first stage of the rocket
first_stage_body = cylinder(pos=vector(0, -153, 0), axis=vector(0, 20, 0), radius=4, color=color.gray(0.9))
first_stage_booster_left = cylinder(pos=vector(-6, -153, 0), axis=vector(0, 20, 0), radius=2, color=color.gray(0.5))
first_stage_booster_right = cylinder(pos=vector(6, -153, 0), axis=vector(0, 20, 0), radius=2, color=color.gray(0.5))

# Create the second stage of the rocket
second_stage_body = cylinder(pos=vector(0, -133, 0), axis=vector(0, 20, 0), radius=4, color=color.white)
second_stage_nose = cone(pos=vector(0, -113, 0), axis=vector(0, 10, 0), radius=4, color=color.gray(0.7))

# Create the ground
ground = box(pos=vector(0, -180, 0), length=500, height=1, width=100, color=color.green)

graph_width = 500
graph_height = 200
graph_x_offset = scene.width // 2 - graph_width // 2
graph_y_offset = scene.height // 2 - graph_height

altitude_graph = graph(title="Rocket Altitude Over Time", xtitle="Time (s)", ytitle="Altitude (m)", width=graph_width,
                       height=graph_height, align='right', foreground=color.white, background=color.black,
                       pos=vector(scene.width - graph_width - 10, scene.height - graph_height, 0))
altitude_curve = gcurve(graph=altitude_graph, color=color.red)

trajectory_graph = graph(title="Rocket Trajectory Over Time", xtitle="Time (s)", ytitle="Horizontal Distance (m)",
                         width=graph_width, height=graph_height, align='right', foreground=color.white, background=color.black,
                         pos=vector(scene.width - graph_width - 10, scene.height - 2 * graph_height - 10, 0))
trajectory_curve = gcurve(graph=trajectory_graph, color=color.blue)

speed_graph = graph(title="Rocket Speed Over Time", xtitle="Time (s)", ytitle="Speed (m/s)", width=graph_width,
                    height=graph_height, align='right', foreground=color.white, background=color.black,
                    pos=vector(scene.width - graph_width - 10, scene.height - 3 * graph_height - 20, 0))
speed_curve = gcurve(graph=speed_graph, color=color.green)
# Parameters
launch_height = 250
deploy_height = 90
stage_separation_height = 40
satellite_distance = 50  # Distance the satellite will move away from the rocket

# Fire parameters
fire_particles = []
fire_rate = 50
fire_lifetime = 2
initial_fire_intensity = 1.0
fade_out_duration = 5.0
fire_intensity = float(initial_fire_intensity)

# Countdown timer parameters
countdown_duration = 11
countdown_label = label(pos=vector(-scene.range + 20, -scene.range + 10, 0), text='', height=12, color=color.white,
                        box=False)

# Gravity parameters for falling objects
gravity = 0.05
cone_gravity = 0.05
booster_velocity_left = 0
booster_velocity_right = 0
rocket_body_velocity = 0

# Cones (exhaust thrusters)
cone_radius = 2
cone_height = 7
first_stage_exhaust = cone(pos=vector(0, -158, 0), axis=vector(0, cone_height, 0), radius=cone_radius, color=color.gray(0.4))
booster_left_exhaust = cone(pos=vector(-6, -158, 0), axis=vector(0, cone_height, 0), radius=cone_radius, color=color.gray(0.4))
booster_right_exhaust = cone(pos=vector(6, -158, 0), axis=vector(0, cone_height, 0), radius=cone_radius, color=color.gray(0.4))

# Initialize velocities for cones
first_stage_exhaust_velocity = vector(0, 0, 0)
booster_left_exhaust_velocity = vector(0, 0, 0)
booster_right_exhaust_velocity = vector(0, 0, 0)

# Main animation loop
t = 0
dt = 0.2
rocket_speed = 0.2
acceleration = 0.1
fade_start_time = None
satellite = None
horizontal_distance = 0
previous_position = vector(0, -153, 0)

# Play launch sound
launch_sound.play()

# Delay start of countdown
time.sleep(6)

# Countdown function
def countdown():
    global countdown_duration
    while countdown_duration > 0:
        countdown_label.text = f'Countdown:00:00:{countdown_duration}'
        countdown_duration -= 1
        rate(1)
    countdown_label.visible = False

# Start countdown
countdown()

# Play deployment sound
deploy_sound.play()

first_stage_active = True
separation_done = False
satellite_deployed = False

def create_fire_particles(base_pos):
    for _ in range(int(fire_rate * fire_intensity)):
        particle_pos = vector(base_pos.x, base_pos.y-12, base_pos.z)
        particle = sphere(pos=particle_pos, radius=random.uniform(1, 3),
                          color=random.choice([color.orange, color.orange, color.orange, color.gray(0.7)]))
        particle.velocity = vector(2 * (1 - 2 * random.random()), -4 * random.uniform(0.8, 1.2),
                                   2 * (1 - 2 * random.random()))
        particle.lifetime = fire_lifetime
        fire_particles.append(particle)

while True:
    rate(60)

    if first_stage_active:
        first_stage_body.pos.y += rocket_speed * dt
        first_stage_booster_left.pos.y += rocket_speed * dt
        first_stage_booster_right.pos.y += rocket_speed * dt
        second_stage_body.pos.y += rocket_speed * dt
        second_stage_nose.pos.y += rocket_speed * dt

        # Update the position of exhaust cones
        first_stage_exhaust.pos = vector(first_stage_body.pos.x, first_stage_body.pos.y - cone_height, first_stage_body.pos.z)
        booster_left_exhaust.pos = vector(first_stage_booster_left.pos.x, first_stage_booster_left.pos.y - cone_height, first_stage_booster_left.pos.z)
        booster_right_exhaust.pos = vector(first_stage_booster_right.pos.x, first_stage_booster_right.pos.y - cone_height, first_stage_booster_right.pos.z)

        if fire_intensity > 0:
            create_fire_particles(first_stage_body.pos)
            create_fire_particles(first_stage_booster_left.pos)
            create_fire_particles(first_stage_booster_right.pos)
    else:
        second_stage_body.pos.y += rocket_speed * dt
        second_stage_nose.pos.y += rocket_speed * dt

        # Update the positions of the exhaust cones
        if separation_done:
            first_stage_exhaust.pos += first_stage_exhaust_velocity * dt
            booster_left_exhaust.pos += booster_left_exhaust_velocity * dt
            booster_right_exhaust.pos += booster_right_exhaust_velocity * dt

    # Update rocket speed based on acceleration
    if first_stage_active:
        rocket_speed += acceleration * dt

    # Calculate horizontal distance for trajectory graph
    current_position = vector(first_stage_body.pos.x, first_stage_body.pos.y, first_stage_body.pos.z)
    horizontal_distance = current_position.x - previous_position.x
    previous_position = current_position

    # Update graphs
    altitude_curve.plot(t, second_stage_body.pos.y)
    trajectory_curve.plot(t, horizontal_distance)
    speed_curve.plot(t, rocket_speed)

    # Update fire particles
    for particle in fire_particles[:]:
        particle.pos += particle.velocity * dt
        particle.lifetime -= dt
        particle.radius *= 0.99
        particle.color = vector(particle.color.x, particle.color.y, particle.color.z) * 0.99
        if particle.lifetime <= 0:
            fire_particles.remove(particle)
            particle.visible = False

    if second_stage_body.pos.y >= stage_separation_height and first_stage_active:
        first_stage_active = False
        first_stage_body.color = color.gray(0.5)  # Change color to indicate it's inactive
        first_stage_booster_left.color = color.gray(0.5)
        first_stage_booster_right.color = color.gray(0.5)
        rocket_speed *= 0.5  # Reduce speed after separation
        separation_done = True
        fade_start_time = t  # Record the time when separation happens

        # Initialize cone velocities to match rocket and booster velocities
        first_stage_exhaust_velocity = vector(0, rocket_speed, 0)
        booster_left_exhaust_velocity = vector(0, rocket_speed, 0)
        booster_right_exhaust_velocity = vector(0, rocket_speed, 0)

        # Create the satellite with solar panels
        satellite = box(pos=second_stage_nose.pos, length=8, width=8, height=8, color=color.red)

        # Create solar panels
        panel_thickness = 1
        panel_length = 12
        panel_width = 4
        left_panel = box(pos=satellite.pos + vector(-panel_length / 2, 0, 0),
                         size=vector(panel_length, panel_width, panel_thickness), color=color.yellow)
        right_panel = box(pos=satellite.pos + vector(panel_length / 2, 0, 0),
                          size=vector(panel_length, panel_width, panel_thickness), color=color.yellow)

        # Attach panels to satellite
        satellite.panels = [left_panel, right_panel]

        # satellite_sound.play()  # Play satellite deployment sound

    # Gradually fade out fire intensity after separation
    if separation_done:
        elapsed_time = t - fade_start_time
        fire_intensity = max(0.0, initial_fire_intensity * (1.0 - (elapsed_time / fade_out_duration)))
        # Reduce the number of fire particles gradually
        for _ in range(int(fire_rate * fire_intensity)):
            if len(fire_particles) > 0:
                particle = fire_particles.pop(0)
                particle.visible = False

        # Animate satellite deployment
        if satellite and not satellite_deployed:
            satellite.pos.y += rocket_speed * dt  # Move the satellite upwards
            for panel in satellite.panels:
                panel.pos.y += rocket_speed * dt  # Move the panels with the satellite
            if satellite.pos.y >= second_stage_body.pos.y + satellite_distance:
                satellite_deployed = True
                satellite.visible = False  # Hide the satellite after deployment
                for panel in satellite.panels:
                    panel.visible = False  # Hide the panels after satellite deployment

        # Make separated boosters, rocket body, and cones fall slowly to the ground
        if not first_stage_active:
            # Stop objects when they hit the ground
            if first_stage_body.pos.y > -180:
                first_stage_body.pos.y -= rocket_body_velocity * dt
                rocket_body_velocity += gravity
            else:
                first_stage_body.pos.y = -180
                rocket_body_velocity = 0

            if first_stage_booster_left.pos.y > -180:
                first_stage_booster_left.pos.y -= booster_velocity_left * dt
                booster_velocity_left += gravity
            else:
                first_stage_booster_left.pos.y = -180
                booster_velocity_left = 0

            if first_stage_booster_right.pos.y > -180:
                first_stage_booster_right.pos.y -= booster_velocity_right * dt
                booster_velocity_right += gravity
            else:
                first_stage_booster_right.pos.y = -180
                booster_velocity_right = 0

            # Update the falling and stopping behavior of the cones
            if first_stage_exhaust.pos.y > -180:
                first_stage_exhaust_velocity.y -= cone_gravity
                first_stage_exhaust.pos.y += first_stage_exhaust_velocity.y * dt
                if first_stage_exhaust.pos.y <= -180:
                    first_stage_exhaust.pos.y = -180
                    first_stage_exhaust_velocity.y = 0

            if booster_left_exhaust.pos.y > -180:
                booster_left_exhaust_velocity.y -= cone_gravity
                booster_left_exhaust.pos.y += booster_left_exhaust_velocity.y * dt
                if booster_left_exhaust.pos.y <= -180:
                    booster_left_exhaust.pos.y = -180
                    booster_left_exhaust_velocity.y = 0

            if booster_right_exhaust.pos.y > -180:
                booster_right_exhaust_velocity.y -= cone_gravity
                booster_right_exhaust.pos.y += booster_right_exhaust_velocity.y * dt
                if booster_right_exhaust.pos.y <= -180:
                    booster_right_exhaust.pos.y = -180
                    booster_right_exhaust_velocity.y = 0

    t += dt
