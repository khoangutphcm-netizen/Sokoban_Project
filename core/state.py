from typing import Tuple, FrozenSet

class GameState:
    def __init__(self, agent_pos: Tuple[int, int], boxes: FrozenSet[Tuple[int, int]]):
        self.agent_pos = agent_pos
        self.boxes = boxes

    def is_goal(self, goals: set) -> bool:
        return self.boxes == frozenset(goals)

    def __eq__(self, other):
        if not isinstance(other, GameState):
            return False
        return self.agent_pos == other.agent_pos and self.boxes == other.boxes

    def __hash__(self):
        return hash((self.agent_pos, self.boxes))

    def __repr__(self):
        return f"GameState(agent={self.agent_pos}, boxes={set(self.boxes)})"

# 4 huong di chuyen: Bac, Nam, Dong, Tay
DIRECTIONS = {
    "North": (-1, 0),
    "South": (1, 0),
    "East": (0, 1),
    "West": (0, -1),
}

def get_successors(state: GameState, grid: dict):
    successors = []
    walls = grid["walls"]
    agent_r, agent_c = state.agent_pos
    boxes = set(state.boxes)

    for action, (dr, dc) in DIRECTIONS.items():
        new_agent = (agent_r + dr, agent_c + dc)

        # Di chuyen vao tuong
        if new_agent in walls:
            continue

        # Day hop
        if new_agent in boxes:
            new_box = (new_agent[0] + dr, new_agent[1] + dc)
            # Hop bi can boi tuong hoac hop khac
            if new_box in walls or new_box in boxes:
                continue

            new_boxes = set(boxes)
            new_boxes.remove(new_agent)
            new_boxes.add(new_box)
            next_state = GameState(new_agent, frozenset(new_boxes))
            successors.append((action, next_state, 1))
        else:
            # Di chuyen vao o trong
            next_state = GameState(new_agent, state.boxes)
            successors.append((action, next_state, 1))

    return successors