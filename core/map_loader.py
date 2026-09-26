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

from state import GameState


def load_map(path):
    """
    đọc file map từ đường dẫn path, trả về grid và initial_state
    """
    with open(path, "r", encoding="utf-8") as f:
        raw_lines = [line.rstrip("\n") for line in f.readlines()]
    while raw_lines and raw_lines[-1] == "": #bỏ qua mấy cái dòng cuối 
        raw_lines.pop()

    height = len(raw_lines)  
    width = max(len(line) for line in raw_lines)  
    lines = [line.ljust(width) for line in raw_lines] 

    walls = set() 
    goals = set()
    boxes = set()
    agent = None
    # lặp qua từng ký tự trong map để xác định vị trí walls, goals, boxes, agent
    for r, line in enumerate(lines):
        for c, ch in enumerate(line):
            pos = (r, c)
            if ch == "%":
                walls.add(pos)
            elif ch == "A":
                agent = pos
            elif ch == "B":
                boxes.add(pos)
            elif ch == "D":
                goals.add(pos)
            elif ch == "C":
                boxes.add(pos)
                goals.add(pos)
            elif ch == " ":
                pass  # ô trống 
            else:
                raise ValueError(f"Debug(Load_Map) Map '{path}' lỗi: ký tự '{ch}'nằm ở dòng {r+1}, cột {c+1}")

    if agent is None:
        raise ValueError(f"Debug(Load_Map) Map '{path}' lỗi: không có vị trí agent ('A')")
    if len(boxes) != len(goals): # số lượng box và goal có bằng nhau không
        raise ValueError(
            f"Debug(Load_Map) Map '{path}' lỗi: số box ({len(boxes)}) != số goal ({len(goals)})"
        )

    grid = {"walls": walls, "goals": goals, "width": width, "height": height} # 
    initial_state = GameState(agent=agent, boxes=frozenset(boxes))
    return grid, initial_state


"""Cái này dùng để in States ra cho debug"""
def print_state(state, grid):
    walls, goals = grid["walls"], grid["goals"]
    for r in range(grid["height"]):
        row = []
        for c in range(grid["width"]):
            pos = (r, c)
            if pos in walls:
                row.append("%")
            elif pos == state.agent:
                row.append("A")
            elif pos in state.boxes and pos in goals:
                row.append("C")
            elif pos in state.boxes:
                row.append("B")
            elif pos in goals:
                row.append("D")
            else:
                row.append(" ")
        print("".join(row))
