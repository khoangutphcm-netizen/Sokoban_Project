import argparse
from pathlib import Path

import pygame

from core.map_loader import load_map
from core.state import get_successors
from search.astar import a_star_search
from search.ucs import uniform_cost_search


ROOT = Path(__file__).resolve().parent
ALGORITHMS = {"UCS": uniform_cost_search, "A*": a_star_search}
COLORS = {
    "background": (27, 35, 39),
    "background_alt": (37, 47, 51),
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


class SokobanGame:
    def __init__(self, map_path: Path):
        pygame.init()
        pygame.display.set_caption("Sokoban")
        self.screen = pygame.display.set_mode((1120, 780), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 25)
        self.small_font = pygame.font.Font(None, 20)
        self.label_font = pygame.font.Font(None, 23)
        self.title_font = pygame.font.Font(None, 76)
        self.heading_font = pygame.font.Font(None, 38)

        self.map_path = map_path
        self.grid, self.initial_state = load_map(str(map_path))
        self.assets_path = ROOT / "assets"
        self.assets = self._load_assets()
        self.page = "menu"
        self.mode = "single"
        self.algorithm = "A*"
        self.sidebar_open = True
        self.buttons = {}
        self.message = "Choose a mode to begin."
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
                    print(f"Ignoring asset {path}: {error}")
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

    def _text(self, text, position, color=None, font=None):
        surface = (font or self.font).render(str(text), True, color or COLORS["text"])
        self.screen.blit(surface, position)
        return surface.get_rect(topleft=position)

    def _button(self, name, label, rect, active=False, small=False):
        fill = COLORS["accent_dark"] if active else COLORS["button"]
        ink = COLORS["white"] if active else COLORS["text"]
        pygame.draw.rect(self.screen, fill, rect, border_radius=7)
        pygame.draw.rect(self.screen, (255, 255, 255, 30), rect, 1, border_radius=7)
        font = self.small_font if small else self.label_font
        surface = font.render(label, True, ink)
        self.screen.blit(surface, surface.get_rect(center=rect.center))
        self.buttons[name] = rect

    def _asset(self, name, rect):
        image = self.assets.get(name)
        if image is None:
            return False
        self.screen.blit(pygame.transform.smoothscale(image, rect.size), rect)
        return True

    def _draw_board(self, area):
        rows = self.grid["height"]
        columns = self.grid["width"]
        tile = max(16, min(84, area.width // max(1, columns), area.height // max(1, rows)))
        board_width, board_height = columns * tile, rows * tile
        origin_x = area.x + (area.width - board_width) // 2
        origin_y = area.y + (area.height - board_height) // 2
        board_rect = pygame.Rect(origin_x, origin_y, board_width, board_height)
        state = self.states[self.action_index]
        owners = self.owner_timeline[self.action_index]

        for row in range(rows):
            for column in range(columns):
                position = (row, column)
                rect = pygame.Rect(origin_x + column * tile, origin_y + row * tile, tile, tile)
                if position in self.grid["walls"]:
                    if not self._asset("wall", rect):
                        pygame.draw.rect(self.screen, COLORS["wall"], rect)
                        pygame.draw.rect(self.screen, COLORS["wall_edge"], rect, max(1, tile // 14))
                    continue

                if not self._asset("floor", rect):
                    pygame.draw.rect(self.screen, COLORS["floor"], rect)
                    pygame.draw.rect(self.screen, COLORS["floor_line"], rect, 1)
                if position in self.grid["goals"]:
                    goal_rect = rect.inflate(-tile // 3, -tile // 3)
                    if not self._asset("goal", goal_rect):
                        pygame.draw.circle(self.screen, COLORS["goal"], rect.center, max(3, tile // 7))
                if position in state.boxes:
                    box_rect = rect.inflate(-tile // 8, -tile // 8)
                    owner = owners.get(position)
                    sprite = f"box_agent{owner}" if owner in (1, 2) else "box"
                    if not self._asset(sprite, box_rect) and not self._asset("box", box_rect):
                        fill = COLORS["agent"] if owner == 1 else COLORS["agent2"] if owner == 2 else COLORS["box"]
                        pygame.draw.rect(self.screen, fill, box_rect, border_radius=4)
                        pygame.draw.rect(self.screen, COLORS["box_edge"], box_rect, 2, border_radius=4)
                if position == state.agent_pos:
                    inset = max(3, tile // 8)
                    agent_rect = rect.inflate(-2 * inset, -2 * inset)
                    if not self._asset("agent", agent_rect):
                        pygame.draw.circle(self.screen, COLORS["agent"], rect.center, tile // 3)
                        pygame.draw.circle(self.screen, COLORS["white"], rect.center, tile // 3, 2)

        return board_rect

    def _draw_menu(self):
        self.buttons.clear()
        self.screen.fill(COLORS["background"])
        width, height = self.screen.get_size()

        for x in range(0, width, 48):
            pygame.draw.line(self.screen, (32, 42, 45), (x, 0), (x, height), 1)
        for y in range(0, height, 48):
            pygame.draw.line(self.screen, (32, 42, 45), (0, y), (width, y), 1)

        left = max(48, width // 11)
        self._text("PUZZLE / SEARCH", (left, 76), COLORS["accent"], self.small_font)
        self._text("SOKOBAN", (left - 4, 106), COLORS["white"], self.title_font)
        self._text("A classic box-pushing puzzle", (left + 2, 184), (190, 201, 192), self.font)
        self._text("SELECT MODE", (left + 2, 265), COLORS["accent"], self.small_font)

        card_y = 294
        card_width = min(250, max(190, (width - 3 * left) // 2))
        card_height = 138
        gap = 18
        for index, (mode, title, note) in enumerate((
            ("single", "ONE AGENT", "Search and replay a solution"),
            ("two", "TWO AGENTS", "Interface slot for future play"),
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
        self._button("start", "PLAY", pygame.Rect(left, card_y + card_height + 24, play_width, 56), active=True)
        self._button("menu_map", "Choose map", pygame.Rect(left, card_y + card_height + 94, card_width, 42), small=True)
        self._text(f"MAP     {self.map_path.name}", (left, card_y + card_height + 155), (177, 188, 180), self.small_font)

        preview_width = min(390, max(260, width // 3))
        preview = pygame.Rect(width - preview_width - max(48, width // 12), 190, preview_width, min(390, height - 250))
        pygame.draw.rect(self.screen, (31, 41, 44), preview.inflate(24, 24), border_radius=10)
        self._draw_board(preview)
        self._text("CURRENT LAYOUT", (preview.x, preview.bottom + 28), COLORS["accent"], self.small_font)
        self._text("Use the sidebar in game to change map or mode.", (preview.x, preview.bottom + 54), (177, 188, 180), self.small_font)

    def _draw_sidebar(self, panel):
        pygame.draw.rect(self.screen, COLORS["panel"], panel)
        pygame.draw.line(self.screen, (218, 221, 209), panel.topleft, (panel.left, panel.bottom), 1)
        x = panel.x + 20
        inner_width = panel.width - 40
        self._text("GAME MENU", (x, panel.y + 22), COLORS["accent_dark"], self.small_font)
        self._text("Session", (x, panel.y + 48), COLORS["text"], self.heading_font)
        close_rect = pygame.Rect(panel.right - 43, panel.y + 17, 28, 28)
        self._button("sidebar_close", "<", close_rect, small=True)

        mode_y = panel.y + 98
        self._text("MODE", (x, mode_y), COLORS["muted"], self.small_font)
        option_width = (inner_width - 8) // 2
        self._button("mode_single", "One agent", pygame.Rect(x, mode_y + 25, option_width, 36), active=self.mode == "single", small=True)
        self._button("mode_two", "Two agents", pygame.Rect(x + option_width + 8, mode_y + 25, option_width, 36), active=self.mode == "two", small=True)

        map_y = mode_y + 86
        self._text("LAYOUT", (x, map_y), COLORS["muted"], self.small_font)
        self._text(self.map_path.name, (x, map_y + 22), COLORS["text"], self.small_font)
        self._button("change_map", "Change map", pygame.Rect(x, map_y + 48, inner_width, 34), small=True)

        algorithm_y = map_y + 103
        self._text("SEARCH ALGORITHM", (x, algorithm_y), COLORS["muted"], self.small_font)
        self._button("algo_ucs", "UCS", pygame.Rect(x, algorithm_y + 24, option_width, 34), active=self.algorithm == "UCS", small=True)
        self._button("algo_astar", "A*", pygame.Rect(x + option_width + 8, algorithm_y + 24, option_width, 34), active=self.algorithm == "A*", small=True)
        solve_label = "Preview agent 1" if self.mode == "two" else "Find solution"
        self._button("solve", solve_label, pygame.Rect(x, algorithm_y + 68, inner_width, 38), active=True, small=True)

        if self.mode == "two":
            slot_y = algorithm_y + 121
            pygame.draw.line(self.screen, (218, 221, 209), (x, slot_y), (x + inner_width, slot_y), 1)
            self._text("AGENT SLOTS", (x, slot_y + 13), COLORS["muted"], self.small_font)
            self._text("Agent 1  /  search preview", (x, slot_y + 39), COLORS["agent"], self.small_font)
            self._text("Agent 2  /  controller pending", (x, slot_y + 64), COLORS["agent2"], self.small_font)
            stats_y = slot_y + 101
        else:
            stats_y = algorithm_y + 121

        pygame.draw.line(self.screen, (218, 221, 209), (x, stats_y), (x + inner_width, stats_y), 1)
        self._text("RUN STATS", (x, stats_y + 13), COLORS["muted"], self.small_font)
        self._text(f"Actions       {self.action_index} / {len(self.actions)}", (x, stats_y + 39), COLORS["text"], self.small_font)
        cost = "-" if self.total_cost is None else self.total_cost
        self._text(f"Solution cost  {cost}", (x, stats_y + 63), COLORS["text"], self.small_font)
        visited = "-" if self.visited is None else f"{self.visited:,}"
        self._text(f"Visited states {visited}", (x, stats_y + 87), COLORS["text"], self.small_font)

        controls_y = panel.bottom - 113
        self._button("play_pause", "Pause" if self.playing else "Play", pygame.Rect(x, controls_y, inner_width, 36), active=self.playing, small=True)
        half = (inner_width - 8) // 2
        self._button("step_back", "Previous", pygame.Rect(x, controls_y + 44, half, 34), small=True)
        self._button("step_forward", "Next", pygame.Rect(x + half + 8, controls_y + 44, half, 34), small=True)
        self._text("SPACE pause   LEFT/RIGHT step", (x, panel.bottom - 21), COLORS["muted"], self.small_font)

    def _draw_game(self):
        self.buttons.clear()
        self.screen.fill(COLORS["background"])
        width, height = self.screen.get_size()
        header = pygame.Rect(0, 0, width, 62)
        pygame.draw.rect(self.screen, COLORS["background_alt"], header)
        pygame.draw.line(self.screen, COLORS["line"], (0, header.bottom), (width, header.bottom), 1)

        self._button("home", "MENU", pygame.Rect(20, 13, 68, 36), small=True)
        self._text("SOKOBAN", (108, 19), COLORS["white"], self.label_font)
        mode_label = "ONE AGENT" if self.mode == "single" else "TWO AGENTS / UI PREVIEW"
        self._text(mode_label, (244, 22), COLORS["accent"], self.small_font)
        self._text(self.map_path.name, (width - 290, 22), (196, 205, 197), self.small_font)
        self._text(f"ACTIONS  {self.action_index}/{len(self.actions)}", (width - 150, 22), COLORS["white"], self.small_font)

        panel_width = min(330, max(290, width // 3)) if self.sidebar_open else 0
        if self.sidebar_open:
            panel = pygame.Rect(width - panel_width, header.bottom, panel_width, height - header.bottom)
            self._draw_sidebar(panel)
            board_right = panel.left
        else:
            board_right = width
            self._button("sidebar_open", ">", pygame.Rect(width - 52, 76, 38, 42), small=True)

        board_area = pygame.Rect(30, 76, max(100, board_right - 60), height - 108)
        board_rect = self._draw_board(board_area)
        if self.mode == "two":
            badge = pygame.Rect(board_rect.x, max(70, board_rect.y - 38), 248, 28)
            pygame.draw.rect(self.screen, COLORS["background_alt"], badge, border_radius=5)
            self._text("SECOND AGENT SLOT: NOT CONNECTED", (badge.x + 9, badge.y + 6), COLORS["agent2"], self.small_font)

        if self.message:
            msg = self.small_font.render(self.message, True, COLORS["white"])
            rect = msg.get_rect(midbottom=(board_area.centerx, height - 18))
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
                raise ValueError("Map must contain an A agent")
            self.grid = grid
            self.initial_state = initial_state
            self.map_path = Path(selected)
            self._reset_run()
            self.message = f"Loaded {self.map_path.name}; run reset."
        except (OSError, ValueError, ImportError) as error:
            self.message = f"Could not load map: {error}"

    def find_solution(self):
        self.playing = False
        self.message = f"Searching with {self.algorithm}..."
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
            self.message = "No solution found for this map."
            return
        self.actions = actions
        self.states, self.owner_timeline = self._make_timeline(actions)
        self.playing = bool(actions)
        self.message = "Solution found. Playback started." if actions else "Already solved."

    def _step(self, amount):
        if not self.actions:
            return
        self.action_index = max(0, min(len(self.actions), self.action_index + amount))
        if self.action_index == len(self.actions):
            self.playing = False
            self.message = "Puzzle solved."

    def _activate(self, name):
        if name == "mode_single" or name == "mode_single_menu":
            self.mode = "single"
            self.message = "Single-agent mode selected."
        elif name == "mode_two" or name == "mode_two_menu":
            self.mode = "two"
            self.message = "Two-agent interface selected; second controller is not connected."
        elif name == "start":
            self.page = "game"
            self.sidebar_open = True
            self._reset_run()
            self.message = "Game ready. Choose an algorithm and find a solution."
        elif name == "menu_map":
            self._choose_map()
        elif name == "home":
            self.page = "menu"
            self.playing = False
        elif name == "sidebar_close":
            self.sidebar_open = False
        elif name == "sidebar_open":
            self.sidebar_open = True
        elif name == "mode_single":
            self.mode = "single"
            self.playing = False
            self.message = "Single-agent mode selected."
        elif name == "mode_two":
            self.mode = "two"
            self.playing = False
            self.message = "Two-agent UI selected; only agent 1 is active."
        elif name == "change_map":
            self._choose_map()
        elif name == "algo_ucs":
            self.algorithm = "UCS"
        elif name == "algo_astar":
            self.algorithm = "A*"
        elif name == "solve":
            self.find_solution()
        elif name == "play_pause" and self.actions:
            self.playing = not self.playing
            self.message = "Playback started." if self.playing else "Playback paused."
        elif name == "step_back":
            self._step(-1)
        elif name == "step_forward":
            self._step(1)

    def run(self):
        running = True
        while running:
            elapsed = self.clock.tick(60)
            if self.page == "game" and self.playing:
                self.playback_elapsed += elapsed
                if self.playback_elapsed >= 260:
                    self.playback_elapsed = 0
                    self._step(1)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                elif event.type == pygame.KEYDOWN and self.page == "game":
                    if event.key == pygame.K_TAB:
                        self.sidebar_open = not self.sidebar_open
                    elif event.key == pygame.K_SPACE and self.actions:
                        self.playing = not self.playing
                        self.message = "Playback started." if self.playing else "Playback paused."
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
