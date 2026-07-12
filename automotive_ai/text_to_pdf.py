import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus import Paragraph
from reportlab.platypus import Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import FrameBreak

# =========================
# SETTINGS
# =========================

input_folder = r"data/output_text"
output_folder = r"data/output_pdf"

os.makedirs(output_folder, exist_ok=True)

# =========================
# PROCESS FILES
# =========================

for filename in os.listdir(input_folder):

    if filename.lower().endswith(".txt"):

        input_path = os.path.join(input_folder, filename)
        name = os.path.splitext(filename)[0]
        output_path = os.path.join(output_folder, name + ".pdf")

        print(f"Converting: {filename}")

        try:
            doc = SimpleDocTemplate(output_path)
            elements = []

            styles = getSampleStyleSheet()
            normal_style = styles["Normal"]

            with open(input_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for line in lines:
                clean_line = line.strip()

                if clean_line:
                    elements.append(Paragraph(clean_line, normal_style))
                else:
                    elements.append(Spacer(1, 0.2 * inch))  # preserve blank lines

                elements.append(Spacer(1, 0.2 * inch))  # spacing between lines

            doc.build(elements)

        except Exception as e:
            print(f"❌ Failed {filename}: {e}")

print("✅ All TXT files converted to PDF successfully!")