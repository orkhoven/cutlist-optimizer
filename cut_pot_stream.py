import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import pandas as pd
from fpdf import FPDF

def parse_input(input_text):
    """Parse user input for dimensions and quantities."""
    try:
        lines = input_text.strip().split("\n")
        parsed = [(float(line.split(",")[0]), float(line.split(",")[1]), int(line.split(",")[2])) for line in lines]
        return parsed
    except Exception as e:
        st.error("Error parsing input. Ensure it is in the format: width,height,quantity (one per line).")
        return []

def optimize_cuts(boards, cuts, blade_thickness):
    optimized_cuts = []
    remaining_boards = boards.copy()

    for cut in cuts:
        cut_width, cut_height = cut
        placed = False
        for board in remaining_boards:
            board_width, board_height = board

            if cut_width <= board_width and cut_height <= board_height:
                optimized_cuts.append((cut_width, cut_height, board))
                remaining_boards.remove(board)
                remaining_boards.append(
                    (board_width - cut_width - blade_thickness, board_height)
                )
                remaining_boards.append(
                    (cut_width, board_height - cut_height - blade_thickness)
                )
                placed = True
                break

        if not placed:
            st.error(f"Could not place cut {cut_width}x{cut_height}")

    return optimized_cuts

def visualize_cuts(boards, optimized_cuts):
    fig, axs = plt.subplots(len(boards), 1, figsize=(8, len(boards) * 4))
    if len(boards) == 1:
        axs = [axs]

    for ax, board in zip(axs, boards):
        board_width, board_height = board
        ax.set_xlim(0, board_width)
        ax.set_ylim(0, board_height)
        ax.set_title(f"Board {board_width}x{board_height}")
        ax.set_aspect('equal', adjustable='box')
        ax.set_xticks(range(0, int(board_width) + 1, 10))
        ax.set_yticks(range(0, int(board_height) + 1, 10))
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)

        for cut_width, cut_height, (b_width, b_height) in optimized_cuts:
            if (b_width, b_height) == board:
                rect = Rectangle((0, 0), cut_width, cut_height, linewidth=1, edgecolor='blue', facecolor='cyan', alpha=0.6)
                ax.add_patch(rect)
                ax.text(cut_width / 2, cut_height / 2, f"{cut_width}x{cut_height}", ha='center', va='center', fontsize=8)

    plt.tight_layout()
    return fig

def export_to_pdf(fig):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Optimized Cuts Visualization", ln=True, align='C')

    fig.savefig("visualization.png")
    pdf.image("visualization.png", x=10, y=20, w=190)
    pdf.output("optimized_cuts.pdf")
    return "optimized_cuts.pdf"

def main():
    st.title("Cut List Optimizer")

    st.sidebar.header("Input Parameters")

    st.sidebar.subheader("Boards")
    board_input = st.sidebar.text_area(
        "Enter boards (width,height,quantity):",
        "100,50,2\n200,100,1"
    )
    boards_data = parse_input(board_input)
    boards = [(w, h) for w, h, q in boards_data for _ in range(q)]

    st.sidebar.subheader("Parts")
    parts_input = st.sidebar.text_area(
        "Enter parts (width,height,quantity):",
        "20,10,4\n50,50,2"
    )
    parts_data = parse_input(parts_input)
    parts = [(w, h) for w, h, q in parts_data for _ in range(q)]

    st.sidebar.subheader("Blade Thickness")
    blade_thickness = st.sidebar.selectbox(
        "Select blade thickness:",
        options=[2, 3, 4],
        format_func=lambda x: f"{x} mm"
    )

    if st.button("Optimize Cuts"):
        optimized_cuts = optimize_cuts(boards, parts, blade_thickness)
        st.write("Optimized Cuts", pd.DataFrame(optimized_cuts, columns=['Cut Width', 'Cut Height', 'Board']))
        fig = visualize_cuts(boards, optimized_cuts)
        st.pyplot(fig)

        if st.button("Export to PDF"):
            pdf_path = export_to_pdf(fig)
            with open(pdf_path, "rb") as f:
                st.download_button("Download PDF", f, file_name="optimized_cuts.pdf")

if __name__ == "__main__":
    main()
