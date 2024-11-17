import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from io import BytesIO
from matplotlib.backends.backend_pdf import PdfPages

# Configure Streamlit page
st.set_page_config(
    page_title="Cutlist Optimizer",
    page_icon="🪚",
    layout="wide",
    initial_sidebar_state="expanded",
)

def greedy_cutting(boards, parts, blade_thickness):
    """
    A greedy approach to optimize the cutting of parts from boards.
    
    Args:
        boards (list): List of boards (width, height, quantity).
        parts (list): List of parts (width, height, quantity).
        blade_thickness (int): Thickness of the blade.
    
    Returns:
        list: A list of boards with detailed cut configurations.
    """
    solution = []
    for board_width, board_height, board_quantity in boards:
        for _ in range(board_quantity):
            board_usage = {"board": (board_width, board_height), "cuts": []}
            available_width = board_width
            available_height = board_height
            for idx, (part_width, part_height, part_quantity) in enumerate(parts):
                st.write(f"Checking part {idx}: {part_width}x{part_height} with quantity {part_quantity}")

                if part_quantity > 0:  # Check if there are parts available
                    # Adjust for blade thickness
                    part_width -= blade_thickness
                    part_height -= blade_thickness
                    st.write(f"Adjusted part: {part_width}x{part_height}")

                    # Check if part fits on the board
                    if part_width <= available_width and part_height <= available_height:
                        # Place the part on the board
                        board_usage["cuts"].append({"part": (part_width, part_height)})
                        st.write(f"Placed part: {part_width}x{part_height} on board")

                        # Reduce available space and update part quantity
                        available_height -= part_height  # Assume parts are placed vertically
                        parts[idx] = (part_width, part_height, part_quantity - 1)  # Update part quantity
                        st.write(f"Remaining quantity for part {idx}: {part_quantity - 1}")
                else:
                    st.write(f"Skipping part {idx}: No quantity left")
                    continue  # Skip if no quantity left for this part
            solution.append(board_usage)
    return solution


# Streamlit App
st.title("Cutlist Optimizer 🪚")

st.sidebar.header("Inputs")
st.sidebar.subheader("Boards")
boards_input = st.sidebar.text_area(
    "Enter board dimensions and quantities (e.g., 100x200x1, 150x150x2):", "100x200x1, 150x150x2"
)

# Parsing boards input
boards = []
for b in boards_input.split(","):
    b = b.strip()
    if b:
        try:
            values = list(map(int, b.split("x")))
            if len(values) == 3:
                boards.append(tuple(values))  # Ensure exactly 3 values: width, height, quantity
            else:
                st.error(f"Invalid board input: '{b}'. Please use the format 'width x height x quantity'.")
        except ValueError:
            st.error(f"Invalid board input: '{b}'. Ensure all values are integers and in the correct format.")
            continue

# Parsing parts input
parts_input = st.sidebar.text_area(
    "Enter parts (width x height x quantity, e.g., 50x50x2, 40x80x1):",
    "50x50x2, 40x80x1"
)

parts = []
for p in parts_input.split(","):
    p = p.strip()
    if p:
        try:
            values = list(map(int, p.split("x")))
            if len(values) == 3:
                parts.append(tuple(values))  # Ensure exactly 3 values: width, height, quantity
            else:
                st.error(f"Invalid part input: '{p}'. Please use the format 'width x height x quantity'.")
        except ValueError:
            st.error(f"Invalid part input: '{p}'. Ensure all values are integers and in the correct format.")
            continue

st.write("Parsed boards:", boards)
st.write("Parsed parts:", parts)

blade_thickness = st.sidebar.selectbox("Blade Thickness (mm):", [2, 3, 4])
export_pdf = st.sidebar.checkbox("Export results as PDF")

if st.sidebar.button("Optimize"):
    try:
        solution = greedy_cutting(boards, parts, blade_thickness)

        # Display results
        st.subheader("Optimization Results")
        for idx, board_data in enumerate(solution):
            st.write(f"**Board {idx + 1}:** {board_data['board'][0]} x {board_data['board'][1]}")
            st.write(f"Parts placed: {len(board_data['cuts'])}")
            if not board_data["cuts"]:
                st.write("No parts placed.")

        visualize_solution(solution, export_pdf)

    except Exception as e:
        st.error(f"An error occurred during optimization: {e}")
