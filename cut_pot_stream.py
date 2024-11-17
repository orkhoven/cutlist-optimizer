import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from io import BytesIO
from matplotlib.backends.backend_pdf import PdfPages

# Set up Streamlit page
st.set_page_config(page_title="Cutlist Optimizer", page_icon="🪚")

# Helper function to parse inputs
def parse_input(input_string):
    items = input_string.strip().split(",")
    parsed_items = []
    for item in items:
        try:
            dimensions = list(map(int, item.split("x")))
            if len(dimensions) == 3:
                parsed_items.append(tuple(dimensions))
            else:
                st.error(f"Invalid input: '{item}', expected 3 values.")
        except ValueError:
            st.error(f"Invalid input: '{item}', please provide integers in the format widthxheightxquantity.")
    return parsed_items

# Greedy optimization function
def greedy_cutting(boards, parts, blade_thickness):
    solution = []
    for board_width, board_height, board_quantity in boards:
        for _ in range(board_quantity):
            board_usage = {"board": (board_width, board_height), "cuts": []}
            available_width = board_width
            available_height = board_height
            for part_width, part_height, part_quantity in sorted(parts, key=lambda x: x[0] * x[1], reverse=True):
                part_width -= blade_thickness
                part_height -= blade_thickness
                if part_width <= available_width and part_height <= available_height and part_quantity > 0:
                    board_usage["cuts"].append({"part": (part_width, part_height)})
                    available_height -= part_height
                    parts = [(pw, ph, pq-1) if (pw == part_width and ph == part_height) else (pw, ph, pq) for pw, ph, pq in parts]
            solution.append(board_usage)
    return solution

# Visualization function
def visualize_solution(solution, export_pdf=False):
    fig, ax = plt.subplots(len(solution), 1, figsize=(8, 5 * len(solution)))
    if len(solution) == 1:
        ax = [ax]

    for idx, board_data in enumerate(solution):
        board_width, board_height, _ = board_data["board"]
        ax[idx].set_xlim(0, board_width)
        ax[idx].set_ylim(0, board_height)
        ax[idx].set_title(f"Board {idx + 1}: {board_width} x {board_height}")
        ax[idx].set_aspect('equal')
        ax[idx].invert_yaxis()
        
        ax[idx].add_patch(patches.Rectangle((0, 0), board_width, board_height, edgecolor="black", fill=False, lw=2))
        
        cuts = board_data["cuts"]
        y_offset = 0
        for cut in cuts:
            part_width, part_height = cut["part"]
            ax[idx].add_patch(patches.Rectangle((0, y_offset), part_width, part_height, edgecolor="blue", facecolor="lightblue"))
            ax[idx].text(part_width / 2, y_offset + part_height / 2, f"{part_width}x{part_height}",
                         color="black", ha="center", va="center")
            y_offset += part_height  # Stack parts vertically
        
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

# Streamlit app layout
st.title("Cutlist Optimizer 🪚")

st.sidebar.header("Inputs")
st.sidebar.subheader("Boards")
boards_input = st.sidebar.text_area(
    "Enter board dimensions and quantities (e.g., 100x200x1, 150x150x2):", "100x200x1, 150x150x2"
)

boards = parse_input(boards_input)

st.sidebar.subheader("Parts")
parts_input = st.sidebar.text_area(
    "Enter parts (width x height x quantity, e.g., 50x50x2, 40x80x1):", "50x50x2, 40x80x1"
)

parts = parse_input(parts_input)

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
