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
    except Exception:
        st.error("Invalid format. Use: width,height,quantity (one per line).")
        return []

def optimize_cuts(boards, cuts, blade_thickness):
    """Optimize the cutting process."""
    remaining_boards = [{"width": bw, "height": bh, "cuts": []} for bw, bh in boards]
    for cut_width, cut_height in cuts:
        placed = False
        for board in remaining_boards:
            if cut_width <= board["width"] and cut_height <= board["height"]:
                # Place cut
                board["cuts"].append((cut_width, cut_height))
                board["width"] -= cut_width + blade_thickness
                placed = True
                break
        if not placed:
            st.error(f"Could not place cut {cut_width}x{cut_height}")
    return remaining_boards

def visualize_cuts(boards):
    """Generate a visualization of the boards and cuts."""
    # Set maximum figure size
    max_height = 15
    num_boards = len(boards)
    fig_height = min(max_height, 3 * num_boards)
    
    fig, ax = plt.subplots(figsize=(10, fig_height))
    colors = plt.cm.tab20.colors

    y_offset = 0
    for i, board in enumerate(boards):
        board_width, board_height = board["width"], board["height"]
        
        # Draw the board
        ax.add_patch(Rectangle((0, y_offset), board_width, board_height, edgecolor="black", fill=False, linewidth=2))
        ax.text(5, y_offset + board_height - 5, f"Board {i + 1}", fontsize=10, color="black")
        
        # Draw cuts
        x_pos = 0
        for j, (cut_width, cut_height) in enumerate(board["cuts"]):
            color = colors[j % len(colors)]
            rect = Rectangle((x_pos, y_offset), cut_width, cut_height, facecolor=color, edgecolor="black", alpha=0.7)
            ax.add_patch(rect)
            ax.text(x_pos + cut_width / 2, y_offset + cut_height / 2, f"{cut_width}x{cut_height}", ha="center", va="center", fontsize=8)
            x_pos += cut_width + 2  # Add blade thickness
        y_offset += board_height + 10  # Update y position for the next board

    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")
    plt.tight_layout()
    return fig

def export_to_pdf(fig):
    """Export the Matplotlib figure to a PDF."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Optimized Cuts Visualization", ln=True, align="C")

    fig.savefig("visualization.png", dpi=72, bbox_inches="tight")
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
        optimized_boards = optimize_cuts(boards, parts, blade_thickness)
        fig = visualize_cuts(optimized_boards)
        st.pyplot(fig)

        if create_pdf:
            pdf_path = export_to_pdf(fig)
            with open(pdf_path, "rb") as f:
                st.download_button("Download PDF", f, file_name="optimized_cuts.pdf")

if __name__ == "__main__":
    main()
