import sys

import pygame
import pso_core

# --- Configuration Constants ---
WIDTH, HEIGHT = 1000, 600
CANVAS_W = 800  # 800px for simulation, 200px for UI sidebar
FPS = 60

# A square world is easier for the engine; the renderer stretches it to fit the canvas.
WORLD_HALF = min(CANVAS_W, HEIGHT) / 2.0

# Colors
COLOR_BG = (20, 24, 30)
COLOR_SIDEBAR = (30, 35, 45)
COLOR_GRID = (35, 42, 55)
COLOR_TARGET = (235, 87, 87)
COLOR_PARTICLE = (86, 204, 242)
COLOR_BEST = (242, 201, 76)
COLOR_TEXT = (220, 225, 230)


def world_to_screen(x: float, y: float) -> tuple[int, int]:
    sx = (x / WORLD_HALF) * (CANVAS_W / 2.0) + (CANVAS_W / 2.0)
    sy = (-y / WORLD_HALF) * (HEIGHT / 2.0) + (HEIGHT / 2.0)
    return int(round(sx)), int(round(sy))


def screen_to_world(mx: float, my: float) -> tuple[float, float]:
    x = ((mx - (CANVAS_W / 2.0)) / (CANVAS_W / 2.0)) * WORLD_HALF
    y = -((my - (HEIGHT / 2.0)) / (HEIGHT / 2.0)) * WORLD_HALF
    return x, y


def main():
    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("PSO Swarm Intelligence Visualizer")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Consolas", 14)

    # 1. Initialize C++ Terrain & Swarm
    terrain = pso_core.Terrain(float(WORLD_HALF), 140.0)
    terrain.regenerate_decoys(3)

    # Initial target, expressed in screen coordinates and converted to world coordinates.
    initial_target_world = screen_to_world(CANVAS_W / 2 + 100, HEIGHT / 2 - 100)
    terrain.set_target(*initial_target_world)

    max_vel = 7.0
    num_particles = 60
    swarm = pso_core.Swarm(terrain, num_particles, max_vel)

    # ONE-TIME DEBUG PRINT (Placed safely OUTSIDE the main loop)
    initial_pos = swarm.get_pos()
    print(f"[DEBUG] Initialized Swarm with {len(initial_pos)} particles from C++.")
    if len(initial_pos) > 0:
        print(f"[DEBUG] First particle position: {initial_pos[0]}")

    # Simulation Controls
    running = True
    paused = False

    # PSO Parameters
    w = 0.729   # Inertia weight
    c1 = 1.494  # Cognitive coefficient
    c2 = 1.494  # Social coefficient

    while running:
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    swarm.reset()
                    terrain.regenerate_decoys(8)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if mx < CANVAS_W:
                    terrain.set_target(*screen_to_world(mx, my))

        # --- Physics Update ---
        if not paused:
            swarm.step(w, c1, c2, max_vel)

        # --- Rendering ---
        screen.fill(COLOR_BG)

        # Grid Lines
        for x in range(0, CANVAS_W, 50):
            pygame.draw.line(screen, COLOR_GRID, (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, 50):
            pygame.draw.line(screen, COLOR_GRID, (0, y), (CANVAS_W, y))

        # Target Point
        tx_world, ty_world = terrain.get_target_x(), terrain.get_target_y()
        tx_screen, ty_screen = world_to_screen(tx_world, ty_world)
        pygame.draw.circle(screen, COLOR_TARGET, (tx_screen, ty_screen), 12, 2)
        pygame.draw.circle(screen, COLOR_TARGET, (tx_screen, ty_screen), 4)

        # Global Best Marker
        gb_x_world, gb_y_world = swarm.get_best_x(), swarm.get_best_y()
        gb_x_screen, gb_y_screen = world_to_screen(gb_x_world, gb_y_world)
        pygame.draw.circle(screen, COLOR_BEST, (gb_x_screen, gb_y_screen), 8, 2)

        # Particles
        particle_positions = swarm.get_pos()
        for pos in particle_positions:
            px, py = world_to_screen(pos[0], pos[1])
            pygame.draw.circle(screen, COLOR_PARTICLE, (px, py), 3)

        # Sidebar UI
        pygame.draw.rect(screen, COLOR_SIDEBAR, (CANVAS_W, 0, WIDTH - CANVAS_W, HEIGHT))

        info_lines = [
            "--- PSO CONTROLS ---",
            "[Space]  : Pause/Resume",
            "[R]      : Reset Swarm",
            "[L-Click]: Set Target",
            "",
            "--- SWARM STATS ---",
            f"Status   : {'PAUSED' if paused else 'RUNNING'}",
            f"Target   : ({tx_screen}, {ty_screen})",
            f"G-Best   : ({gb_x_screen}, {gb_y_screen})",
            "",
            "--- PARAMETERS ---",
            f"Inertia (w) : {w:.3f}",
            f"Cognitive(c1): {c1:.3f}",
            f"Social   (c2): {c2:.3f}",
        ]

        y_offset = 20
        for line in info_lines:
            txt_surface = font.render(line, True, COLOR_TEXT)
            screen.blit(txt_surface, (CANVAS_W + 15, y_offset))
            y_offset += 22

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
