"""systems/particles.py — Kinematic Particle Simulation System (Milestone 4E).

Implements a lightweight, deterministic 2D particle system for celebratory bursts
and atmospheric light effects in LUMEN.

Each particle simulates:
- Position (x, y)
- Velocity (vx, vy) with drag damping
- Lifetime (current life and max life)
- Size (radius in pixels, smoothly scaling with life fraction)
- Alpha transparency (0..255, fading with remaining life)
- Color (RGB tuple from a curated ancient-temple celestial palette)

Particles update over time using numerical integration and are removed from memory
when their lifetime expires.
"""

from dataclasses import dataclass
import math
import random
import pygame


@dataclass
class Particle:
    """Represents an individual physical particle in the simulation."""

    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    size: float
    color: tuple[int, int, int]
    alpha: float = 255.0
    drag: float = 0.95

    @property
    def is_alive(self) -> bool:
        """Returns True if the particle still has remaining lifespan."""
        return self.life > 0.0

    def update(self, dt: float) -> bool:
        """Updates particle kinematics, attenuates alpha, and returns True if alive."""
        if self.life <= 0.0:
            return False

        self.life -= dt
        if self.life <= 0.0:
            self.life = 0.0
            self.alpha = 0.0
            return False

        # Kinematic position update: x(t + dt) = x(t) + v * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Velocity damping / atmospheric drag
        damping = self.drag ** (dt * 60.0)
        self.vx *= damping
        self.vy *= damping

        # Alpha transparency decay based on remaining lifetime fraction
        fraction = max(0.0, min(1.0, self.life / self.max_life))
        self.alpha = 255.0 * fraction
        return True


class ParticleSystem:
    """Manages emission, numerical updates, culling, and rendering of particle groups."""

    def __init__(self):
        self.particles: list[Particle] = []

    def emit_celebration_burst(self, origin_x: float, origin_y: float, count: int = 65):
        """Emits a celebratory burst of radiant golden and azure celestial sparks."""
        # Curated harmonious ancient temple color palette
        palette = [
            (255, 225, 110),  # Radiant gold
            (255, 195, 60),   # Warm amber
            (90, 180, 255),   # Celestial azure
            (160, 230, 255),  # Prismatic cyan
            (110, 245, 170),  # Verdant harmonic
            (255, 255, 240),  # Pure starlight
        ]

        for _ in range(count):
            angle = random.uniform(0.0, 2.0 * math.pi)
            speed = random.uniform(35.0, 185.0)
            vx = math.cos(angle) * speed
            # Buoyancy bias toward ceiling / heavens
            vy = math.sin(angle) * speed - random.uniform(15.0, 50.0)

            life = random.uniform(1.2, 2.4)
            size = random.uniform(2.0, 5.0)
            color = random.choice(palette)

            p = Particle(
                x=float(origin_x),
                y=float(origin_y),
                vx=vx,
                vy=vy,
                life=life,
                max_life=life,
                size=size,
                color=color,
                alpha=255.0,
                drag=0.94,
            )
            self.particles.append(p)

    def update(self, dt: float):
        """Updates all living particles and removes expired ones from memory."""
        alive = []
        for p in self.particles:
            if p.update(dt):
                alive.append(p)
        self.particles = alive

    def clear(self):
        """Removes all active particles."""
        self.particles.clear()

    @property
    def particle_count(self) -> int:
        """Returns the number of currently active particles."""
        return len(self.particles)

    def draw(self, surface: pygame.Surface, camera_offset: tuple[int, int] = (0, 0)):
        """Renders active particles with alpha transparency onto the destination surface."""
        if not self.particles:
            return

        ox, oy = camera_offset
        sw, sh = surface.get_size()

        for p in self.particles:
            sx = int(p.x - ox)
            sy = int(p.y - oy)

            # Viewport culling
            r = int(max(1.0, p.size * (p.life / p.max_life)))
            if sx + r < 0 or sx - r >= sw or sy + r < 0 or sy - r >= sh:
                continue

            a = int(max(0, min(255, p.alpha)))
            if a <= 0:
                continue

            # Render circular light mote with alpha blending
            p_surf = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(p_surf, (*p.color, a), (r + 2, r + 2), r)
            # Soft atmospheric halo
            if r >= 2:
                pygame.draw.circle(p_surf, (*p.color, a // 3), (r + 2, r + 2), r + 1)

            surface.blit(p_surf, (sx - r - 2, sy - r - 2), special_flags=pygame.BLEND_ALPHA_SDL2)
