#!/usr/bin/env python
# coding: utf-8

# In[ ]:


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

def optimize_cuts(boards, parts, blade_thickness):
    """
    Optimizes the cutting of parts from boards using a 2D bin-packing approach.
    Minimizes waste and maximizes board utilization.
    
    Args:
        boards (list): List of boards as (width, height, quantity).
        parts (list): List of parts as (width, height, quantity).
        blade_thickness (int): Thickness of the blade in mm.
    
    Returns:
        list: A list of boards with detailed cut configurations.
    """
    # Validate inputs
    if not all(len(board) == 3 for board in boards):
        raise ValueError("Each board must be a tuple of (width, height, quantity).")
    if not all(len(part) == 3 for part in parts):
        raise ValueError("Each part must be a tuple of (width, height, quantity).")
    
    # Expand parts based on their quantities
    expanded_parts = []
    for part in parts:
        expanded_parts.extend([(part[0], part[1])] * part[2])
    
    # Sort parts by area in descending order for better packing
    expanded_parts.sort(key=lambda x: x[0] * x[1], reverse=True)

    # Initialize solution
    solution = []

    # Process each board
    for board in boards:
        board_width, board_height, board_quantity = board
        board_usage = []

        for _ in range(board_quantity):
            current_board = {"width": board_width, "height": board_height, "cuts": []}
            spaces = [{"x": 0, "y": 0, "width": board_width, "height": board_height}]

            remaining_parts = []

            # Try to fit each part into available spaces
            for part in expanded_parts:
                part_width, part_height = part
                placed = False

                for space in spaces:
                    if (part_width + blade_thickness <= space["width"] and
                        part_height + blade_thickness <= space["height"]):
                        # Place part and update spaces
                        current_board["cuts"].append({
                            "x": space["x"],
                            "y": space["y"],
                            "width": part_width,
                            "height": part_height
                        })

                        # Update remaining space
                        new_spaces = [
                            {
                                "x": space["x"] + part_width + blade_thickness,
                                "y": space["y"],
                                "width": space["width"] - part_width - blade_thickness,
                                "height": space["height"]
                            },
                            {
                                "x": space["x"],
                                "y": space["y"] + part_height + blade_thickness,
                                "width": part_width,
                                "height": space["height"] - part_height - blade_thickness
                            }
                        ]

                        spaces.remove(space)
                        spaces.extend([s for s in new_spaces if s["width"] > 0 and s["height"] > 0])
                        placed = True
                        break

                if not placed:
                    remaining_parts.append(part)

            # Add board usage details
            board_usage.append(current_board)
            expanded_parts = remaining_parts

            if not remaining_parts:
                break

        solution.append({"board": (board_width, board_height), "details": board_usage})

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
        
        # Check if there are cuts in the current board usage
        cuts = board_data["details"][0]["cuts"] if len(board_data["details"]) > 0 else []

        # Draw cuts (parts)
        for cut in cuts:
            part_width, part_height = cut["width"], cut["height"]
            x, y = cut["x"], cut["y"]
            ax[idx].add_patch(patches.Rectangle((x, y), part_width, part_height, edgecolor="blue", facecolor="lightblue"))
            ax[idx].text(x + part_width / 2, y + part_height / 2, f"{part_width}x{part_height}",
                         color="black", ha="center", va="center")
    
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
    tuple(map(int, b.strip().split("x")))
    for b in boards_input.split(",")
]

st.sidebar.subheader("Parts")
parts_input = st.sidebar.text_area(
    "Enter parts (width x height x quantity, e.g., 50x50x2, 40x80x1):",
    "50x50x2, 40x80x1"
)
parts = [
    tuple(map(int, p.strip().split("x")))
    for p in parts_input.split(",")
]

# Blade thickness selection
blade_thickness = st.sidebar.selectbox("Blade Thickness (mm):", [2, 3, 4])

export_pdf = st.sidebar.checkbox("Export results as PDF")

if st.sidebar.button("Optimize"):
    try:
        # Run the optimizer
        solution = optimize_cuts(boards, parts, blade_thickness)
        
        # Display results
        st.subheader("Optimization Results")
        for idx, board_data in enumerate(solution):
            st.write(f"**Board {idx + 1}:** {board_data['board'][0]} x {board_data['board'][1]} (Quantity: {board_data['board'][2]})")
            st.write("Parts placed:")
            if len(board_data["details"]) > 0:
                for cut in board_data["details"][0]["cuts"]:
                    part_width, part_height, (x, y) = cut["width"], cut["height"], (cut["x"], cut["y"])
                    st.write(f" - {part_width} x {part_height} at position ({x}, {y})")
            else:
                st.write("No parts placed.")
        
        # Visualize results and export if needed
        st.subheader("Visualization")
        visualize_solution(solution, export_pdf=export_pdf)
        
    except Exception as e:
        st.error(f"Error in optimization: {e}")

