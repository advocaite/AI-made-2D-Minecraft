# Example dimensions for background images:
# - Mountains: 1920x1080 pixels (wide and detailed)
# - Clouds: 2560x720 pixels (wide and slim)
# Adjust dimensions as needed for your design.

import pygame
import os
import random  # new import
import math    # new import

class ParallaxBackground:
    def __init__(self, screen_width, screen_height):
        # Adjust base_path to locate the 'backgrounds' folder relative to this file.
        base_path = os.path.join(os.path.dirname(__file__), "backgrounds")
        self.layers = [
            {
                "image": pygame.image.load(os.path.join(base_path, "mountains.png")).convert_alpha(),
                "factor": 0.5,
                "v_offset": 200  # NEW: vertical offset adjustment for this layer
            }
        ]
        self.screen_width = screen_width
        self.screen_height = screen_height
        # Replace simple flash variables with lightning bolt effect variables.
        self.lightning_bolts = []   # list of bolts (each bolt is a list of points)
        self.lightning_duration = 200  # bolt effect duration in milliseconds
        self.lightning_timer = 0
        # New: subtle overall flash alpha
        self.flash_alpha = 0
        # New: glow surface for lightning points (radius = 30)
        self.glow = self._create_glow_surface(30)
        # New: Weather state and particle list
        self.weather = "clear"  # options: "clear", "rain", "snow", "storm"
        self.weather_particles = []

    def _create_glow_surface(self, radius):
        glow = pygame.Surface((radius*2, radius*2), flags=pygame.SRCALPHA)
        for ix in range(radius*2):
            for iy in range(radius*2):
                dx = ix - radius
                dy = iy - radius
                dist = math.sqrt(dx*dx + dy*dy)
                if dist < radius:
                    a = int(200 * (1 - dist / radius))
                    glow.set_at((ix, iy), (255, 255, 224, a))
        return glow

    def trigger_lightning(self):
        # Only trigger lightning during a storm.
        if self.weather != "storm":
            return
        # Generate one bolt bolt effect.
        bolt = []
        start_x = random.randint(0, self.screen_width)
        y = 0
        bolt.append((start_x, y))
        while y < self.screen_height // 2:
            x_offset = random.randint(-20, 20)
            y_offset = random.randint(10, 30)
            start_x = max(0, min(self.screen_width, start_x + x_offset))
            y += y_offset
            bolt.append((start_x, y))
        self.lightning_bolts = [bolt]
        self.lightning_timer = self.lightning_duration
        # Set a more transparent flash (lower intensity).
        self.flash_alpha = 10  # changed from 50

    def draw(self, surface, cam_offset_x, dt=0):
        for layer in self.layers:
            # Calculate horizontal offset based on parallax factor
            offset = cam_offset_x * layer["factor"]
            image = layer["image"]
            image_width = image.get_width()
            x = -offset % image_width - image_width
            # NEW: Apply vertical offset from layer dictionary.
            y = self.screen_height - image.get_height() + layer.get("v_offset", 0)
            while x < self.screen_width:
                surface.blit(image, (x, y))
                x += image_width
        # Note: lightning effects are now rendered via get_light_effect().
        # New: Render current weather effects on the same render layer.
        self.draw_weather(surface, dt)

    def get_light_effect(self, dt):
        # Build effect overlay to be merged into the overall lightmap.
        effect = pygame.Surface((self.screen_width, self.screen_height), flags=pygame.SRCALPHA)
        if self.lightning_timer > 0 and self.lightning_bolts:
            alpha = int(255 * (self.lightning_timer / self.lightning_duration))
            for bolt in self.lightning_bolts:
                pygame.draw.lines(effect, (255, 255, 255, alpha), False, bolt, 2)
                for point in bolt:
                    # Draw a subtle outline glow (1-2 pixels)
                    pygame.draw.circle(effect, (255, 255, 224, alpha), point, 2)
            self.lightning_timer -= dt
            if self.lightning_timer <= 0:
                self.lightning_bolts = []
        if self.flash_alpha > 0:
            flash_overlay = pygame.Surface((self.screen_width, self.screen_height), flags=pygame.SRCALPHA)
            # Adjust multiplier for smoother fade in/out
            effective_alpha = int(self.flash_alpha * 0.5)
            flash_overlay.fill((255, 255, 255, effective_alpha))
            effect.blit(flash_overlay, (0, 0))
            # Slow down the decrement for a gradual fade
            self.flash_alpha = max(self.flash_alpha - int(0.1 * dt), 0)
        return effect

    def set_weather(self, weather_type):
        # Set new weather type and reinitialize particles.
        self.weather = weather_type
        self.weather_particles = []
        if weather_type in ("rain", "storm"):
            # Use more particles for a storm if needed.
            count = 120 if weather_type == "storm" else 100
            for _ in range(count):
                x = random.randint(0, self.screen_width)
                y = random.randint(0, self.screen_height)
                speed = random.randint(300, 500) / 1000  # pixels per ms
                self.weather_particles.append({"x": x, "y": y, "speed": speed})
        elif weather_type == "snow":
            for _ in range(80):
                x = random.randint(0, self.screen_width)
                y = random.randint(0, self.screen_height)
                speed = random.randint(50, 150) / 1000
                self.weather_particles.append({"x": x, "y": y, "speed": speed})
        # For "clear", no particles.

    def update_weather(self, dt):
        if self.weather not in ("rain", "snow"):
            return
        for p in self.weather_particles:
            p["y"] += p["speed"] * dt
            if p["y"] > self.screen_height:
                p["y"] = -5
                p["x"] = random.randint(0, self.screen_width)

    def draw_weather(self, surface, dt):
        self.update_weather(dt)
        if self.weather == "rain":
            for p in self.weather_particles:
                start = (int(p["x"]), int(p["y"]))
                # Draw a slightly slanted raindrop for a falling effect.
                end = (int(p["x"] - 2), int(p["y"]) + 10)
                pygame.draw.line(surface, (100, 100, 255, 180), start, end, 1)
        elif self.weather == "snow":
            for p in self.weather_particles:
                # Add a gentle horizontal oscillation for snow
                offset = int(2 * math.sin(p["y"] * 0.05))
                pygame.draw.circle(surface, (255, 255, 255, 200), (int(p["x"] + offset), int(p["y"])), 2)
