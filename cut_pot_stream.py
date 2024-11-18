import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import pandas as pd
from fpdf import FPDF

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
    fig, ax = plt.subplots(figsize=(8, 8))

    for i, board in enumerate(boards):
        board_width, board_height = board
        ax.add_patch(Rectangle((0, -i * (board_height + 10)), board_width, board_height, edgecolor='black', fill=False))

    colors = plt.cm.tab20.colors
    for idx, (cut_width, cut_height, (board_width, board_height)) in enumerate(optimized_cuts):
        color = colors[idx % len(colors)]
        ax.add_patch(Rectangle((0, -idx * (board_height + 10)), cut_width, cut_height, edgecolor='black', color=color, alpha=0.7))

    ax.set_xlim(0, max(board[0] for board in boards))
    ax.set_ylim(-len(boards) * max(board[1] for board in boards), 0)
    ax.set_aspect('equal')
    plt.axis('off')
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
    num_boards = st.sidebar.number_input("Number of boards", min_value=1, step=1)
    boards = []
    for i in range(num_boards):
        width = st.sidebar.number_input(f"Board {i+1} Width", min_value=1.0, step=0.1)
        height = st.sidebar.number_input(f"Board {i+1} Height", min_value=1.0, step=0.1)
        boards.append((width, height))

    num_cuts = st.sidebar.number_input("Number of cuts", min_value=1, step=1)
    cuts = []
    for i in range(num_cuts):
        width = st.sidebar.number_input(f"Cut {i+1} Width", min_value=1.0, step=0.1)
        height = st.sidebar.number_input(f"Cut {i+1} Height", min_value=1.0, step=0.1)
        cuts.append((width, height))

    blade_thickness = st.sidebar.number_input("Blade Thickness", min_value=0.0, step=0.1)

    if st.button("Optimize Cuts"):
        optimized_cuts = optimize_cuts(boards, cuts, blade_thickness)
        st.write("Optimized Cuts", pd.DataFrame(optimized_cuts, columns=['Cut Width', 'Cut Height', 'Board']))
        fig = visualize_cuts(boards, optimized_cuts)
        st.pyplot(fig)

        if st.button("Export to PDF"):
            pdf_path = export_to_pdf(fig)
            with open(pdf_path, "rb") as f:
                st.download_button("Download PDF", f, file_name="optimized_cuts.pdf")

if __name__ == "__main__":
    main()
