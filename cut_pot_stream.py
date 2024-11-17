import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pulp import LpMaximize, LpProblem, LpVariable, lpSum
from io import BytesIO
from matplotlib.backends.backend_pdf import PdfPages

# Configure Streamlit page
st.set_page_config(
    page_title="Cutlist Optimizer",
    page_icon="🪚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Add custom CSS for background color and styling
st.markdown(
    """
    <style>
    body {
        background-color: #f7f9fc;
        color: #333;
    }
    .sidebar .sidebar-content {
        background-color: #eef3f7;
    }
    .stButton>button {
        background-color: #2b8a3e;
        color: white;
        border: none;
        padding: 0.5em 1em;
        font-size: 16px;
        border-radius: 5px;
        cursor: pointer;
    }
    .stButton>button:hover {
        background-color: #276a31;
    }
    h1, h2, h3 {
        color: #2b6777;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def optimize_cuts(boards, parts, blade_thickness):
    """
    Optimizes the cutting of parts from boards using a bin-packing approach with linear programming.
    
    Args:
        boards (list): List of boards as (width, height, quantity).
        parts (list): List of parts as (width, height, quantity).
        blade_thickness (int): Thickness of the blade in mm.
    
    Returns:
        list: A list of boards with detailed cut configurations.
    """
    # Initialize optimization problem
    prob = LpProblem("Cutting Optimization", LpMaximize)

    # Flatten parts based on their quantities
    expanded_parts = []
    for part in parts:
        expanded_parts.extend([(part[0], part[1])] * part[2])

    # Create variables for each part-board combination
    part_board_vars = {}
    for idx, (board_width, board_height, board_quantity) in enumerate(boards):
        for part in expanded_parts:
            part_width, part_height = part
            for i in range(board_quantity):
                var_name = f"part_{expanded_parts.index(part)}_board_{idx}_slot_{i}"
                part_board_vars[var_name] = LpVariable(var_name, cat="Binary")

    # Objective function: Maximize the number of cuts placed on boards
    prob += lpSum(part_board_vars.values()), "Total Cuts"

    # Constraints to ensure parts are placed on available boards
    for part_idx, (part_width, part_height) in enumerate(expanded_parts):
        part_quantity = parts[part_idx][2]
        prob += lpSum(part_board_vars[f"part_{part_idx}_board_{board_idx}_slot_{i}"]
                      for board_idx, (board_width, board_height, board_quantity) in enumerate(boards)
                      for i in range(board_quantity)) == part_quantity, f"Part_{part_idx}_placed"

    # Constraints to ensure parts fit on boards
    for board_idx, (board_width, board_height, board_quantity) in enumerate(boards):
        for i in range(board_quantity):
            for part_idx, (part_width, part_height) in enumerate(expanded_parts):
                for var_name in part_board_vars:
                    # Check if part fits within the board size and blade thickness
                    if part_width + blade_thickness <= board_width and part_height + blade_thickness <= board_height:
                        prob += part_board_vars[var_name] <= 1, f"Fit_Constraint_{var_name}"

    # Solve the problem
    prob.solve()

    # Extract the solution and build the output
    solution = []
    for board_idx, (board_width, board_height, board_quantity) in enumerate(boards):
        board_usage = {"board": (board_width, board_height), "cuts": []}
        for i in range(board_quantity):
            for part_idx, (part_width, part_height) in enumerate(expanded_parts):
                for var_name in part_board_vars:
                    if part_board_vars[var_name].varValue == 1:
                        # Parse part and add the cut to the board usage
                        part_idx = int(var_name.split("_")[1])
                        cut_info = {"part": expanded_parts[part_idx], "slot": i}
                        board_usage["cuts"].append(cut_info)
        solution.append(board_usage)

    return solution


# Visualization with PDF export
def visualize_solution(solution, export_pdf=False):
    fig, ax = plt.subplots(len(solution), 1, figsize=(8, 5 * len(solution)))
    if len(solution) == 1:
        ax = [ax]

    for idx, board_data in enumerate(solution):
        board_width, board_height, _ = board_data['board']
        ax[idx].set_xlim(0, board_width)
        ax[idx].set_ylim(0, board_height)
        ax[idx].set_title(f"Board {idx + 1}: {board_width} x {board_height}")
        ax[idx].set_aspect('equal')
        ax[idx].invert_yaxis()
        ax[idx].set_xlabel("Width")
        ax[idx].set_ylabel("Height")
        
        # Draw board
        ax[idx].add_patch(patches.Rectangle((0, 0), board_width, board_height, edgecolor="black", fill=False, lw=2))
        
        # Draw cuts (parts placed on board)
        cuts = board_data["cuts"] if len(board_data["cuts"]) > 0 else []
        
        if cuts:
            for cut in cuts:
                part_width, part_height = cut["part"]
                x, y = cut["slot"], 0  # Example, modify slot logic to position cuts better
                ax[idx].add_patch(patches.Rectangle((x, y), part_width, part_height, edgecolor="blue", facecolor="lightblue"))
                ax[idx].text(x + part_width / 2, y + part_height / 2, f"{part_width}x{part_height}",
                             color="black", ha="center", va="center")
        else:
            ax[idx].text(board_width / 2, board_height / 2, "No parts placed", ha="center", va="center", fontsize=12, color="red")
    
    st.pyplot(fig)
    
    if export_pdf:
        pdf_buffer = BytesIO()
        with PdfPages(pdf_buffer) as pdf:
            for single_ax in ax:
                pdf.savefig(single_ax.figure)
        pdf_buffer.seek(0)
        st.download_button(
            label="Download PDF",
            data=pdf_buffer,
            file_name="Cutlist_Optimization_Results.pdf",
            mime="application/pdf",
        )

# Streamlit App
st.title("Cutlist Optimizer 🪚")

st.sidebar.header("Inputs")
st.sidebar.subheader("Boards")
boards_input = st.sidebar.text_area(
    "Enter board dimensions and quantities (e.g., 100x200x1, 150x150x2):", "100x200x1, 150x150x2"
)
boards = [
    tuple(map(int, b.strip().split("x"))) if b.strip() else None
    for b in boards_input.split(",")
]

st.sidebar.subheader("Parts")
parts_input = st.sidebar.text_area(
    "Enter parts (width x height x quantity, e.g., 50x50x2, 40x80x1):",
    "50x50x2, 40x80x1"
)

# Safely parse the parts input, ensuring no invalid parts are added
parts = []
for p in parts_input.split(","):
    p = p.strip()
    if p:
        try:
            parts.append(tuple(map(int, p.split("x"))))
        except ValueError:
            st.error(f"Invalid part input: {p}. Please use the format 'width x height x quantity'.")
            continue

# Now, parts should be a list of valid tuples, or empty if no valid inputs were found

blade_thickness = st.sidebar.selectbox("Blade Thickness (mm):", [2, 3, 4])

export_pdf = st.sidebar.checkbox("Export results as PDF")

if st.sidebar.button("Optimize"):
    try:
        solution = optimize_cuts(boards, parts, blade_thickness)
        
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
