#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

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

# Greedy algorithm for cutlist optimization considering blade thickness
def greedy_cutlist(boards, parts, blade_thickness):
    parts = sorted(parts, key=lambda x: x[0] * x[1], reverse=True)
    solution = []
    
    for board in boards:
        board_width, board_height, board_quantity = board
        for _ in range(board_quantity):  # Consider board quantities
            remaining_space = [[0, 0, board_width, board_height]]  # [x1, y1, x2, y2]
            current_board_parts = []
            
            for part in parts[:]:
                part_width, part_height, quantity = part
                for _ in range(quantity):
                    for space in remaining_space:
                        x1, y1, x2, y2 = space
                        if part_width + blade_thickness <= (x2 - x1) and part_height + blade_thickness <= (y2 - y1):
                            # Allocate space considering blade thickness
                            current_board_parts.append((part_width, part_height, (x1, y1)))
                            remaining_space.remove(space)
                            remaining_space.append([x1 + part_width + blade_thickness, y1, x2, y2])  # Right space
                            remaining_space.append([x1, y1 + part_height + blade_thickness, x1 + part_width, y2])  # Bottom space
                            break
                    else:
                        continue
                    break
                else:
                    parts.remove(part)
            if current_board_parts:
                solution.append({'board': board, 'parts': current_board_parts})
    return solution

from matplotlib.backends.backend_pdf import PdfPages

# Visualization function with PDF export
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
        
        # Draw parts
        for part in board_data["parts"]:
            part_width, part_height, (x, y) = part
            ax[idx].add_patch(patches.Rectangle((x, y), part_width, part_height, edgecolor="blue", facecolor="lightblue"))
            ax[idx].text(x + part_width / 2, y + part_height / 2, f"{part_width}x{part_height}",
                         color="black", ha="center", va="center")
    
    # Show visualization in Streamlit
    st.pyplot(fig)
    
    # Export to PDF if requested
    if export_pdf:
        pdf_filename = "Cutlist_Optimization_Results.pdf"
        with PdfPages(pdf_filename) as pdf:
            for single_ax in ax:
                pdf.savefig(single_ax.figure)
        st.success(f"Graphs exported successfully to {pdf_filename}.")
        st.download_button(
            label="Download PDF",
            data=open(pdf_filename, "rb").read(),
            file_name=pdf_filename,
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
        solution = greedy_cutlist(boards, parts, blade_thickness)
        
        # Display results
        st.subheader("Optimization Results")
        for idx, board_data in enumerate(solution):
            st.write(f"**Board {idx + 1}:** {board_data['board'][0]} x {board_data['board'][1]} (Quantity: {board_data['board'][2]})")
            st.write("Parts placed:")
            for part in board_data["parts"]:
                part_width, part_height, (x, y) = part
                st.write(f" - {part_width} x {part_height} at position ({x}, {y})")
        
        # Visualize results and export if needed
        st.subheader("Visualization")
        visualize_solution(solution, export_pdf=export_pdf)
        
    except Exception as e:
        st.error(f"Error in optimization: {e}")

