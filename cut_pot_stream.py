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
                if part_quantity > 0:  # Check if there are parts available
                    # Adjust for blade thickness
                    part_width -= blade_thickness
                    part_height -= blade_thickness

                    # Check if part fits on the board
                    if part_width <= available_width and part_height <= available_height:
                        # Place the part on the board
                        board_usage["cuts"].append({"part": (part_width, part_height)})

                        # Reduce available space and update part quantity
                        available_height -= part_height  # Assume parts are placed vertically
                        parts[idx] = (part_width, part_height, part_quantity - 1)  # Update part quantity
                else:
                    continue  # Skip if no quantity left for this part
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
                x, y = 0, 0  # Position logic can be enhanced for better fitting
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

# Debugging boards input
st.write("Parsed boards:", boards)

# Add input for parts directly
parts_input = st.sidebar.text_area(
    "Enter parts (width x height x quantity, e.g., 50x50x2, 40x80x1):",
    "50x50x2, 40x80x1"
)

# Parsing parts input
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

# Debugging parts input
st.write("Parsed parts:", parts)
st.sidebar.subheader("Blade Thickness")
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

