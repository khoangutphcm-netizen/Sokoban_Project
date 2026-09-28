import argparse
import sys
from pathlib import Path
import pygame
from core.map_loader import load_map
from core.state import get_successors
from search.astar import a_star_search
from search.ucs import uniform_cost_search

# Kích hoạt chế độ nét cao (High-DPI) trên Windows
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent
ALGORITHMS = {"UCS": uniform_cost_search, "A*": a_star_search}

COLORS = {
    "background": (20, 26, 30),
    "background_alt": (28, 37, 42),
    "panel": (244, 242, 232),
    "floor": (220, 211, 184),
    "floor_line": (203, 192, 163),
    "wall": (59, 75, 70),
    "wall_edge": (42, 55, 52),
    "goal": (212, 91, 73),
    "box": (194, 132, 62),
    "box_edge": (112, 70, 35),
    "agent": (49, 133, 174),
    "agent2": (198, 91, 103),
    "text": (37, 46, 43),
    "muted": (116, 126, 120),
    "accent": (135, 204, 147),
    "accent_dark": (56, 115, 78),
    "button": (230, 231, 220),
    "white": (250, 250, 244),
    "line": (77, 94, 91),
}

def lerp(start: float, end: float, t: float) -> float:
    return start + (end - start) * t

class SokobanGame:
    def __init__(self, map_path: Path):
        pygame.init()
        pygame.display.set_caption("Sokoban - 120 FPS High Quality")
        
        self.screen = pygame.display.set_mode((1160, 800), pygame.RESIZABLE | pygame.DOUBLEBUF)
        self.clock = pygame.time.Clock()
        
        # Font chữ khử răng cưa
        self.font = pygame.font.SysFont("Segoe UI", 18, bold=True)
        self.small_font = pygame.font.SysFont("Segoe UI", 14)
        self.label_font = pygame.font.SysFont("Segoe UI", 16, bold=True)
        self.title_font = pygame.font.SysFont("Segoe UI", 64, bold=True)
        self.heading_font = pygame.font.SysFont("Segoe UI", 28, bold=True)
        
        self.map_path = map_path
        self.grid, self.initial_state = load_map(str(map_path))
        self.assets_path = ROOT / "assets"
        self.assets = self._load_assets()
        
        # Hệ thống bộ nhớ đệm
        self.scaled_assets_cache = {}
        self.text_cache = {}
        
        self.page = "menu"
        self.mode = "single"
        self.algorithm = "A*"
        self.sidebar_open = True
        self.buttons = {}
        self.message = "Choose a mode to begin."
        
        # Biến xử lý Animation 120 FPS
        self.anim_t = 1.0
        self.anim_speed = 6.0  # Tốc độ trượt (càng cao lướt càng nhanh)
        self.prev_state = self.initial_state
        
        self._reset_run()

    def _load_assets(self):
        names = ("wall", "floor", "goal", "box", "box_agent1", "box_agent2", "agent")
        images = {}
        for name in names:
            path = self.assets_path / f"{name}.png"
            if path.is_file():
                try:
                    images[name] = pygame.image.load(str(path)).convert_alpha()
                except pygame.error as error:
                    print(f"Lỗi nạp ảnh {path}: {error}")
        return images

    def _reset_run(self):
        self.states = [self.initial_state]
        self.actions = []
        self.owner_timeline = [{}]
        self.action_index = 0
        self.total_cost = None
        self.visited = None
        self.playing = False
        self.playback_elapsed = 0
        self.prev_state = self.initial_state
        self.anim_t = 1.0

    def _text(self, text, position, color=None, font=None):
        font_obj = font or self.font
        color_val = color or COLORS["text"]
        text_str = str(text)
        cache_key = (text_str, color_val, font_obj)
        if cache_key not in self.text_cache:
            self.text_cache[cache_key] = font_obj.render(text_str, True, color_val)
        surface = self.text_cache[cache_key]
        self.screen.blit(surface, position)
        return surface.get_rect(topleft=position)

    def _button(self, name, label, rect, active=False, small=False):
        fill = COLORS["accent_dark"] if active else COLORS["button"]
        ink = COLORS["white"] if active else COLORS["text"]
        pygame.draw.rect(self.screen, fill, rect, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255, 40), rect, 1, border_radius=8)
        font_obj = self.small_font if small else self.label_font
        cache_key = (label, ink, font_obj)
        if cache_key not in self.text_cache:
            self.text_cache[cache_key] = font_obj.render(label, True, ink)
        surface = self.text_cache[cache_key]
        self.screen.blit(surface, surface.get_rect(center=rect.center))
        self.buttons[name] = rect

    def _asset(self, name, rect):
        image = self.assets.get(name)
        if image is None:
            return False
        cache_key = (name, rect.size)
        if cache_key not in self.scaled_assets_cache:
            self.scaled_assets_cache[cache_key] = pygame.transform.smoothscale(image, rect.size)
        self.screen.blit(self.scaled_assets_cache[cache_key], rect)
        return True

    def _draw_board(self, area):
        rows = self.grid["height"]
        columns = self.grid["width"]
        tile = max(36, min(122, area.width // max(1, columns), area.height // max(1, rows)))
        board_width, board_height = columns * tile, rows * tile
        origin_x = area.x + (area.width - board_width) // 2
        origin_y = area.y + (area.height - board_height) // 2
        board_rect = pygame.Rect(origin_x, origin_y, board_width, board_height)

        curr_state = self.states[self.action_index]
        prev_state = self.prev_state
        t = min(1.0, self.anim_t)

        # 1. Vẽ nền sàn, tường và các ô đích
        for r in range(rows):
            for c in range(columns):
                pos = (r, c)
                rect = pygame.Rect(origin_x + c * tile, origin_y + r * tile, tile, tile)
                if pos in self.grid["walls"]:
                    if not self._asset("wall", rect):
                        pygame.draw.rect(self.screen, COLORS["wall"], rect)
                        pygame.draw.rect(self.screen, COLORS["wall_edge"], rect, 2)
                    continue

                if not self._asset("floor", rect):
                    pygame.draw.rect(self.screen, COLORS["floor"], rect)
                    pygame.draw.rect(self.screen, COLORS["floor_line"], rect, 1)

                if pos in self.grid["goals"]:
                    goal_rect = rect.inflate(-tile // 3, -tile // 3)
                    if not self._asset("goal", goal_rect):
                        pygame.draw.circle(self.screen, COLORS["goal"], rect.center, max(4, tile // 6))

        # 2. Vẽ các Hộp với nội suy vị trí mượt (Smooth LERP)
        curr_boxes = list(curr_state.boxes)
        prev_boxes = list(prev_state.boxes)
        
        # Ghép cặp hộp di chuyển gần nhất để trượt mượt
        interpolated_boxes = []
        unpaired_curr = curr_boxes.copy()
        for pb in prev_boxes:
            best_match = min(unpaired_curr, key=lambda cb: abs(cb[0]-pb[0]) + abs(cb[1]-pb[1]))
            if abs(best_match[0]-pb[0]) + abs(best_match[1]-pb[1]) <= 1:
                interpolated_boxes.append((pb, best_match))
                unpaired_curr.remove(best_match)
            else:
                interpolated_boxes.append((pb, pb))

        owners = self.owner_timeline[self.action_index]
        for p_box, c_box in interpolated_boxes:
            interp_r = lerp(p_box[0], c_box[0], t)
            interp_c = lerp(p_box[1], c_box[1], t)
            
            box_x = origin_x + interp_c * tile + tile // 16
            box_y = origin_y + interp_r * tile + tile // 16
            box_size = tile - tile // 8
            box_rect = pygame.Rect(int(box_x), int(box_y), int(box_size), int(box_size))
            
            owner = owners.get(c_box)
            sprite = f"box_agent{owner}" if owner in (1, 2) else "box"
            if not self._asset(sprite, box_rect) and not self._asset("box", box_rect):
                fill = COLORS["agent"] if owner == 1 else COLORS["agent2"] if owner == 2 else COLORS["box"]
                pygame.draw.rect(self.screen, fill, box_rect, border_radius=6)
                pygame.draw.rect(self.screen, COLORS["box_edge"], box_rect, 2, border_radius=6)

        # 3. Vẽ Agent với nội suy vị trí mượt
        if curr_state.agent_pos and prev_state.agent_pos:
            agent_r = lerp(prev_state.agent_pos[0], curr_state.agent_pos[0], t)
            agent_c = lerp(prev_state.agent_pos[1], curr_state.agent_pos[1], t)
            
            inset = max(3, tile // 8)
            ag_size = tile - 2 * inset
            ag_x = origin_x + agent_c * tile + inset
            ag_y = origin_y + agent_r * tile + inset
            agent_rect = pygame.Rect(int(ag_x), int(ag_y), int(ag_size), int(ag_size))
            
            if not self._asset("agent", agent_rect):
                pygame.draw.circle(self.screen, COLORS["agent"], agent_rect.center, tile // 3)
                pygame.draw.circle(self.screen, COLORS["white"], agent_rect.center, tile // 3, 2)

        return board_rect

    def _draw_menu(self):
        self.buttons.clear()
        self.screen.fill(COLORS["background"])
        width, height = self.screen.get_size()
        
        left = max(48, width // 11)
        self._text("Introduction to AI Midterm Project", (left, 76), COLORS["accent"], self.small_font)
        self._text("SOKOBAN", (left - 4, 100), COLORS["white"], self.title_font)
        self._text("Academic Search Engine Demo", (left + 2, 175), (190, 201, 192), self.font)
        self._text(">> SELECT MODE <<", (left + 2, 250), COLORS["accent"], self.small_font)

        card_y = 280
        card_width = min(250, max(190, (width - 3 * left) // 2))
        card_height = 138
        gap = 18

        for index, (mode, title, note) in enumerate((
            ("single", "ONE AGENT", "Req 1 - 4 (A* & UCS)"),
            ("two", "TWO AGENTS", "Req 6 - 8 (Multi-Agent)"),
        )):
            card = pygame.Rect(left + index * (card_width + gap), card_y, card_width, card_height)
            selected = self.mode == mode
            pygame.draw.rect(self.screen, COLORS["background_alt"], card, border_radius=10)
            pygame.draw.rect(self.screen, COLORS["accent"] if selected else COLORS["line"], card, 2 if selected else 1, border_radius=10)
            self._text(f"0{index + 1}", (card.x + 17, card.y + 15), COLORS["accent"], self.small_font)
            self._text(title, (card.x + 17, card.y + 49), COLORS["white"], self.label_font)
            self._text(note, (card.x + 17, card.y + 82), (177, 188, 180), self.small_font)
            self.buttons[f"mode_{mode}"] = card

        play_width = card_width * 2 + gap
        self._button("start", "PLAY GAME", pygame.Rect(left, card_y + card_height + 24, play_width, 54), active=True)
        self._button("menu_map", "Choose map", pygame.Rect(left, card_y + card_height + 90, card_width, 40), small=True)
        self._text(f"MAP: {self.map_path.name}", (left, card_y + card_height + 145), (177, 188, 180), self.small_font)

        preview_width = min(420, max(280, width // 3))
        preview = pygame.Rect(width - preview_width - max(48, width // 12), 170, preview_width, min(420, height - 240))
        pygame.draw.rect(self.screen, (25, 33, 38), preview.inflate(20, 20), border_radius=12)
        self._draw_board(preview)

    def _draw_sidebar(self, panel):
        pygame.draw.rect(self.screen, COLORS["panel"], panel)
        pygame.draw.line(self.screen, (218, 221, 209), panel.topleft, (panel.left, panel.bottom), 1)
        x = panel.x + 20
        inner_width = panel.width - 40
        
        self._text("CONTROL PANEL", (x, panel.y + 18), COLORS["accent_dark"], self.small_font)
        self._text("Solver Setup", (x, panel.y + 40), COLORS["text"], self.heading_font)
        self._button("sidebar_close", "<", pygame.Rect(panel.right - 40, panel.y + 16, 26, 26), small=True)

        mode_y = panel.y + 86
        self._text("MODE", (x, mode_y), COLORS["muted"], self.small_font)
        option_width = (inner_width - 8) // 2
        self._button("mode_single", "Single", pygame.Rect(x, mode_y + 22, option_width, 34), active=self.mode == "single", small=True)
        self._button("mode_two", "Two-Agent", pygame.Rect(x + option_width + 8, mode_y + 22, option_width, 34), active=self.mode == "two", small=True)

        map_y = mode_y + 70
        self._text("MAP FILE", (x, map_y), COLORS["muted"], self.small_font)
        self._text(self.map_path.name, (x, map_y + 20), COLORS["text"], self.small_font)
        self._button("change_map", "Change Map...", pygame.Rect(x, map_y + 44, inner_width, 32), small=True)

        algo_y = map_y + 90
        self._text("ALGORITHM", (x, algo_y), COLORS["muted"], self.small_font)
        self._button("algo_ucs", "UCS", pygame.Rect(x, algo_y + 22, option_width, 34), active=self.algorithm == "UCS", small=True)
        self._button("algo_astar", "A* (Hungarian)", pygame.Rect(x + option_width + 8, algo_y + 22, option_width, 34), active=self.algorithm == "A*", small=True)
        self._button("solve", "Solve Puzzle", pygame.Rect(x, algo_y + 64, inner_width, 38), active=True, small=True)

        stats_y = algo_y + 118
        pygame.draw.line(self.screen, (218, 221, 209), (x, stats_y), (x + inner_width, stats_y), 1)
        self._text("METRICS", (x, stats_y + 10), COLORS["muted"], self.small_font)
        self._text(f"Action Step:    {self.action_index} / {len(self.actions)}", (x, stats_y + 32), COLORS["text"], self.small_font)
        cost_str = "-" if self.total_cost is None else str(self.total_cost)
        self._text(f"Path Cost:      {cost_str}", (x, stats_y + 54), COLORS["text"], self.small_font)
        visited_str = "-" if self.visited is None else f"{self.visited:,}"
        self._text(f"Explored Nodes: {visited_str}", (x, stats_y + 76), COLORS["text"], self.small_font)

        controls_y = panel.bottom - 110
        self._button("play_pause", "Pause" if self.playing else "Auto Play", pygame.Rect(x, controls_y, inner_width, 36), active=self.playing, small=True)
        half = (inner_width - 8) // 2
        self._button("step_back", "Previous", pygame.Rect(x, controls_y + 42, half, 32), small=True)
        self._button("step_forward", "Next", pygame.Rect(x + half + 8, controls_y + 42, half, 32), small=True)
        self._text("SPACE: Pause | LEFT/RIGHT: Step", (x, panel.bottom - 20), COLORS["muted"], self.small_font)

    def _draw_game(self):
        self.buttons.clear()
        self.screen.fill(COLORS["background"])
        width, height = self.screen.get_size()

        header = pygame.Rect(0, 0, width, 58)
        pygame.draw.rect(self.screen, COLORS["background_alt"], header)
        pygame.draw.line(self.screen, COLORS["line"], (0, header.bottom), (width, header.bottom), 1)

        self._button("home", "MENU", pygame.Rect(18, 12, 64, 34), small=True)
        self._text("SOKOBAN AI", (96, 17), COLORS["white"], self.label_font)
        self._text(f"FPS: {int(self.clock.get_fps())}", (220, 20), COLORS["accent"], self.small_font)
        self._text(f"Map: {self.map_path.name}", (width - 320, 20), (196, 205, 197), self.small_font)
        self._text(f"Step: {self.action_index}/{len(self.actions)}", (width - 140, 20), COLORS["white"], self.small_font)

        panel_width = min(330, max(280, width // 3)) if self.sidebar_open else 0
        if self.sidebar_open:
            panel = pygame.Rect(width - panel_width, header.bottom, panel_width, height - header.bottom)
            self._draw_sidebar(panel)
            board_right = panel.left
        else:
            board_right = width
            self._button("sidebar_open", ">", pygame.Rect(width - 48, 70, 36, 38), small=True)

        board_area = pygame.Rect(24, 70, max(100, board_right - 48), height - 98)
        self._draw_board(board_area)

        if self.message:
            msg = self.small_font.render(self.message, True, COLORS["white"])
            rect = msg.get_rect(midbottom=(board_area.centerx, height - 12))
            self.screen.blit(msg, rect)

    def _draw(self):
        if self.page == "menu":
            self._draw_menu()
        else:
            self._draw_game()

    def _make_timeline(self, actions):
        states = [self.initial_state]
        owners = [{}]
        for action in actions:
            current = states[-1]
            next_state = next(
                candidate_state
                for candidate_action, candidate_state, _ in get_successors(current, self.grid)
                if candidate_action == action
            )
            owner_map = dict(owners[-1])
            moved_boxes = next_state.boxes - current.boxes
            if moved_boxes:
                moved_box = next(iter(moved_boxes))
                old_box = next(iter(current.boxes - next_state.boxes))
                owner_map.pop(old_box, None)
                owner_map[moved_box] = 1
            states.append(next_state)
            owners.append(owner_map)
        return states, owners

    def _choose_map(self):
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            selected = filedialog.askopenfilename(
                title="Choose Sokoban map",
                filetypes=(("Text maps", "*.txt"), ("All files", "*.*")),
            )
            root.destroy()
            if not selected:
                return
            grid, initial_state = load_map(selected)
            if initial_state.agent_pos is None:
                raise ValueError("Bản đồ phải chứa vị trí người chơi 'A'")
            self.grid = grid
            self.initial_state = initial_state
            self.map_path = Path(selected)
            self.scaled_assets_cache.clear()
            self._reset_run()
            self.message = f"Loaded {self.map_path.name}"
        except Exception as error:
            self.message = f"Lỗi nạp map: {error}"

    def find_solution(self):
        self.playing = False
        self.message = f"Solving with {self.algorithm}..."
        self._draw()
        pygame.display.flip()
        
        actions, cost, visited = ALGORITHMS[self.algorithm](self.initial_state, self.grid)
        self.action_index = 0
        self.total_cost = cost if actions is not None else None
        self.visited = visited
        
        if actions is None:
            self.actions = []
            self.states = [self.initial_state]
            self.owner_timeline = [{}]
            self.message = "Không tìm thấy lời giải cho map này."
            return
            
        self.actions = actions
        self.states, self.owner_timeline = self._make_timeline(actions)
        self.playing = bool(actions)
        self.message = "Đã tìm thấy lời giải! Đang phát chuyển động." if actions else "Đã ở đích."

    def _step(self, amount):
        if not self.actions:
            return
        new_index = max(0, min(len(self.actions), self.action_index + amount))
        if new_index != self.action_index:
            self.prev_state = self.states[self.action_index]
            self.action_index = new_index
            self.anim_t = 0.0  # Bắt đầu hoạt ảnh trượt từ vị trí cũ sang mới
            
        if self.action_index == len(self.actions):
            self.playing = False
            self.message = "Puzzle Solved!"

    def _activate(self, name):
        if name in ("mode_single", "mode_single_menu"):
            self.mode = "single"
            self.message = "Single-agent mode selected."
        elif name in ("mode_two", "mode_two_menu"):
            self.mode = "two"
            self.message = "Two-agent mode UI preview."
        elif name == "start":
            self.page = "game"
            self.sidebar_open = True
            self._reset_run()
            self.message = "Ready. Click 'Solve Puzzle' to run."
        elif name in ("menu_map", "change_map"):
            self._choose_map()
        elif name == "home":
            self.page = "menu"
            self.playing = False
        elif name == "sidebar_close":
            self.sidebar_open = False
        elif name == "sidebar_open":
            self.sidebar_open = True
        elif name == "algo_ucs":
            self.algorithm = "UCS"
        elif name == "algo_astar":
            self.algorithm = "A*"
        elif name == "solve":
            self.find_solution()
        elif name == "play_pause" and self.actions:
            self.playing = not self.playing
            self.message = "Playing animation..." if self.playing else "Paused."
        elif name == "step_back":
            self._step(-1)
        elif name == "step_forward":
            self._step(1)

    def run(self):
        running = True
        while running:
            # Chạy ở tốc độ khung hình 120 FPS
            dt = self.clock.tick(120) / 1000.0  # Delta time theo giây
            
            # Cập nhật chuyển động nội suy mượt mà
            if self.anim_t < 1.0:
                self.anim_t = min(1.0, self.anim_t + self.anim_speed * dt)

            if self.page == "game" and self.playing:
                self.playback_elapsed += dt
                # Mỗi bước đẩy cách nhau 0.22s, lướt êm ái
                if self.playback_elapsed >= 0.22:
                    self.playback_elapsed = 0
                    self._step(1)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE | pygame.DOUBLEBUF)
                    self.scaled_assets_cache.clear()
                elif event.type == pygame.KEYDOWN and self.page == "game":
                    if event.key == pygame.K_TAB:
                        self.sidebar_open = not self.sidebar_open
                    elif event.key == pygame.K_SPACE and self.actions:
                        self.playing = not self.playing
                        self.message = "Playing animation..." if self.playing else "Paused."
                    elif event.key == pygame.K_LEFT:
                        self._step(-1)
                    elif event.key == pygame.K_RIGHT:
                        self._step(1)
                    elif event.key == pygame.K_r:
                        self._reset_run()
                        self.message = "Run reset."
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for name, rect in self.buttons.items():
                        if rect.collidepoint(event.pos):
                            self._activate(name)
                            break

            self._draw()
            pygame.display.flip()

        pygame.quit()

def main():
    parser = argparse.ArgumentParser(description="Sokoban search game")
    parser.add_argument("--map", type=Path, default=ROOT / "example_map.txt", help="Initial map file")
    args = parser.parse_args()
    SokobanGame(args.map).run()

if __name__ == "__main__":
    main()