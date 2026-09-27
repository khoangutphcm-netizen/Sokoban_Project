import heapq
from core.state import GameState, get_successors
from search.heuristic import hungarian_heuristic, compute_deadlocks

class AStarNode:
    def __init__(self, state: GameState, parent=None, action=None, g_cost: int = 0, h_cost: int = 0):
        self.state = state
        self.parent = parent
        self.action = action
        self.g_cost = g_cost
        self.h_cost = h_cost
        self.f_cost = g_cost + h_cost

    def __lt__(self, other):
        return self.f_cost < other.f_cost

def reconstruct_path(node: AStarNode):
    actions = []
    curr = node
    while curr.parent is not None:
        actions.append(curr.action)
        curr = curr.parent
    actions.reverse()
    return actions

def a_star_search(initial_state: GameState, grid: dict):
    deadlocks = compute_deadlocks(grid)
    start_h = hungarian_heuristic(initial_state, grid)
    start_node = AStarNode(initial_state, g_cost=0, h_cost=start_h)
    
    frontier = []
    counter = 0
    heapq.heappush(frontier, (start_node.f_cost, counter, start_node))
    
    explored = set()
    best_g = {initial_state: 0}

    while frontier:
        f_val, _, current_node = heapq.heappop(frontier)
        current_state = current_node.state

        if current_state.is_goal(grid["goals"]):
            return reconstruct_path(current_node), current_node.g_cost, len(explored)

        if current_state in explored:
            continue
        explored.add(current_state)

        for action, next_state, step_cost in get_successors(current_state, grid):
            if any(b in deadlocks for b in next_state.boxes):
                continue

            new_g = current_node.g_cost + step_cost
            if next_state not in explored and (next_state not in best_g or new_g < best_g[next_state]):
                best_g[next_state] = new_g
                h_val = hungarian_heuristic(next_state, grid)
                
                if h_val >= 10000:
                    continue

                child_node = AStarNode(next_state, parent=current_node, action=action, g_cost=new_g, h_cost=h_val)
                counter += 1
                heapq.heappush(frontier, (child_node.f_cost, counter, child_node))

    return None, 0, len(explored)