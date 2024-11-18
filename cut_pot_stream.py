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
    remaining_boards = [{"width": bw, "height": bh, "cuts": []} for bw, bh in boards]
    for cut_width, cut_height in cuts:
        placed = False
        for board in remaining_boards:
            if cut_width <= board["width"] and cut_height <= board["height"]:
                # Place cut
                board["cuts"].append((cut_width, cut_height, len(board["cuts"])))
                # Update board space
                board["width"] -= cut_width + blade_thickness
                placed = True
                break
        if not placed:
            st.error(f"Could not place cut {cut_width}x{cut_height}")
    return remaining_boards

def visualize_cuts(boards):
    """Generate a visualization of the boards and cuts."""
    fig, ax = plt.subplots(figsize=(12, len(boards) * 4))
    y_offset = 0
    colors = plt.cm.tab20.colors

    for i, board in enumerate(boards):
        # Draw board
        ax.add_patch(Rectangle((0, y_offset), board["width"], board["height"], edgecolor='black', fill=False, linewidth=2))
        for j, (cw, ch, _) in enumerate(board["cuts"]):
            color = colors[j % len(colors)]
            rect = Rectangle((0, y_offset), cw, ch, facecolor=color, edgecolor='black', alpha=0.7)
            ax.add_patch(rect)
            ax.text(cw / 2, y_offset + ch / 2, f"{cw}x{ch}", ha="center", va="center", fontsize=8)
            y_offset += ch  # Adjust offset for next cut

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
        optimized_boards = optimize_cuts(boards, parts, blade_thickness)
        fig = visualize_cuts(optimized_boards)
        st.pyplot(fig)

        if create_pdf:
            pdf_path = export_to_pdf(fig)
            with open(pdf_path, "rb") as f:
                st.download_button("Download PDF", f, file_name="optimized_cuts.pdf")

if __name__ == "__main__":
    main()
