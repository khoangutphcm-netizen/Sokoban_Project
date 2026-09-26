

from dataclasses import dataclass
from typing import FrozenSet, Tuple, List

Pos = Tuple[int, int]# (dr, dc) cho tung huong di chuyen

 
DIRECTIONS = {        
    "North": (-1, 0),
    "South": (1, 0),
    "East": (0, 1),
    "West": (0, -1),
}

@dataclass(frozen=True) # Ép GameState thành kiểu dữ liệu bất biến


class GameState:
    """Lưu trữ state, bao gồm vị trí của agent và các box"""

    agent: Pos # vi trí agent (row, col)
    boxes: FrozenSet[Pos] # vì box bất biến, nên dùng frozenset để lưu trữ các vị trí box cũng như hashable

    def is_goal(self, goals: FrozenSet[Pos]):  
        return self.boxes == goals # nếu tất cả box đều ở vị trí goal thì state hiện tại là goal state


def get_successors(state: GameState, grid):  
    """
    Sinh ra các state kế tiếp từ state hiện tại, cùng với action và cost ( = 1)
    Return: List[Tuple[action, next_state, cost]]
    """
    walls = grid["walls"] # walls
    successors = [] # danh sách các state kế tiếp, mỗi phần tử là tuple (action, next_state, cost)

    for action, (dr, dc) in DIRECTIONS.items():
        next_agent = (state.agent[0] + dr, state.agent[1] + dc) # tạo vị trí agent mới khi move

        if next_agent in walls:
            continue  # tường chặn

        if next_agent in state.boxes:
            # ở trước có box thì cần kiểm tra xem box có thể đẩy được không
            next_box = (next_agent[0] + dr, next_agent[1] + dc)
            if next_box in walls or next_box in state.boxes:
                continue  # bị chặn

            new_boxes = set(state.boxes) # tạo một tập hợp mới từ các vị trí box hiện tại
            new_boxes.remove(next_agent) # loại bỏ box cũ
            new_boxes.add(next_box)      # thêm box mới vào vị trí đẩy được
            next_state = GameState(agent=next_agent, boxes=frozenset(new_boxes)) # tạo state mới với agent di chuyển và box di chuyn

        else:# ô trống, AI có thể chỉ di chuyển 
            next_state = GameState(agent=next_agent, boxes=state.boxes) # tạo state mới chỉ agent di chuyển, box không thay đổi

        successors.append((action, next_state, 1)) # Thêm (action, next_state, cost = 1) vào list successors 

    return successors 


def apply_action(state: GameState, action: str, grid) -> GameState:
    """trả về state mới sau khi action được áp dụng từ state hiện tại"""
    for a, next_state, _ in get_successors(state, grid): # Duyệt qua tất cả các state kế tiếp
        if a == action: # Nếu action trùng với action được sinh ra từ get_successors, trả về next_state tương ứng
            return next_state
    raise ValueError(f"Debug(Action): Action '{action}' không hợp lệ từ state {state}")

"""Cái này dùng để tạo danh sách chuỗi trạng thái phục vụ tính năng phát lại, tua tới và tua lùi từng bước"""
def reconstruct_states(initial_state: GameState, actions: List[str], grid) -> List[GameState]:
    """với initial_state + list action, tái tạo lại toàn bộ chuỗi state đã đi qua."""
    states = [initial_state]
    current = initial_state
    for a in actions:
        current = apply_action(current, a, grid)
        states.append(current)
    return states
