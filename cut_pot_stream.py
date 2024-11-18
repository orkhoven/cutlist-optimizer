import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from fpdf import FPDF

def parse_input(input_text):
    """Parse user input for dimensions and quantities."""
    try:
        lines = input_text.strip().split("\n")
        parsed = [(float(line.split(",")[0]), float(line.split(",")[1]), int(line.split(",")[2])) for line in lines]
        return [(w, h) for w, h, qty in parsed for _ in range(qty)]
    except:
        st.error("Invalid format. Use: width,height,quantity (one per line).")
        return []

def optimize_cuts(boards, cuts, blade_thickness):
    """Optimize the cutting process."""
    remaining_boards = boards.copy()
    optimized_cuts = []

    for cut_width, cut_height in cuts:
        placed = False
        for i, (board_width, board_height) in enumerate(remaining_boards):
            if cut_width <= board_width and cut_height <= board_height:
                optimized_cuts.append((cut_width, cut_height, i))
                # Update board dimensions
                remaining_boards[i] = (
                    board_width - cut_width - blade_thickness, board_height
                )
                placed = True
                break

        if not placed:
            st.error(f"Could not place cut {cut_width}x{cut_height}")

    return optimized_cuts

def visualize_cuts(boards, optimized_cuts):
    """Generate a visualization of the boards and cuts."""
    fig, ax = plt.subplots(figsize=(10, 8))
    colors = plt.cm.tab20.colors

    for i, (board_width, board_height) in enumerate(boards):
        # Draw the board
        ax.add_patch(Rectangle((0, -i * (board_height + 10)), board_width, board_height, edgecolor='black', fill=False))

        # Draw cuts on this board
        offset_x, offset_y = 0, -i * (board_height + 10)
        for cut_width, cut_height, board_index in optimized_cuts:
            if board_index == i:
                ax.add_patch(Rectangle((offset_x, offset_y), cut_width, cut_height, facecolor=colors[i % len(colors)], edgecolor='black', alpha=0.6))
                ax.text(offset_x + cut_width / 2, offset_y + cut_height / 2, f"{cut_width}x{cut_height}", ha="center", va="center", fontsize=8)
                offset_x += cut_width  # Shift for next cut

    ax.set_xlim(0, max(board[0] for board in boards))
    ax.set_ylim(-len(boards) * (max(board[1] for board in boards) + 10), 0)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig

def export_to_pdf(fig):
    """Export the Matplotlib figure to a PDF."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Optimized Cuts Visualization", ln=True, align="C")

    fig.savefig("visualization.png", dpi=300, bbox_inches="tight")
    pdf.image("visualization.png", x=10, y=30, w=190)
    pdf.output("optimized_cuts.pdf")
    return "optimized_cuts.pdf"

def main():
    st.title("Cut List Optimizer")

    st.sidebar.header("Input Parameters")
    board_input = st.sidebar.text_area(
        "Enter boards (width,height,quantity):", "100,50,2\n200,100,1"
    )
    boards = parse_input(board_input)

    parts_input = st.sidebar.text_area(
        "Enter parts (width,height,quantity):", "20,10,4\n50,50,2"
    )
    parts = parse_input(parts_input)

    blade_thickness = st.sidebar.selectbox(
        "Blade Thickness:", options=[2, 3, 4], format_func=lambda x: f"{x} mm"
    )

    create_pdf = st.sidebar.checkbox("Create PDF")

    if st.button("Optimize Cuts"):
        optimized_cuts = optimize_cuts(boards, parts, blade_thickness)
        fig = visualize_cuts(boards, optimized_cuts)
        st.pyplot(fig)

        if create_pdf:
            pdf_path = export_to_pdf(fig)
            with open(pdf_path, "rb") as f:
                st.download_button("Download PDF", f, file_name="optimized_cuts.pdf")

if __name__ == "__main__":
    main()
