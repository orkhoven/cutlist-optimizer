import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import mplcursors
import plotly.graph_objects as go


def optimize_cuts_with_subregions(boards, parts, blade_thickness):
    """
    Optimize cuts using 2D bin packing with subregion splitting.
    Args:
        boards: List of tuples [(width, height), ...] representing board dimensions.
        parts: List of tuples [(width, height), ...] representing part dimensions.
        blade_thickness: Space taken up by the cutting blade (in the same units as dimensions).

    Returns:
        List of boards with cuts assigned and remaining available space.
    """
    # Sort parts by area (largest to smallest)
    parts = sorted(parts, key=lambda x: x[0] * x[1], reverse=True)

    # Each board will hold cuts and remaining spaces
    packed_boards = [{"width": board[0], "height": board[1], "cuts": [], "spaces": [(0, 0, board[0], board[1])]} for board in boards]

    def try_to_place_part(part_width, part_height):
        """Try to place a part on the boards and return the result."""
        for board in packed_boards:
            for i, (x, y, space_width, space_height) in enumerate(board["spaces"]):
                if part_width <= space_width and part_height <= space_height:
                    # Place the cut
                    board["cuts"].append((x, y, part_width, part_height))

                    # Split the remaining space into sub-regions
                    new_spaces = [
                        (x + part_width + blade_thickness, y, space_width - part_width - blade_thickness, space_height),  # Right space
                        (x, y + part_height + blade_thickness, space_width, space_height - part_height - blade_thickness),  # Top space
                    ]

                    # Replace the used space with valid sub-regions
                    del board["spaces"][i]
                    board["spaces"].extend([s for s in new_spaces if s[2] > 0 and s[3] > 0])  # Keep only non-zero spaces
                    return True
        return False

    # Try to place all parts
    for part_width, part_height in parts:
        placed = try_to_place_part(part_width, part_height)
        if not placed:
            # Try rotating the part and place again
            placed = try_to_place_part(part_height, part_width)
        
        if not placed:
            st.error(f"Part {part_width}x{part_height} could not be placed!")

    return packed_boards


import io

def plot_board(board, board_index):
    """Plot a single board with cuts, including hover annotations."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot cuts (blue color)
    for i, cut in enumerate(board["cuts"]):
        ax.add_patch(plt.Rectangle((cut[0], cut[1]), cut[2], cut[3], color="blue"))
        ax.text(cut[0] + cut[2]/2, cut[1] + cut[3]/2, f"Cut {i+1}", ha="center", va="center", color="white")

    # Set labels and limits
    ax.set_title(f"Board {board_index+1}: {board['width']}x{board['height']}")
    ax.set_xlim(0, board['width'])
    ax.set_ylim(0, board['height'])
    ax.set_xlabel('Width')
    ax.set_ylabel('Height')

    # Add hover functionality with annotations
    mplcursors.cursor(hover=True).connect(
        "add", lambda sel: sel.annotation.set_text(
            f"Cut {sel.index+1}: {board['cuts'][sel.index][2]}x{board['cuts'][sel.index][3]}"
        )
    )
    
    # Save the figure as a PDF
    pdf_buffer = io.BytesIO()
    fig.savefig(pdf_buffer, format="pdf")
    pdf_buffer.seek(0)
    
    return fig, pdf_buffer

def visualize_boards(boards):
    """Visualize all boards with cuts and provide a PDF download option."""
    for i, board in enumerate(boards):
        fig, pdf_buffer = plot_board(board, i)
        st.pyplot(fig)
        
        # Add download button for the PDF
        st.download_button(
            label=f"Download Board {i+1} as PDF",
            data=pdf_buffer,
            file_name=f"board_{i+1}.pdf",
            mime="application/pdf"
        )

# Streamlit App
st.title("Cut List Optimizer with Hover Annotations")

st.sidebar.header("Input Parameters")
board_input = st.sidebar.text_area(
    "Enter boards (widthxheight):", "100x50\n200x100"
)
boards = [tuple(map(int, b.split("x"))) for b in board_input.split("\n") if b.strip()]

parts_input = st.sidebar.text_area(
    "Enter parts (widthxheight):", "20x10\n20x10\n20x10\n20x10\n50x50\n50x50"
)
parts = [tuple(map(int, p.split("x"))) for p in parts_input.split("\n") if p.strip()]

blade_thickness = st.sidebar.number_input(
    "Blade Thickness (mm):", min_value=0, value=2, step=1
)

if st.button("Optimize Cuts"):
    # Perform the optimization
    packed_boards = optimize_cuts_with_subregions(boards, parts, blade_thickness)
    
    # Visualize the packed boards and offer PDF download
    visualize_boards(packed_boards)
