"""
file map .txt gồm có
  - grid: thôing tin về bản đồ, là dict gồm các key
      'walls' : tường (%),
      'goals' : vị trí đích (D)
      'width', 'height': kích thước bản đồ
  - initial_state: GameState ban đầu

ký hiệu map 
  %  -> walls
  A  -> vi trí agent
  B  -> box (chưa ở vị trí đích)
  D  -> vị trí đích (goal) còn trống
  C  -> box đang nằm đúng tại một goal (vừa là box, vừa là goal)
  ' '-> ô trống
"""

from core.state import GameState

def load_map(path: str):
    with open(path, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    lines = [line.rstrip("\r\n") for line in raw_lines if line.strip()]
    if not lines:
        raise ValueError("File map rong!")

    height = len(lines)
    width = max(len(line) for line in lines)

    walls = set()
    goals = set()
    boxes = set()
    agent_pos = None

    for r, line in enumerate(lines):
        for c, ch in enumerate(line):
            pos = (r, c)
            if ch in ("%", "#"):
                walls.add(pos)
            elif ch == "D":
                goals.add(pos)
            elif ch == "B":
                boxes.add(pos)
            elif ch == "A":
                agent_pos = pos
            elif ch == "C":  # Hop nam tren dich
                boxes.add(pos)
                goals.add(pos)

    grid = {
        "walls": walls,
        "goals": goals,
        "width": width,
        "height": height
    }

    initial_state = GameState(agent_pos=agent_pos, boxes=frozenset(boxes))
    return grid, initial_state