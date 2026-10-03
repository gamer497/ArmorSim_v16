import math
import random
import sys
import numpy as np
import pygame
import pymunk

# --- Display & Colors ---
WIDTH, HEIGHT = 1340, 840
FPS = 60

COLOR_BG = (12, 14, 18)
COLOR_PANEL = (22, 26, 34)
COLOR_PANEL_BORDER = (38, 46, 60)
COLOR_TEXT = (225, 232, 245)
COLOR_TEXT_DIM = (130, 142, 160)
COLOR_ACCENT = (0, 205, 255)
COLOR_GREEN = (46, 204, 113)
COLOR_RED = (231, 76, 60)
COLOR_YELLOW = (241, 196, 15)
COLOR_ORANGE = (230, 126, 34)
COLOR_COPPER = (243, 156, 18)
COLOR_TUNGSTEN = (220, 240, 255)

# Collision Types for Pymunk
COLLTYPE_WALL = 1
COLLTYPE_CREW = 2
COLLTYPE_SPALL = 3

# --- ERA Types ---
ERA_TYPES = {
    "NONE": {
        "name": "ERA: NONE (Disabled)",
        "kin_reduction": 0.0,
        "heat_reduction": 0.0,
        "color": (40, 48, 60),
        "desc": "Standard armor without explosive reactive tiles."
    },
    "KONTAKT_5": {
        "name": "Контакт-5 (Базовая)",
        "kin_reduction": 0.20,
        "heat_reduction": 0.50,
        "color": (56, 142, 60),
        "desc": "Heavy steel flyer plates (-20% Kinetic, -50% HEAT)."
    },
    "RELIKT": {
        "name": "Т-90М 'Реликт' (Усиленная)",
        "kin_reduction": 0.50,
        "heat_reduction": 0.80,
        "color": (102, 187, 106),
        "desc": "Multi-layer flyer plates (-50% Kinetic, -80% HEAT)."
    },
    "DUPLET": {
        "name": "Оплот-М 'Дуплет' (Тандем)",
        "kin_reduction": 0.60,
        "heat_reduction": 0.90,
        "color": (211, 84, 0),
        "desc": "Multi-module tandem counter-jets (-60% Kinetic, -90% HEAT)."
    }
}

SHELL_PRESETS = {
    "APFSDS": {
        "name": "APFSDS (Tungsten Dart)",
        "mass": 4.8, # kg
        "length": 64,
        "width": 6,
        "base_vel": 1750, # m/s
        "pen_power": 1.65,
        "ricochet_angle": 78.0,
        "is_heat": False,
        "color": (215, 240, 255),
        "desc": "High velocity dart: Punches deep, spawns heavy tungsten fragments on full penetration."
    },
    "APCBC": {
        "name": "APCBC (Capped HE)",
        "mass": 10.5,
        "length": 46,
        "width": 14,
        "base_vel": 940,
        "pen_power": 1.15,
        "ricochet_angle": 71.0,
        "is_heat": False,
        "color": (241, 196, 15),
        "desc": "Heavy blunt shot: Wide destruction cavity."
    },
    "APCR": {
        "name": "APCR (Rigid Composite)",
        "mass": 5.4,
        "length": 38,
        "width": 9,
        "base_vel": 1300,
        "pen_power": 1.30,
        "ricochet_angle": 67.0,
        "is_heat": False,
        "color": (52, 152, 219),
        "desc": "Hard composite core: High velocity, sharp ricochet angle."
    },
    "HEAT": {
        "name": "HEAT (Tandem Jet)",
        "mass": 3.6,
        "length": 44,
        "width": 12,
        "base_vel": 1100,
        "pen_power": 2.10,
        "ricochet_angle": 75.0,
        "is_heat": True,
        "color": (231, 76, 60),
        "desc": "Chemical energy jet: Dissipated by ERA explosive flyer plates."
    }
}

class Slider:
    def __init__(self, x, y, w, h, min_val, max_val, initial, label, unit=""):
        self.rect = pygame.Rect(x, y, w, h)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial
        self.label = label
        self.unit = unit
        self.dragging = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self.update_val(event.pos[0])
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.update_val(event.pos[0])
            return True
        return False

    def update_val(self, mouse_x):
        rel = (mouse_x - self.rect.x) / self.rect.w
        rel = max(0.0, min(1.0, rel))
        self.value = self.min_val + rel * (self.max_val - self.min_val)

    def draw(self, surface, font, small_font):
        txt_label = small_font.render(f"{self.label}:", True, COLOR_TEXT_DIM)
        val_str = f"{self.value:.1f}{self.unit}" if (self.max_val - self.min_val < 50) else f"{int(round(self.value))}{self.unit}"
        txt_val = font.render(val_str, True, COLOR_ACCENT)
        surface.blit(txt_label, (self.rect.x, self.rect.y - 17))
        surface.blit(txt_val, (self.rect.right - txt_val.get_width(), self.rect.y - 17))

        pygame.draw.rect(surface, (32, 38, 48), self.rect, border_radius=4)
        fill_w = int(((self.value - self.min_val) / (self.max_val - self.min_val)) * self.rect.w)
        if fill_w > 0:
            pygame.draw.rect(surface, COLOR_ACCENT, (self.rect.x, self.rect.y, fill_w, self.rect.h), border_radius=4)
        thumb_x = self.rect.x + fill_w
        pygame.draw.circle(surface, (245, 250, 255), (thumb_x, self.rect.centery), self.rect.h // 2 + 3)

class Button:
    def __init__(self, x, y, w, h, text, key):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.key = key

    def is_hovered(self, pos):
        return self.rect.collidepoint(pos)

    def draw(self, surface, font, active=False, custom_bg=None):
        hover = self.is_hovered(pygame.mouse.get_pos())
        if active:
            bg_col = custom_bg if custom_bg else COLOR_ACCENT
            text_col = (10, 14, 20)
        elif hover:
            bg_col = (42, 50, 64)
            text_col = (255, 255, 255)
        else:
            bg_col = (26, 31, 40)
            text_col = COLOR_TEXT

        pygame.draw.rect(surface, bg_col, self.rect, border_radius=5)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER if not active else COLOR_ACCENT, self.rect, width=1, border_radius=5)
        txt = font.render(self.text, True, text_col)
        surface.blit(txt, (self.rect.centerx - txt.get_width() // 2, self.rect.centery - txt.get_height() // 2))

# --- High-Resolution Pixel Armor Matrix ---
class HighResArmorMatrix:
    def __init__(self, center_x, center_y, thickness_mm, angle_deg, resistance_factor=1.0, era_type="NONE"):
        self.cx = float(center_x)
        self.cy = float(center_y)
        self.thickness_mm = float(thickness_mm)
        self.angle_deg = float(angle_deg)
        self.resistance_factor = float(resistance_factor)
        self.era_type = era_type

        self.cell_size = 2.4 if thickness_mm <= 300 else (2.4 + (thickness_mm - 300) * 0.0015)
        self.plate_thick_px = self.thickness_mm * 0.42
        self.plate_height_px = 380.0

        self.grid_w = max(100, int((self.plate_thick_px + 80) / self.cell_size) + 20)
        self.grid_h = int(self.plate_height_px / self.cell_size) + 40

        self.grid = np.zeros((self.grid_h, self.grid_w), dtype=np.float32)
        self.surface = pygame.Surface((int(self.grid_w * self.cell_size), int(self.grid_h * self.cell_size)), pygame.SRCALPHA)

        self.era_blocks = []
        self.build_matrix()

    def build_matrix(self):
        self.grid.fill(0.0)
        self.era_blocks.clear()

        rad = math.radians(self.angle_deg)
        cos_a, sin_a = math.cos(rad), math.sin(rad)

        cx_idx = self.grid_w * 0.20
        cy_idx = self.grid_h * 0.5

        for r in range(self.grid_h):
            for c in range(self.grid_w):
                dx = (c - cx_idx) * self.cell_size
                dy = (r - cy_idx) * self.cell_size

                dist_norm = dx * cos_a + dy * sin_a
                dist_tang = -dx * sin_a + dy * cos_a

                if abs(dist_tang) <= (self.plate_height_px * 0.5) and 0.0 <= dist_norm <= self.plate_thick_px:
                    self.grid[r, c] = 100.0

        if self.era_type != "NONE":
            era_cfg = ERA_TYPES[self.era_type]
            era_count = 14 if self.era_type == "DUPLET" else 12
            block_h = (self.plate_height_px * 0.95) / era_count
            tangent = (-sin_a, cos_a)
            normal = (cos_a, sin_a)

            for i in range(era_count):
                offset_t = (i - era_count / 2 + 0.5) * block_h
                bx = self.cx + tangent[0] * offset_t - normal[0] * 14.0
                by = self.cy + tangent[1] * offset_t - normal[1] * 14.0

                self.era_blocks.append({
                    "x": bx,
                    "y": by,
                    "active": True,
                    "w": 16.0 if self.era_type == "DUPLET" else 14.0,
                    "h": block_h * 0.88,
                    "angle": self.angle_deg,
                    "type": self.era_type,
                    "color": era_cfg["color"]
                })

        self.update_surface()

    def update_surface(self):
        self.surface.fill((0, 0, 0, 0))
        rows, cols = np.where(self.grid > 0)
        sz = int(self.cell_size) + 1

        for r, c in zip(rows, cols):
            hp_ratio = self.grid[r, c] / 100.0
            col = (
                int(80 + (1.0 - hp_ratio) * 140),
                int(95 * hp_ratio + 15),
                int(115 * hp_ratio + 20)
            )
            pygame.draw.rect(self.surface, col, (int(c * self.cell_size), int(r * self.cell_size), sz, sz))

    def world_to_grid(self, wx, wy):
        cx_idx = self.grid_w * 0.20
        cy_idx = self.grid_h * 0.5
        c = int((wx - self.cx) / self.cell_size + cx_idx)
        r = int((wy - self.cy) / self.cell_size + cy_idx)
        return r, c

    def excavate_crater(self, hit_x, hit_y, radius_px, damage=100.0):
        r_center, c_center = self.world_to_grid(hit_x, hit_y)
        rad_cells = int(radius_px / self.cell_size) + 1
        destroyed_count = 0

        for dr in range(-rad_cells, rad_cells + 1):
            for dc in range(-rad_cells, rad_cells + 1):
                nr = r_center + dr
                nc = c_center + dc
                if 0 <= nr < self.grid_h and 0 <= nc < self.grid_w:
                    d_px = math.hypot(dc * self.cell_size, dr * self.cell_size)
                    if d_px <= radius_px and self.grid[nr, nc] > 0:
                        self.grid[nr, nc] -= damage
                        if self.grid[nr, nc] <= 0:
                            self.grid[nr, nc] = 0
                            destroyed_count += 1

        if destroyed_count > 0:
            self.update_surface()
        return destroyed_count

    def check_solid_at_world(self, wx, wy):
        r, c = self.world_to_grid(wx, wy)
        if 0 <= r < self.grid_h and 0 <= c < self.grid_w:
            return self.grid[r, c] > 0
        return False

    def is_past_rear_face(self, wx, wy):
        rad = math.radians(self.angle_deg)
        cos_a, sin_a = math.cos(rad), math.sin(rad)
        cx_idx = self.grid_w * 0.20
        cy_idx = self.grid_h * 0.5
        dx = (wx - self.cx)
        dy = (wy - self.cy)
        dist_norm = dx * cos_a + dy * sin_a
        return dist_norm > (self.plate_thick_px + 2.0)

    def has_remaining_armor_ahead(self, wx, wy, dir_x, dir_y, max_dist_px=80.0):
        # Raymarch along trajectory to verify NO solid armor blocks remain ahead
        dist = 2.0
        while dist <= max_dist_px:
            tx = wx + dir_x * dist
            ty = wy + dir_y * dist
            if self.check_solid_at_world(tx, ty):
                return True
            dist += self.cell_size
        return False

    def check_era_hit(self, hit_x, hit_y):
        for era in self.era_blocks:
            if era["active"]:
                d = math.hypot(era["x"] - hit_x, era["y"] - hit_y)
                if d <= (era["h"] * 0.55):
                    era["active"] = False
                    return era
        return None

    def draw(self, screen):
        cx_idx = self.grid_w * 0.20
        cy_idx = self.grid_h * 0.5
        top_left_x = self.cx - cx_idx * self.cell_size
        top_left_y = self.cy - cy_idx * self.cell_size
        screen.blit(self.surface, (top_left_x, top_left_y))

        for era in self.era_blocks:
            if era["active"]:
                rad = math.radians(era["angle"])
                cos_a, sin_a = math.cos(rad), math.sin(rad)
                tx, ty = -sin_a, cos_a
                nx, ny = cos_a, sin_a
                hw, hh = era["w"] * 0.5, era["h"] * 0.5

                pts = [
                    (era["x"] + tx * hh - nx * hw, era["y"] + ty * hh - ny * hw),
                    (era["x"] - tx * hh - nx * hw, era["y"] - ty * hh - ny * hw),
                    (era["x"] - tx * hh + nx * hw, era["y"] - ty * hh + ny * hw),
                    (era["x"] + tx * hh + nx * hw, era["y"] + ty * hh + ny * hw),
                ]
                pygame.draw.polygon(screen, era["color"], pts)
                pygame.draw.polygon(screen, (230, 240, 255), pts, 1)

# --- Physical Spall Particle Data Wrapper ---
class PhysicalSpallData:
    def __init__(self, color, damage, energy=100.0, max_life=75):
        self.color = color
        self.damage = damage
        self.energy = energy
        self.initial_energy = energy
        self.life = max_life
        self.max_life = max_life
        self.hit_modules = set()

# --- Main Simulator Engine with Pymunk Physics Spalling ---
class FullAdvancedBallisticsApp:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("2D Terminal Ballistics Simulator: Pymunk Physical Spall")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("DejaVu Sans, Arial, Helvetica", 13)
        self.font_bold = pygame.font.SysFont("DejaVu Sans, Arial, Helvetica", 13, bold=True)
        self.font_large = pygame.font.SysFont("DejaVu Sans, Arial, Helvetica", 19, bold=True)
        self.font_small = pygame.font.SysFont("DejaVu Sans, Arial, Helvetica", 11)
        self.font_title = pygame.font.SysFont("DejaVu Sans, Arial, Helvetica", 15, bold=True)

        # World Area
        self.world_rect = pygame.Rect(340, 20, 980, 800)

        # Plate Position & Parameters
        self.plate_offset_x = 0.0
        self.plate_offset_y = 0.0
        self.armor_thickness = 220.0
        self.armor_angle = 30.0
        self.selected_era = "KONTAKT_5"
        self.crew_size_radius = 26.0
        self.spall_density_count = 60 # User adjustable 10 to 200
        self.time_scale = 0.6
        self.paused = False

        # Selection & Dragging state
        self.dragging_plate = False
        self.drag_start_mouse = (0, 0)
        self.drag_start_offset = (0, 0)
        self.dragged_crew_idx = None
        self.selected_crew_idx = None

        # Setup Pymunk Physics Space for Interior Fighting Compartment
        self.space = pymunk.Space()
        self.space.gravity = (0, 350)
        self.space.damping = 0.995

        # Sliders
        self.sliders = [
            Slider(35, 120, 270, 10, 10, 1000, self.armor_thickness, "Armor Thickness", " mm"),
            Slider(35, 160, 270, 10, -75, 75, self.armor_angle, "Armor Angle (Obliquity)", "°"),
            Slider(35, 200, 270, 10, -160, 200, self.plate_offset_x, "Plate Offset X", " px"),
            Slider(35, 240, 270, 10, -150, 150, self.plate_offset_y, "Plate Offset Y", " px"),
            Slider(35, 280, 270, 10, 12, 60, self.crew_size_radius, "Crew Size Scale", " px"),
            Slider(35, 320, 270, 10, 10, 200, self.spall_density_count, "Spall Density", " pts"),
            Slider(35, 360, 270, 10, 500, 2500, SHELL_PRESETS["APFSDS"]["base_vel"], "Muzzle Velocity", " m/s"),
            Slider(35, 400, 270, 10, 0.4, 2.5, 1.0, "RHA Hardness Factor", "x"),
            Slider(35, 440, 270, 10, 0.05, 1.0, self.time_scale, "Slow-Motion Speed", "x"),
        ]

        # Ammunition Buttons
        self.selected_shell = "APFSDS"
        self.shell_buttons = []
        btn_w, btn_h = 62, 24
        for i, key in enumerate(SHELL_PRESETS.keys()):
            self.shell_buttons.append(Button(35 + i * (btn_w + 6), 65, btn_w, btn_h, key, key))

        # ERA Buttons
        self.era_buttons = []
        era_keys = list(ERA_TYPES.keys())
        for i, key in enumerate(era_keys):
            eb_w = 130
            eb_h = 24
            bx = 35 + (i % 2) * (eb_w + 10)
            by = 475 + (i // 2) * (eb_h + 5)
            short_name = key.replace("_", " ").title()
            if key == "NONE": short_name = "No ERA"
            elif key == "KONTAKT_5": short_name = "Контакт-5"
            elif key == "RELIKT": short_name = "Реликт"
            elif key == "DUPLET": short_name = "Дуплет"
            self.era_buttons.append(Button(bx, by, eb_w, eb_h, short_name, key))

        # Crew Management Buttons
        self.btn_add_crew = Button(35, 535, 85, 26, "+ Add Crew", "ADD_CREW")
        self.btn_del_crew = Button(126, 535, 85, 26, "Delete Crew", "DEL_CREW")
        self.btn_reset_sim = Button(217, 535, 88, 26, "Reset [R]", "RESET")

        # Ballistics & Matrix
        self.armor = None
        self.rebuild_matrix()

        self.active_shell = None
        self.cumulative_jet = []
        self.entrance_sparks = []
        
        # Pymunk Physical Spall Particles: [(body, shape, data)]
        self.physical_spall_bodies = []
        self.destroyed_voxel_count = 0
        self.last_impact_info = {"status": "READY", "color": COLOR_TEXT_DIM, "v_loss": 0, "pen_mm": 0}

        # Customizable Crew & Modules
        self.base_module_pos = (self.world_rect.x + 670, self.world_rect.y + 400)
        self.crew_members = [
            {"name": "Commander", "pos": [self.base_module_pos[0] + 10, self.base_module_pos[1] - 70], "base_r": 26, "hp": 100, "col": (52, 152, 219), "body": None, "shape": None},
            {"name": "Gunner", "pos": [self.base_module_pos[0] + 10, self.base_module_pos[1] + 70], "base_r": 26, "hp": 100, "col": (46, 204, 113), "body": None, "shape": None},
            {"name": "Driver", "pos": [self.base_module_pos[0] - 120, self.base_module_pos[1]], "base_r": 26, "hp": 100, "col": (155, 89, 182), "body": None, "shape": None},
            {"name": "Ammo Rack", "pos": [self.base_module_pos[0] + 100, self.base_module_pos[1] - 50], "base_r": 34, "hp": 100, "col": (231, 76, 60), "body": None, "shape": None},
            {"name": "Engine Block", "pos": [self.base_module_pos[0] + 210, self.base_module_pos[1]], "base_r": 50, "hp": 100, "col": (241, 196, 15), "body": None, "shape": None},
        ]
        self.custom_crew_counter = 1

        self.aim_y = float(self.world_rect.y + 400)
        self.aim_angle = 0.0

        self.setup_pymunk_environment()

    def get_plate_world_pos(self):
        return (
            self.world_rect.x + 360 + self.plate_offset_x,
            self.world_rect.y + 400 + self.plate_offset_y
        )

    def rebuild_matrix(self):
        cx, cy = self.get_plate_world_pos()
        self.armor = HighResArmorMatrix(
            cx, cy,
            self.armor_thickness, self.armor_angle,
            self.sliders[7].value,
            self.selected_era
        )

    def setup_pymunk_environment(self):
        # Clear existing
        for b, s, d in self.physical_spall_bodies:
            if s in self.space.shapes: self.space.remove(s)
            if b in self.space.bodies: self.space.remove(b)
        self.physical_spall_bodies.clear()

        for s in list(self.space.shapes):
            self.space.remove(s)
        for b in list(self.space.bodies):
            self.space.remove(b)

        # Hull Walls
        hull_pts = [
            (self.base_module_pos[0] - 170, self.base_module_pos[1] - 230),
            (self.base_module_pos[0] + 280, self.base_module_pos[1] - 230),
            (self.base_module_pos[0] + 310, self.base_module_pos[1] + 230),
            (self.base_module_pos[0] - 170, self.base_module_pos[1] + 230)
        ]
        for i in range(len(hull_pts) - 1):
            wb = pymunk.Body(body_type=pymunk.Body.STATIC)
            ws = pymunk.Segment(wb, hull_pts[i], hull_pts[i + 1], 4)
            ws.friction = 0.6
            ws.elasticity = 0.4
            ws.collision_type = COLLTYPE_WALL
            self.space.add(wb, ws)

        # Create Pymunk Static Bodies for Crew / Modules (is_sensor=True to prevent bouncing)
        for m in self.crew_members:
            eff_r = self.get_effective_radius(m)
            mb = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
            mb.position = m["pos"][0], m["pos"][1]
            ms = pymunk.Circle(mb, eff_r)
            ms.sensor = True
            ms.collision_type = COLLTYPE_CREW
            ms.custom_data = m
            ms.friction = 0.0
            ms.elasticity = 0.0
            self.space.add(mb, ms)
            m["body"] = mb
            m["shape"] = ms

    def reset_sim(self):
        self.rebuild_matrix()
        self.active_shell = None
        
        for b, s, d in self.physical_spall_bodies:
            if s in self.space.shapes: self.space.remove(s)
            if b in self.space.bodies: self.space.remove(b)
        self.physical_spall_bodies.clear()

        self.cumulative_jet.clear()
        self.entrance_sparks.clear()
        self.destroyed_voxel_count = 0
        for m in self.crew_members:
            m["hp"] = 100
        self.last_impact_info = {"status": "READY", "color": COLOR_TEXT_DIM, "v_loss": 0, "pen_mm": 0}
        self.setup_pymunk_environment()

    def add_custom_crew(self):
        names = ["Loader", "Radio Op", "Driver 2", f"Crew #{self.custom_crew_counter}"]
        name = names[min(len(names) - 1, self.custom_crew_counter - 1)]
        self.custom_crew_counter += 1

        spawn_x = self.base_module_pos[0] + random.randint(-40, 60)
        spawn_y = self.base_module_pos[1] + random.randint(-40, 40)

        new_crew = {
            "name": name,
            "pos": [spawn_x, spawn_y],
            "base_r": 25,
            "hp": 100,
            "col": (random.randint(80, 200), random.randint(120, 220), 255),
            "body": None,
            "shape": None
        }
        self.crew_members.append(new_crew)
        self.selected_crew_idx = len(self.crew_members) - 1
        self.setup_pymunk_environment()

    def delete_selected_crew(self):
        if self.selected_crew_idx is not None and 0 <= self.selected_crew_idx < len(self.crew_members):
            target = self.crew_members.pop(self.selected_crew_idx)
            if target.get("shape") and target["shape"] in self.space.shapes:
                self.space.remove(target["shape"])
            if target.get("body") and target["body"] in self.space.bodies:
                self.space.remove(target["body"])
            self.selected_crew_idx = None
        elif len(self.crew_members) > 0:
            target = self.crew_members.pop()
            if target.get("shape") and target["shape"] in self.space.shapes:
                self.space.remove(target["shape"])
            if target.get("body") and target["body"] in self.space.bodies:
                self.space.remove(target["body"])
            self.selected_crew_idx = None

    def get_effective_radius(self, member):
        scale = self.crew_size_radius / 26.0
        return max(8, int(member.get("base_r", 26) * scale))

    def fire_projectile(self):
        st = SHELL_PRESETS[self.selected_shell]
        vel_mps = self.sliders[6].value
        rad = math.radians(self.aim_angle)

        gun_x = self.world_rect.x + 40
        gun_y = self.aim_y

        sim_speed = vel_mps * 0.045
        self.active_shell = {
            "x": float(gun_x),
            "y": float(gun_y),
            "vx": math.cos(rad) * sim_speed,
            "vy": math.sin(rad) * sim_speed,
            "speed_mps": vel_mps,
            "initial_speed": vel_mps,
            "angle_deg": self.aim_angle,
            "key": self.selected_shell,
            "radius": st["width"] * 0.5,
            "length": st["length"],
            "trail": []
        }
        self.last_impact_info = {"status": "IN FLIGHT", "color": st["color"], "v_loss": 0, "pen_mm": 0}

    def spawn_front_entrance_sparks(self, x, y, dir_x, dir_y, count=6):
        base_ang = math.atan2(dir_y, dir_x)
        for _ in range(min(12, count)):
            ang = base_ang + random.gauss(0, 0.45)
            spd = random.uniform(3, 12)
            self.entrance_sparks.append({
                "x": float(x),
                "y": float(y),
                "vx": math.cos(ang) * spd,
                "vy": math.sin(ang) * spd,
                "color": (255, random.randint(160, 240), 40),
                "size": random.randint(2, 3),
                "life": random.randint(15, 30)
            })
        if len(self.entrance_sparks) > 30:
            self.entrance_sparks = self.entrance_sparks[-30:]

    def spawn_pymunk_physical_spall(self, start_x, start_y, dir_x, dir_y, rem_speed_mps):
        # STRICT REQUIREMENT: ONLY SPAWNS ON FULL PENETRATION BEHIND ARMOR
        total_spall_count = int(self.spall_density_count)
        base_ang = math.atan2(dir_y, dir_x)

        # Clear old spall if exceeding buffer
        if len(self.physical_spall_bodies) > 150:
            for b, s, d in self.physical_spall_bodies[:80]:
                if s in self.space.shapes: self.space.remove(s)
                if b in self.space.bodies: self.space.remove(b)
            self.physical_spall_bodies = self.physical_spall_bodies[80:]

        for i in range(total_spall_count):
            ang = base_ang + random.gauss(0, 0.28)
            spd = random.uniform(120, 680) * (rem_speed_mps / 1200.0)
            
            p_mass = random.uniform(0.1, 0.4)
            p_radius = random.uniform(2.0, 4.2)
            p_moment = pymunk.moment_for_circle(p_mass, 0, p_radius)

            body = pymunk.Body(p_mass, p_moment)
            body.position = start_x + math.cos(ang) * 5.0, start_y + math.sin(ang) * 5.0
            body.velocity = pymunk.Vec2d(math.cos(ang) * spd, math.sin(ang) * spd)

            shape = pymunk.Circle(body, p_radius)
            shape.friction = 0.5
            shape.elasticity = 0.45
            shape.collision_type = COLLTYPE_SPALL

            is_tungsten = (i % 3 == 0 and self.selected_shell == "APFSDS")
            p_color = COLOR_TUNGSTEN if is_tungsten else (255, random.randint(110, 230), 40)
            initial_energy = random.uniform(70.0, 140.0) if is_tungsten else random.uniform(40.0, 95.0)
            initial_energy *= (rem_speed_mps / 1000.0)
            p_data = PhysicalSpallData(p_color, damage=random.randint(15, 45), energy=initial_energy, max_life=random.randint(50, 100))
            shape.custom_data = p_data

            self.space.add(body, shape)
            self.physical_spall_bodies.append((body, shape, p_data))

    def trigger_era_detonation(self, era_block, dir_x, dir_y):
        rad_norm = math.radians(self.armor_angle + 180)
        for _ in range(25):
            ang = rad_norm + random.uniform(-0.8, 0.8)
            spd = random.uniform(8, 24)
            self.entrance_sparks.append({
                "x": float(era_block["x"]),
                "y": float(era_block["y"]),
                "vx": math.cos(ang) * spd,
                "vy": math.sin(ang) * spd,
                "color": (255, random.randint(190, 255), 50),
                "size": random.randint(2, 4),
                "life": random.randint(15, 35)
            })

    def trigger_heat_detonation(self, hit_x, hit_y, dir_x, dir_y, era_hit_type=None):
        heat_reduction = 0.0
        if era_hit_type and era_hit_type != "NONE":
            heat_reduction = ERA_TYPES[era_hit_type]["heat_reduction"]

        jet_count = int(35 * (1.0 - heat_reduction))
        jet_speed_base = 32.0 * (1.0 - heat_reduction * 0.6)
        jet_energy = 110.0 * (1.0 - heat_reduction)

        for i in range(max(3, jet_count)):
            spread = random.gauss(0, 0.03 + heat_reduction * 0.12)
            ang = math.atan2(dir_y, dir_x) + spread
            spd = jet_speed_base * (1.0 - (i / max(1, jet_count)) * 0.4) + random.uniform(-1, 1)

            self.cumulative_jet.append({
                "x": float(hit_x),
                "y": float(hit_y),
                "vx": math.cos(ang) * spd,
                "vy": math.sin(ang) * spd,
                "energy": jet_energy,
                "life": 45,
                "color": COLOR_COPPER if i % 2 == 0 else (255, 240, 180)
            })

        for _ in range(20):
            ang = random.uniform(0, math.tau)
            spd = random.uniform(2, 10)
            self.entrance_sparks.append({
                "x": float(hit_x),
                "y": float(hit_y),
                "vx": math.cos(ang) * spd,
                "vy": math.sin(ang) * spd,
                "color": (255, random.randint(80, 180), 20),
                "size": random.randint(2, 4),
                "life": random.randint(15, 30)
            })

    def remove_dead_spall_callback(self, space, shape):
        if shape in space.shapes:
            space.remove(shape)
        if shape.body in space.bodies:
            space.remove(shape.body)

    def update_physics(self):
        st = SHELL_PRESETS[self.selected_shell]
        dt_scale = self.time_scale

        # 1. Update Shell Ballistics
        if self.active_shell:
            sh = self.active_shell
            sh["trail"].append((sh["x"], sh["y"]))
            if len(sh["trail"]) > 30:
                sh["trail"].pop(0)

            substeps = 8
            step_vx = (sh["vx"] * dt_scale) / substeps
            step_vy = (sh["vy"] * dt_scale) / substeps

            for _ in range(substeps):
                sh["x"] += step_vx
                sh["y"] += step_vy

                # ERA check
                if self.selected_era != "NONE" and not sh.get("era_checked", False):
                    era_hit = self.armor.check_era_hit(sh["x"], sh["y"])
                    if era_hit:
                        sh["era_checked"] = True
                        era_cfg = ERA_TYPES[era_hit["type"]]
                        self.trigger_era_detonation(era_hit, sh["vx"], sh["vy"])

                        if st["is_heat"]:
                            self.trigger_heat_detonation(sh["x"], sh["y"], sh["vx"], sh["vy"], era_hit_type=era_hit["type"])
                            self.last_impact_info = {"status": f"ERA DEFEAT ({era_hit['type']})", "color": COLOR_GREEN, "v_loss": int(sh["initial_speed"]), "pen_mm": 40}
                            self.active_shell = None
                            break
                        else:
                            kin_loss = era_cfg["kin_reduction"]
                            sh["speed_mps"] *= (1.0 - kin_loss)
                            sh["vx"] *= (1.0 - kin_loss)
                            sh["vy"] *= (1.0 - kin_loss)

                # Armor impact check
                if self.armor.check_solid_at_world(sh["x"], sh["y"]):
                    impact_angle = abs(self.armor_angle - sh["angle_deg"])

                    # Ricochet check
                    if not sh.get("penetrating", False) and impact_angle >= st["ricochet_angle"]:
                        sh["vy"] = -abs(sh["vy"]) * 0.8
                        sh["vx"] *= 0.6
                        sh["speed_mps"] *= 0.5
                        self.spawn_front_entrance_sparks(sh["x"], sh["y"], -sh["vx"], -sh["vy"], count=12)
                        self.last_impact_info = {"status": "RICOCHET", "color": COLOR_YELLOW, "v_loss": int(sh["initial_speed"] - sh["speed_mps"]), "pen_mm": 0}
                        break

                    # HEAT Detonation
                    if st["is_heat"]:
                        self.trigger_heat_detonation(sh["x"], sh["y"], sh["vx"], sh["vy"], era_hit_type=None)
                        self.last_impact_info = {"status": "HEAT JET ACTIVE", "color": COLOR_ORANGE, "v_loss": int(sh["initial_speed"]), "pen_mm": int(self.armor_thickness)}
                        self.active_shell = None
                        break

                    sh["penetrating"] = True
                    crater_radius = max(3.5, sh["radius"] * 1.1)

                    destroyed = self.armor.excavate_crater(sh["x"], sh["y"], crater_radius, damage=100.0)
                    self.destroyed_voxel_count += destroyed

                    rha_factor = self.sliders[7].value
                    pen_power = st["pen_power"]
                    speed_loss_step = (destroyed * 2.3 * rha_factor) / pen_power
                    sh["speed_mps"] = max(0.0, sh["speed_mps"] - speed_loss_step)

                    cur_speed = math.hypot(sh["vx"], sh["vy"])
                    if cur_speed > 0:
                        dir_x, dir_y = sh["vx"] / cur_speed, sh["vy"] / cur_speed
                        new_sim_speed = (sh["speed_mps"] * 0.045)
                        sh["vx"] = dir_x * new_sim_speed
                        sh["vy"] = dir_y * new_sim_speed

                    if random.random() < 0.25:
                        self.spawn_front_entrance_sparks(sh["x"], sh["y"], -sh["vx"], -sh["vy"], count=2)

                    # STRICT NON-PENETRATION: Stopped inside armor -> ZERO BEHIND-ARMOR SPALL
                    if sh["speed_mps"] <= 75.0:
                        self.last_impact_info = {
                            "status": "NON-PENETRATION (STOPPED IN ARMOR)",
                            "color": COLOR_RED,
                            "v_loss": int(sh["initial_speed"]),
                            "pen_mm": int(min(self.armor_thickness, (1.0 - sh["speed_mps"]/sh["initial_speed"]) * self.armor_thickness * 0.85))
                        }
                        self.active_shell = None
                        break

            # STRICT FULL PENETRATION: Only when past rear face AND no armor blocks ahead
            if self.active_shell and sh.get("penetrating", False):
                cur_speed = math.hypot(sh["vx"], sh["vy"])
                dir_x = sh["vx"] / max(0.001, cur_speed)
                dir_y = sh["vy"] / max(0.001, cur_speed)
                if self.armor.is_past_rear_face(sh["x"], sh["y"]) and not self.armor.has_remaining_armor_ahead(sh["x"], sh["y"], dir_x, dir_y):
                    v_loss = int(sh["initial_speed"] - sh["speed_mps"])
                    self.last_impact_info = {"status": "FULL PENETRATION (SPALL CONE)", "color": COLOR_GREEN, "v_loss": v_loss, "pen_mm": int(self.armor_thickness)}
                    # Spawn Pymunk Physical Spall Particles
                    self.spawn_pymunk_physical_spall(sh["x"], sh["y"], sh["vx"], sh["vy"], sh["speed_mps"])
                    self.active_shell = None

        # 2. Step Pymunk Space for Physical Spall & Debris
        substeps_pymunk = 4
        dt_pymunk = (1.0 / FPS) * dt_scale / substeps_pymunk
        for _ in range(substeps_pymunk):
            self.space.step(dt_pymunk)

        # Update Crew Bodies to match dragged position
        for m in self.crew_members:
            if m.get("body"):
                m["body"].position = m["pos"][0], m["pos"][1]

        # 3. Step & Process Physical Spall Particles (Volumetric Overpenetration & Drag)
        rem_spall = []
        for b, s, d in self.physical_spall_bodies:
            d.life -= 1
            px, py = b.position.x, b.position.y

            # Check penetration through crew circles
            for m in self.crew_members:
                eff_r = self.get_effective_radius(m)
                dist = math.hypot(px - m["pos"][0], py - m["pos"][1])
                if dist <= eff_r:
                    # Inside crew body: apply continuous tissue drag (20-40% speed loss per penetration)
                    crew_id = id(m)
                    if crew_id not in d.hit_modules:
                        d.hit_modules.add(crew_id)
                        # Damage based on current speed & energy
                        cur_spd = b.velocity.length
                        dmg = int(random.uniform(10, 25) * (cur_spd / 450.0) * (d.energy / max(1.0, d.initial_energy)))
                        dmg = max(4, min(40, dmg))
                        m["hp"] = max(0, m["hp"] - dmg)

                        # Speed reduction (20% - 40% loss)
                        retention = random.uniform(0.60, 0.80)
                        deflect = random.uniform(-0.10, 0.10)
                        cos_d, sin_d = math.cos(deflect), math.sin(deflect)
                        vx = b.velocity.x * retention
                        vy = b.velocity.y * retention
                        b.velocity = pymunk.Vec2d(vx * cos_d - vy * sin_d, vx * sin_d + vy * cos_d)
                        d.energy *= retention
                    else:
                        # Minor viscous drag while traveling inside the same module
                        b.velocity = pymunk.Vec2d(b.velocity.x * 0.96, b.velocity.y * 0.96)

            cur_v = b.velocity.length
            # Expire if out of bounds, life ended, or lost all energy/velocity
            if d.life > 0 and cur_v > 8.0 and d.energy > 1.0 and self.world_rect.collidepoint((px, py)):
                rem_spall.append((b, s, d))
            else:
                self.space.add_post_step_callback(self.remove_dead_spall_callback, s)
        self.physical_spall_bodies = rem_spall

        # 4. Update Cumulative Jet
        rem_jet = []
        for jp in self.cumulative_jet:
            jp["x"] += jp["vx"] * dt_scale
            jp["y"] += jp["vy"] * dt_scale
            jp["life"] -= 1

            if self.armor.check_solid_at_world(jp["x"], jp["y"]):
                destroyed = self.armor.excavate_crater(jp["x"], jp["y"], radius_px=2.5, damage=100.0)
                self.destroyed_voxel_count += destroyed
                jp["energy"] -= (destroyed * 1.2 * self.sliders[7].value)
                if jp["energy"] <= 0:
                    continue

            # Check if cumulative jet actually penetrated rear armor
            cur_j_spd = math.hypot(jp["vx"], jp["vy"])
            j_dir_x = jp["vx"] / max(0.001, cur_j_spd)
            j_dir_y = jp["vy"] / max(0.001, cur_j_spd)
            if self.armor.is_past_rear_face(jp["x"], jp["y"]) and not self.armor.has_remaining_armor_ahead(jp["x"], jp["y"], j_dir_x, j_dir_y):
                for m in self.crew_members:
                    eff_r = self.get_effective_radius(m)
                    dist = math.hypot(jp["x"] - m["pos"][0], jp["y"] - m["pos"][1])
                    if dist <= eff_r:
                        m["hp"] = max(0, m["hp"] - 2)

            if jp["life"] > 0 and self.world_rect.collidepoint((jp["x"], jp["y"])):
                rem_jet.append(jp)
        self.cumulative_jet = rem_jet

        # 5. Update Entrance Sparks
        rem_sparks = []
        for s in self.entrance_sparks:
            s["x"] += s["vx"] * dt_scale
            s["y"] += s["vy"] * dt_scale
            s["vy"] += 0.15 * dt_scale
            s["life"] -= 1
            if s["life"] > 0 and self.world_rect.collidepoint((s["x"], s["y"])):
                rem_sparks.append(s)
        self.entrance_sparks = rem_sparks

    def run(self):
        running = True
        while running:
            self.clock.tick(FPS)
            mouse_pos = pygame.mouse.get_pos()
            mouse_pressed = pygame.mouse.get_pressed()

            # Responsive Event Handler
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        self.fire_projectile()
                    elif event.key == pygame.K_r:
                        self.reset_sim()
                    elif event.key == pygame.K_p:
                        self.paused = not self.paused
                    elif event.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
                        self.delete_selected_crew()

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        for btn in self.shell_buttons:
                            if btn.is_hovered(event.pos):
                                self.selected_shell = btn.key
                                self.sliders[6].value = SHELL_PRESETS[self.selected_shell]["base_vel"]

                        for btn in self.era_buttons:
                            if btn.is_hovered(event.pos):
                                self.selected_era = btn.key
                                self.rebuild_matrix()

                        if self.btn_add_crew.is_hovered(event.pos):
                            self.add_custom_crew()

                        if self.btn_del_crew.is_hovered(event.pos):
                            self.delete_selected_crew()

                        if self.btn_reset_sim.is_hovered(event.pos):
                            self.reset_sim()

                        clicked_crew = False
                        for i, m in enumerate(self.crew_members):
                            eff_r = self.get_effective_radius(m)
                            d = math.hypot(event.pos[0] - m["pos"][0], event.pos[1] - m["pos"][1])
                            if d <= eff_r:
                                self.dragged_crew_idx = i
                                self.selected_crew_idx = i
                                clicked_crew = True
                                break

                        if not clicked_crew and self.world_rect.collidepoint(event.pos) and event.pos[0] > self.world_rect.x + 220:
                            self.selected_crew_idx = None

                        if self.world_rect.collidepoint(event.pos) and event.pos[0] < self.world_rect.x + 160:
                            self.aim_y = float(event.pos[1])
                            self.fire_projectile()

                    elif event.button == 3:
                        right_clicked_crew = False
                        for i, m in enumerate(self.crew_members):
                            eff_r = self.get_effective_radius(m)
                            d = math.hypot(event.pos[0] - m["pos"][0], event.pos[1] - m["pos"][1])
                            if d <= eff_r:
                                target = self.crew_members.pop(i)
                                if target.get("shape") and target["shape"] in self.space.shapes:
                                    self.space.remove(target["shape"])
                                if target.get("body") and target["body"] in self.space.bodies:
                                    self.space.remove(target["body"])
                                self.selected_crew_idx = None
                                right_clicked_crew = True
                                break

                        if not right_clicked_crew and self.world_rect.collidepoint(event.pos):
                            self.dragging_plate = True
                            self.drag_start_mouse = event.pos
                            self.drag_start_offset = (self.plate_offset_x, self.plate_offset_y)

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.dragged_crew_idx = None
                    elif event.button == 3:
                        self.dragging_plate = False

                elif event.type == pygame.MOUSEMOTION:
                    if self.dragging_plate:
                        dx = event.pos[0] - self.drag_start_mouse[0]
                        dy = event.pos[1] - self.drag_start_mouse[1]
                        self.plate_offset_x = max(-160.0, min(200.0, self.drag_start_offset[0] + dx))
                        self.plate_offset_y = max(-150.0, min(150.0, self.drag_start_offset[1] + dy))
                        self.sliders[2].value = self.plate_offset_x
                        self.sliders[3].value = self.plate_offset_y
                        self.rebuild_matrix()

                    if self.dragged_crew_idx is not None and 0 <= self.dragged_crew_idx < len(self.crew_members):
                        self.crew_members[self.dragged_crew_idx]["pos"][0] = event.pos[0]
                        self.crew_members[self.dragged_crew_idx]["pos"][1] = event.pos[1]

                # Sliders
                rebuild = False
                for s in self.sliders:
                    if s.handle_event(event):
                        if s == self.sliders[0]:
                            self.armor_thickness = s.value
                            rebuild = True
                        elif s == self.sliders[1]:
                            self.armor_angle = s.value
                            rebuild = True
                        elif s == self.sliders[2]:
                            self.plate_offset_x = s.value
                            rebuild = True
                        elif s == self.sliders[3]:
                            self.plate_offset_y = s.value
                            rebuild = True
                        elif s == self.sliders[4]:
                            self.crew_size_radius = s.value
                            self.setup_pymunk_environment()
                        elif s == self.sliders[5]:
                            self.spall_density_count = int(s.value)
                        elif s == self.sliders[7]:
                            rebuild = True
                        elif s == self.sliders[8]:
                            self.time_scale = s.value

                if rebuild:
                    self.rebuild_matrix()

            if mouse_pressed[0] and self.world_rect.collidepoint(mouse_pos) and mouse_pos[0] < self.world_rect.x + 160:
                self.aim_y = float(mouse_pos[1])
                cx, cy = self.get_plate_world_pos()
                dx = (cx - 20) - (self.world_rect.x + 40)
                dy = mouse_pos[1] - cy
                self.aim_angle = math.degrees(math.atan2(dy, dx)) * 0.25

            if not self.paused:
                self.update_physics()

            # --- Rendering ---
            self.screen.fill(COLOR_BG)

            panel_rect = pygame.Rect(20, 20, 300, 800)
            pygame.draw.rect(self.screen, COLOR_PANEL, panel_rect, border_radius=8)
            pygame.draw.rect(self.screen, COLOR_PANEL_BORDER, panel_rect, width=1, border_radius=8)

            self.screen.blit(self.font_title.render("BALLISTICS & DEFENSE CONTROL", True, COLOR_TEXT), (35, 24))
            self.screen.blit(self.font_small.render("Pymunk Rigid-Body Spalling Engine", True, COLOR_TEXT_DIM), (35, 42))

            self.screen.blit(self.font_small.render("AMMUNITION TYPE:", True, COLOR_TEXT_DIM), (35, 52))
            for btn in self.shell_buttons:
                btn.draw(self.screen, self.font_bold, active=(btn.key == self.selected_shell))

            st = SHELL_PRESETS[self.selected_shell]
            desc = self.font_small.render(st["desc"], True, st["color"])
            self.screen.blit(desc, (35, 94))

            for s in self.sliders:
                s.draw(self.screen, self.font_bold, self.font_small)

            self.screen.blit(self.font_small.render("EXPLOSIVE REACTIVE ARMOR (ДЗ):", True, COLOR_TEXT_DIM), (35, 458))
            for btn in self.era_buttons:
                btn.draw(self.screen, self.font_bold, active=(btn.key == self.selected_era), custom_bg=ERA_TYPES[btn.key]["color"])

            self.btn_add_crew.draw(self.screen, self.font_bold)
            self.btn_del_crew.draw(self.screen, self.font_bold)
            self.btn_reset_sim.draw(self.screen, self.font_bold)

            hints = self.font_bold.render("[RMB/Del] Remove  [LMB Drag] Move", True, COLOR_ACCENT)
            self.screen.blit(hints, (35, 570))

            status_box = pygame.Rect(35, 595, 270, 70)
            pygame.draw.rect(self.screen, (16, 19, 25), status_box, border_radius=6)
            pygame.draw.rect(self.screen, self.last_impact_info["color"], status_box, width=2, border_radius=6)

            st_txt = self.font_large.render(self.last_impact_info["status"], True, self.last_impact_info["color"])
            self.screen.blit(st_txt, (status_box.centerx - st_txt.get_width() // 2, status_box.y + 10))

            sub_st = self.font_small.render(f"Loss: {self.last_impact_info['v_loss']} m/s | Armor Pen: {self.last_impact_info['pen_mm']} mm", True, COLOR_TEXT_DIM)
            self.screen.blit(sub_st, (status_box.centerx - sub_st.get_width() // 2, status_box.y + 42))

            tele_box = pygame.Rect(35, 675, 270, 135)
            pygame.draw.rect(self.screen, (16, 19, 25), tele_box, border_radius=6)
            pygame.draw.rect(self.screen, COLOR_PANEL_BORDER, tele_box, width=1, border_radius=6)

            self.screen.blit(self.font_bold.render("TELEMETRY & COMBAT STATUS", True, COLOR_TEXT), (45, 685))

            cur_speed = int(self.active_shell["speed_mps"]) if self.active_shell else 0
            sel_crew_name = self.crew_members[self.selected_crew_idx]["name"] if (self.selected_crew_idx is not None and 0 <= self.selected_crew_idx < len(self.crew_members)) else "None"
            lines = [
                ("Current Shell Speed:", f"{cur_speed} m/s"),
                ("Selected Member:", f"{sel_crew_name}"),
                ("Crew Alive:", f"{sum(1 for c in self.crew_members if c['hp'] > 0)} / {len(self.crew_members)}"),
                ("Physical Spall Count:", f"{len(self.physical_spall_bodies)}"),
                ("Sim Speed Mode:", f"{self.time_scale:.2f}x {'(PAUSED)' if self.paused else ''}")
            ]
            for i, (k, v) in enumerate(lines):
                y_pos = 705 + i * 19
                self.screen.blit(self.font_small.render(k, True, COLOR_TEXT_DIM), (45, y_pos))
                tv = self.font_small.render(v, True, COLOR_TEXT)
                self.screen.blit(tv, (tele_box.right - tv.get_width() - 10, y_pos))

            # --- World Simulation View ---
            pygame.draw.rect(self.screen, (10, 12, 16), self.world_rect, border_radius=8)
            pygame.draw.rect(self.screen, COLOR_PANEL_BORDER, self.world_rect, width=1, border_radius=8)

            for gx in range(self.world_rect.x + 50, self.world_rect.right, 50):
                pygame.draw.line(self.screen, (18, 22, 28), (gx, self.world_rect.y), (gx, self.world_rect.bottom))
            for gy in range(self.world_rect.y + 50, self.world_rect.bottom, 50):
                pygame.draw.line(self.screen, (18, 22, 28), (self.world_rect.x, gy), (self.world_rect.right, gy))

            hull_poly = [
                (self.base_module_pos[0] - 170, self.base_module_pos[1] - 230),
                (self.base_module_pos[0] + 280, self.base_module_pos[1] - 230),
                (self.base_module_pos[0] + 310, self.base_module_pos[1] + 230),
                (self.base_module_pos[0] - 170, self.base_module_pos[1] + 230)
            ]
            pygame.draw.polygon(self.screen, (16, 20, 26), hull_poly)
            pygame.draw.polygon(self.screen, (34, 42, 54), hull_poly, 1)

            # Draw Crew Members & Modules
            for i, m in enumerate(self.crew_members):
                pos = (int(m["pos"][0]), int(m["pos"][1]))
                eff_r = self.get_effective_radius(m)
                hp_ratio = m["hp"] / 100.0
                mod_col = (
                    int(m["col"][0] * hp_ratio + 50 * (1 - hp_ratio)),
                    int(m["col"][1] * hp_ratio),
                    int(m["col"][2] * hp_ratio)
                )
                pygame.draw.circle(self.screen, (24, 28, 36), pos, eff_r)
                pygame.draw.circle(self.screen, mod_col, pos, max(2, int(eff_r * hp_ratio)))
                pygame.draw.circle(self.screen, m["col"], pos, eff_r, 2)

                if self.selected_crew_idx == i:
                    pygame.draw.circle(self.screen, (255, 255, 255), pos, eff_r + 4, 2)

                lbl = self.font_small.render(m["name"], True, COLOR_TEXT)
                hp_lbl = self.font_small.render(f"HP: {m['hp']}%", True, COLOR_GREEN if m["hp"] > 50 else COLOR_RED)
                self.screen.blit(lbl, (pos[0] - lbl.get_width() // 2, pos[1] - eff_r - 15))
                self.screen.blit(hp_lbl, (pos[0] - hp_lbl.get_width() // 2, pos[1] - 6))

            # Draw Armor & ERA
            self.armor.draw(self.screen)

            # Draw Pymunk Physical Spall Particles (Only exist after Full Penetration)
            for b, s, d in self.physical_spall_bodies:
                spall_pos = (int(b.position.x), int(b.position.y))
                pygame.draw.circle(self.screen, d.color, spall_pos, int(s.radius))

            # Draw Cumulative HEAT Jet
            for jp in self.cumulative_jet:
                pygame.draw.circle(self.screen, jp["color"], (int(jp["x"]), int(jp["y"])), 3)
                pygame.draw.circle(self.screen, (255, 255, 255), (int(jp["x"]), int(jp["y"])), 1)

            # Draw Front Entrance Sparks
            for s in self.entrance_sparks:
                pygame.draw.circle(self.screen, s["color"], (int(s["x"]), int(s["y"])), s["size"])

            # Gun & Aim Line
            gun_pos = (self.world_rect.x + 40, int(self.aim_y))
            cx, cy = self.get_plate_world_pos()
            pygame.draw.rect(self.screen, (50, 58, 70), (gun_pos[0] - 30, gun_pos[1] - 8, 35, 16), border_radius=2)
            pygame.draw.line(self.screen, (40, 50, 65), gun_pos, (cx, int(self.aim_y)), 1)

            # Draw Active Projectile & Trail
            if self.active_shell:
                sh = self.active_shell
                if len(sh["trail"]) > 1:
                    pygame.draw.lines(self.screen, st["color"], False, sh["trail"], 2)

                rad = math.radians(sh["angle_deg"])
                tip_x = sh["x"] + math.cos(rad) * (sh["length"] * 0.5)
                tip_y = sh["y"] + math.sin(rad) * (sh["length"] * 0.5)
                tail_x = sh["x"] - math.cos(rad) * (sh["length"] * 0.5)
                tail_y = sh["y"] - math.sin(rad) * (sh["length"] * 0.5)
                pygame.draw.line(self.screen, st["color"], (tail_x, tail_y), (tip_x, tip_y), int(sh["radius"] * 2))
                pygame.draw.circle(self.screen, (255, 255, 255), (int(tip_x), int(tip_y)), int(sh["radius"]))

            # Top HUD
            hud_txt = self.font_bold.render(f"SIMULATOR: {st['name']} | ERA: {ERA_TYPES[self.selected_era]['name']}", True, COLOR_TEXT)
            self.screen.blit(hud_txt, (self.world_rect.x + 20, self.world_rect.y + 15))
            sub_hud = self.font_small.render("Pymunk Rigid-Body Spall Particles • Zero Internal Spall on Non-Pen • Spall Density Slider", True, COLOR_TEXT_DIM)
            self.screen.blit(sub_hud, (self.world_rect.x + 20, self.world_rect.y + 36))

            pygame.display.flip()

        pygame.quit()
        sys.exit(0)

if __name__ == "__main__":
    app = FullAdvancedBallisticsApp()
    app.run()
