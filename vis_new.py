import sys

import pygame
import pygame_gui
import pso_core
import numpy as np

# --- Configuration Constants ---
WIDTH, HEIGHT = 1100, 900
CANVAS_W = 900  # 800px for simulation, 200px for UI sidebar
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
    # Scale uniformly based on HEIGHT to prevent horizontal stretching
    sx = (x / WORLD_HALF) * (HEIGHT / 2.0) + (CANVAS_W / 2.0)
    sy = (-y / WORLD_HALF) * (HEIGHT / 2.0) + (HEIGHT / 2.0)
    return int(round(sx)), int(round(sy))

def screen_to_world(mx: float, my: float) -> tuple[float, float]:
    # Reverse the uniform scaling
    x = ((mx - (CANVAS_W / 2.0)) / (HEIGHT / 2.0)) * WORLD_HALF
    y = -((my - (HEIGHT / 2.0)) / (HEIGHT / 2.0)) * WORLD_HALF
    return x, y

def generate_landscape_visual(terrain, w, h):
    # Step = 2 provides an ideal balance: lightning fast generation (4x fewer points)
    # while keeping contour lines sharp and smooth when scaled to full screen.
    step = 2
    xs, ys = np.arange(0, w, step), np.arange(0, h, step)
    gx, gy = np.meshgrid(xs, ys, indexing='ij') 
    wx = ((gx.astype(np.float64) - (w / 2.0)) / (h / 2.0)) * WORLD_HALF
    wy = -((gy.astype(np.float64) - (h / 2.0)) / (h / 2.0)) * WORLD_HALF

    points = np.column_stack((wx.ravel(), wy.ravel()))
    
    try:
        z_flat = terrain.fitness_at(points)
        z = np.array(z_flat).reshape(gx.shape)
    except Exception:
        z = np.zeros(gx.shape)
        # 2. CRITICAL FIX: Use the converted wx/wy arrays instead of xs/ys pixels
        for i in range(len(xs)):
            for j in range(len(ys)):
                z[i, j] = terrain.fitness_at(float(wx[i, j]), float(wy[i, j]))

    z_min, z_max = z.min(), z.max()
    z = (z - z_min) / (z_max - z_min) if z_max > z_min else np.zeros_like(z)
        
    color = np.zeros((*z.shape, 3), dtype=np.uint8)
    stops = [
        (0.00, np.array([14, 14, 22])), (0.35, np.array([26, 50, 76])),
        (0.60, np.array([20, 96, 92])), (0.82, np.array([182, 122, 46])),
        (1.00, np.array([255, 205, 110]))
    ]
    
    for i in range(len(stops) - 1):
        t0, c0 = stops[i]
        t1, c1 = stops[i + 1]
        mask = (z >= t0) & (z <= t1)
        local_t = (z[mask] - t0) / (t1 - t0 or 1.0)
        for ch in range(3):
            color[..., ch][mask] = c0[ch] + local_t * (c1[ch] - c0[ch])

    band = (z * 10).astype(int)
    edge = np.zeros_like(band, dtype=bool)
    edge[1:, :] |= band[1:, :] != band[:-1, :]
    edge[:, 1:] |= band[:, 1:] != band[:, :-1]
    color[edge] = (color[edge] * 0.55).astype(np.uint8)

    surface = pygame.surfarray.make_surface(color)
    return pygame.transform.smoothscale(surface, (w, h))

def main():
    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("PSO Swarm Intelligence Visualizer")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Consolas", 14)

    terrain = pso_core.Terrain(float(WORLD_HALF), 140.0)
    terrain.regenerate_decoys(3)
    initial_target_world = screen_to_world(CANVAS_W / 2 + 100, HEIGHT / 2 - 100)
    terrain.set_target(*initial_target_world)
    
    max_vel = 7.0
    num_particles = 60
    swarm = pso_core.Swarm(terrain, num_particles, max_vel)

    initial_pos = swarm.get_pos()
    print(f"initialized Swarm with {len(initial_pos)} particles from C++.")
    if len(initial_pos) > 0:
        print(f"first particle position: {initial_pos[0]}")
        print(f"max x: {max(initial_pos, key=lambda p: p[0])}")
        print(f"min x: {min(initial_pos, key=lambda p: p[0])}")
        print(f"max y: {max(initial_pos, key=lambda p: p[1])}")
        print(f"min y: {min(initial_pos, key=lambda p: p[1])}")

    # Simulation Controls
    running = True
    paused = False
    retargeting = True

    bg_surface = generate_landscape_visual(terrain, CANVAS_W, HEIGHT)

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
                elif event.key == pygame.K_t:
                    retargeting = not retargeting

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if mx < CANVAS_W:
                    terrain.set_target(*screen_to_world(mx, my))
                    bg_surface = generate_landscape_visual(terrain, CANVAS_W, HEIGHT)
                    if retargeting:
                        swarm.retarget()

        if not paused:
            swarm.step(w, c1, c2, max_vel)

        # --- Rendering ---
        screen.fill(COLOR_BG)
        screen.blit(bg_surface, (0, 0))

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
            pygame.draw.circle(screen, COLOR_PARTICLE, (px, py), 5)

        # Sidebar UI
        pygame.draw.rect(screen, COLOR_SIDEBAR, (CANVAS_W, 0, WIDTH - CANVAS_W, HEIGHT))

        info_lines = [
            "--- PSO CONTROLS ---",
            "[Space]  : Pause/Resume",
            "[R]      : Reset Swarm",
            "[L-Click]: Set Target",
            "[T]      : Retarget",
            "",
            "--- SWARM STATS ---",
            f"Status   : {'PAUSED' if paused else 'RUNNING'}",
            f"Target   : ({tx_screen}, {ty_screen})",
            f"G-Best   : ({gb_x_screen}, {gb_y_screen})",
            f"Retarget : {'ON' if retargeting else 'OFF'}",
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
