import heapq
import time
from core.state import GameState, get_successors
from search.heuristic import compute_deadlocks

class SearchNode:
    def __init__(self, state: GameState, parent=None, action=None, cost: int = 0):
        self.state = state
        self.parent = parent
        self.action = action
        self.cost = cost

    def __lt__(self, other):
        return self.cost < other.cost

def reconstruct_path(node: SearchNode):
    actions = []
    curr = node
    while curr.parent is not None:
        actions.append(curr.action)
        curr = curr.parent
    actions.reverse()
    return actions

def uniform_cost_search(initial_state: GameState, grid: dict, max_nodes: int = 50000):
    deadlocks = compute_deadlocks(grid)
    start_node = SearchNode(initial_state, cost=0)
    
    frontier = []
    counter = 0
    heapq.heappush(frontier, (start_node.cost, counter, start_node))
    
    explored = set()
    best_costs = {initial_state: 0}
    start_time = time.time()

    while frontier:
        cost, _, current_node = heapq.heappop(frontier)
        current_state = current_node.state

        if current_state.is_goal(grid["goals"]):
            return reconstruct_path(current_node), current_node.cost, len(explored)

        if current_state in explored:
            continue
        explored.add(current_state)

        # In tiến trình UCS
        if len(explored) % 5000 == 0:
            print(f"   -> [UCS Đang duyệt]: {len(explored):,} nodes...")

        # Giới hạn an toàn tránh treo máy
        if len(explored) >= max_nodes:
            print(f"   -> [UCS Cảnh báo]: Đã duyệt vượt quá {max_nodes:,} nodes mà chưa tìm thấy đích (Bùng nổ không gian trạng thái).")
            return None, cost, len(explored)

        for action, next_state, step_cost in get_successors(current_state, grid):
            if any(b in deadlocks for b in next_state.boxes):
                continue

            new_cost = current_node.cost + step_cost
            if next_state not in explored and (next_state not in best_costs or new_cost < best_costs[next_state]):
                best_costs[next_state] = new_cost
                child_node = SearchNode(next_state, parent=current_node, action=action, cost=new_cost)
                counter += 1
                heapq.heappush(frontier, (child_node.cost, counter, child_node))

    return None, 0, len(explored)