import heapq
from core.state import GameState, get_successors

def chebyshev_distance(pos1, pos2):
    return max(abs(pos1[0] - pos2[0]), abs(pos1[1] - pos2[1]))

def heuristic(state: GameState, grid: dict) -> int:
    boxes = state.boxes
    goals = grid["goals"]
    unmatched_boxes = [b for b in boxes if b not in goals]
    unmatched_goals = [g for g in goals if g not in boxes]
    
    if not unmatched_boxes or not unmatched_goals:
        return 0
        
    h = 0
    for box in unmatched_boxes:
        min_d = min(chebyshev_distance(box, g) for g in unmatched_goals)
        h += min_d
    return h

def uniform_cost_search(initial_state: GameState, grid: dict):
    frontier = []
    counter = 0
    heapq.heappush(frontier, (0, counter, initial_state, []))
    visited = set()
    
    while frontier:
        cost, _, state, actions = heapq.heappop(frontier)
        
        if state.is_goal(grid["goals"]):
            return actions, cost, len(visited)
            
        if state in visited:
            continue
        visited.add(state)
        
        for action, next_state, step_cost in get_successors(state, grid):
            if next_state not in visited:
                counter += 1
                heapq.heappush(frontier, (cost + step_cost, counter, next_state, actions + [action]))
                
    return None, 0, len(visited)

def a_star_search(initial_state: GameState, grid: dict):
    frontier = []
    counter = 0
    start_h = heuristic(initial_state, grid)
    heapq.heappush(frontier, (start_h, counter, initial_state, [], 0))
    visited = set()
    
    while frontier:
        f_cost, _, state, actions, g_cost = heapq.heappop(frontier)
        
        if state.is_goal(grid["goals"]):
            return actions, g_cost, len(visited)
            
        if state in visited:
            continue
        visited.add(state)
        
        for action, next_state, step_cost in get_successors(state, grid):
            if next_state not in visited:
                counter += 1
                new_g = g_cost + step_cost
                new_h = heuristic(next_state, grid)
                new_f = new_g + new_h
                heapq.heappush(frontier, (new_f, counter, next_state, actions + [action], new_g))
                
    return None, 0, len(visited)