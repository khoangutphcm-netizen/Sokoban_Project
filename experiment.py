import time
import os
from core.map_loader import load_map
from search.ucs import uniform_cost_search
from search.astar import a_star_search
from search.heuristic import hungarian_heuristic

def verify_heuristic_properties(initial_state, grid, optimal_cost):
    print("\n" + "=" * 60)
    print("KIỂM CHỨNG TÍNH CHẤT HEURISTIC (YÊU CẦU 4)")
    print("=" * 60)
    h_start = hungarian_heuristic(initial_state, grid)
    print(f"Giá trị Heuristic ban đầu h(S0): {h_start}")
    print(f"Chi phí tối ưu thực tế h*(S0) : {optimal_cost}")
    
    is_admissible = h_start <= optimal_cost
    print(f"-> Kiểm tra h(S0) <= h*(S0): {h_start} <= {optimal_cost} => {is_admissible}")
    if is_admissible:
        print("=> KẾT LUẬN 1: Hàm Heuristic đạt tính ADMISSIBLE (cận dưới an toàn).")
    
    from core.state import get_successors
    consistent_check = True
    for action, next_state, step_cost in get_successors(initial_state, grid):
        h_next = hungarian_heuristic(next_state, grid)
        if h_start > step_cost + h_next:
            consistent_check = False
            break
            
    print(f"-> Kiểm tra tính nhất quán h(n) <= c(n, a, n') + h(n'): {consistent_check}")
    if consistent_check:
        print("=> KẾT LUẬN 2: Hàm Heuristic đạt tính CONSISTENT (nhất quán).")
    print("=" * 60)

def run_experiment(map_path: str):
    print(f"\n" + "=" * 60)
    print(f"BÁO CÁO THỰC NGHIỆM TÌM KIẾM SOKOBAN (TASK 1)")
    print(f"Đường dẫn map: {map_path}")
    print("=" * 60)
    
    if not os.path.exists(map_path):
        print(f"Lỗi: Không tìm thấy file tại '{map_path}'")
        return

    grid, initial_state = load_map(map_path)
    
    # 1. Thực nghiệm A* Search
    print("\n[1] CHẠY A* SEARCH (Hungarian Heuristic + BFS Distance)")
    start_time = time.perf_counter()
    actions_astar, cost_astar, nodes_astar = a_star_search(initial_state, grid)
    time_astar = time.perf_counter() - start_time
    
    if actions_astar is not None:
        print(f"   -> Kết quả: THÀNH CÔNG")
        print(f"   -> Chi phí tối ưu (Cost): {cost_astar}")
        print(f"   -> Không gian (Nodes đã duyệt): {nodes_astar:,} nodes")
        print(f"   -> Thời gian tính toán: {time_astar:.4f} giây")
        print(f"   -> Chuỗi hành động ({len(actions_astar)} bước): {actions_astar[:8]}...")
    else:
        print("   -> Kết quả: Không tìm thấy lời giải!")

    # 2. Thực nghiệm Uniform Cost Search (UCS)
    print("\n[2] CHẠY UNIFORM COST SEARCH (UCS)")
    start_time = time.perf_counter()
    actions_ucs, cost_ucs, nodes_ucs = uniform_cost_search(initial_state, grid)
    time_ucs = time.perf_counter() - start_time
    
    if actions_ucs is not None:
        print(f"   -> Kết quả: THÀNH CÔNG")
        print(f"   -> Chi phí tối ưu (Cost): {cost_ucs}")
        print(f"   -> Không gian (Nodes đã duyệt): {nodes_ucs:,} nodes")
        print(f"   -> Thời gian tính toán: {time_ucs:.4f} giây")
    else:
        print("   -> Kết quả: Không tìm thấy lời giải!")

    # 3. So sánh đối chiếu trực diện
    if actions_astar is not None and actions_ucs is not None:
        print("\n" + "=" * 60)
        print(f"{'Tiêu chí đánh giá':<25} | {'UCS':<14} | {'A* (Hungarian)':<15}")
        print("-" * 60)
        print(f"{'Thời gian thực thi (s)':<25} | {time_ucs:<14.4f} | {time_astar:<15.4f}")
        print(f"{'Bộ nhớ (Số nodes duyệt)':<25} | {nodes_ucs:<14} | {nodes_astar:<15}")
        print(f"{'Độ dài đường đi (Cost)':<25} | {cost_ucs:<14} | {cost_astar:<15}")
        print("=" * 60)

    # 4. Kiểm chứng tính chất Heuristic
    if actions_astar is not None:
        verify_heuristic_properties(initial_state, grid, cost_astar)

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    target_map = os.path.join(base_dir, "example_map.txt")
    run_experiment(target_map)