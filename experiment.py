import time
import os
from core.map_loader import load_map
from core.search import uniform_cost_search, a_star_search, heuristic

def verify_heuristic_properties(initial_state, grid):
    """
    Yêu cầu 4: Kiểm chứng tính Admissible và Consistent của Heuristic
    - Admissible: h(n) <= h*(n) (chi phí ước lượng không vượt quá chi phí thực tế)
    - Consistent: h(n) <= c(n, a, n') + h(n')
    """
    print("\n" + "=" * 55)
    print("KIỂM CHỨNG TÍNH CHẤT HEURISTIC (YÊU CẦU 4)")
    print("=" * 55)
    
    h_start = heuristic(initial_state, grid)
    print(f"Giá trị Heuristic tại trạng thái ban đầu h(S0): {h_start}")
    
    # 1. Kiểm tra Admissibility thông qua chi phí tối ưu từ A*
    actions, optimal_cost, _ = a_star_search(initial_state, grid)
    if actions is not None:
        print(f"Chi phí tối ưu thực tế h*(S0): {optimal_cost}")
        is_admissible = h_start <= optimal_cost
        print(f"-> Kiểm tra h(S0) <= h*(S0): {h_start} <= {optimal_cost} => {is_admissible}")
        if is_admissible:
            print("=> KẾT LUẬN: Hàm Heuristic đạt tính ADMISSIBLE (hợp lệ/chấp nhận được).")
    
    # 2. Kiểm chứng Consistency trên các trạng thái kề
    from core.state import get_successors
    consistent_check = True
    for action, next_state, step_cost in get_successors(initial_state, grid):
        h_next = heuristic(next_state, grid)
        # Bất đẳng thức tam giác: h(n) <= c + h(n')
        if h_start > step_cost + h_next:
            consistent_check = False
            break
            
    print(f"-> Kiểm tra tính nhất quán h(n) <= c(n, a, n') + h(n'): {consistent_check}")
    if consistent_check:
        print("=> KẾT LUẬN: Hàm Heuristic đạt tính CONSISTENT (nhất quán).")
    print("=" * 55)


def run_experiment(map_path: str):
    print(f"\nBẮT ĐẦU THỰC NGHIỆM ĐỒ ÁN SOKOBAN (YÊU CẦU 3 & 4)")
    print(f"Đường dẫn bản đồ: {map_path}")
    print("=" * 55)
    
    if not os.path.exists(map_path):
        print(f"Lỗi: Không tìm thấy file map tại '{map_path}'!")
        return

    grid, initial_state = load_map(map_path)
    
    # -------------------------------------------------------------
    # 1. THỬ NGHIỆM VỚI A* SEARCH (Có Heuristic định hướng)
    # -------------------------------------------------------------
    print("\n[1] CHẠY A* SEARCH (Chebyshev Heuristic + Deadlock Pruning)")
    print("Đang tính toán...")
    start_time = time.perf_counter()
    actions_astar, cost_astar, nodes_astar = a_star_search(initial_state, grid)
    time_astar = time.perf_counter() - start_time
    
    if actions_astar is not None:
        print(f"   -> Kết quả: THÀNH CÔNG!")
        print(f"   -> Số bước đi (Cost): {cost_astar}")
        print(f"   -> Trạng thái đã duyệt (Space Complexity): {nodes_astar:,} nodes")
        print(f"   -> Thời gian chạy (Time Complexity): {time_astar:.4f} giây")
        print(f"   -> Các bước đi: {actions_astar[:10]} ... (tổng {len(actions_astar)} bước)")
    else:
        print("   -> Không tìm thấy lời giải!")

    # -------------------------------------------------------------
    # 2. THỬ NGHIỆM VỚI UNIFORM COST SEARCH (UCS)
    # -------------------------------------------------------------
    print("\n[2] CHẠY UNIFORM COST SEARCH (UCS)")
    print("Lưu ý: Với map nhiều hộp, UCS duyệt vét cạn sẽ cần nhiều thời gian và RAM.")
    start_time = time.perf_counter()
    actions_ucs, cost_ucs, nodes_ucs = uniform_cost_search(initial_state, grid)
    time_ucs = time.perf_counter() - start_time
    
    if actions_ucs is not None:
        print(f"   -> Kết quả: THÀNH CÔNG!")
        print(f"   -> Số bước đi (Cost): {cost_ucs}")
        print(f"   -> Trạng thái đã duyệt (Space Complexity): {nodes_ucs:,} nodes")
        print(f"   -> Thời gian chạy (Time Complexity): {time_ucs:.4f} giây")
    else:
        print("   -> Không tìm thấy lời giải!")

    # -------------------------------------------------------------
    # 3. SO SÁNH TRỰC DIỆN (Đưa vào slide thuyết trình)
    # -------------------------------------------------------------
    if actions_astar is not None and actions_ucs is not None:
        print("\n" + "=" * 55)
        print("BẢNG SO SÁNH ĐỘ PHỨC TẠP (CONTRASTING COMPLEXITY):")
        print("-" * 55)
        print(f"{'Tiêu chí':<25} | {'UCS':<12} | {'A*':<12}")
        print("-" * 55)
        print(f"{'Thời gian (giây)':<25} | {time_ucs:<12.4f} | {time_astar:<12.4f}")
        print(f"{'Bộ nhớ (Số nodes duyệt)':<25} | {nodes_ucs:<12} | {nodes_astar:<12}")
        print(f"{'Độ dài đường đi (Cost)':<25} | {cost_ucs:<12} | {cost_astar:<12}")
        print("=" * 55)

    # 4. Kiểm chứng tính chất Heuristic
    verify_heuristic_properties(initial_state, grid)


if __name__ == "__main__":
    # Ưu tiên tìm file example_map.txt ở thư mục gốc hoặc trong core/
    target_map = "core/example_map.txt" if os.path.exists("core/example_map.txt") else "example_map.txt"
    run_experiment(target_map)