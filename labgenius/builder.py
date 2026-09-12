"""
Document Builder & Styler for LabGenius.
Compiles clean, university-exact Word reports (.docx) matching the student's submission standards:
Title cover page, Program headings, Code screenshots, and Output screenshots.
"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

from .config import Config
from .parser import LabManual, LabTask
from .solver import TaskSolution
from .runner import ExecutionResult


class DocumentBuilder:
    """Builds university-exact lab report documents."""

    def __init__(self, config: Config):
        self.config = config
        self.student = config.student
        self.doc_conf = config.document

    def build_report(
        self,
        manual: LabManual,
        solutions: List[TaskSolution],
        exec_results: List[ExecutionResult],
        task_screenshots: List[Tuple[Path, Path]],  # List of (code_img, out_img)
        output_path: Path,
    ) -> Path:
        """Generate the completed lab document (.docx) matching user's completed lab format."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        doc = docx.Document()

        # Set 1.0 inch standard margins
        for section in doc.sections:
            section.top_margin = Inches(1.0)
            section.bottom_margin = Inches(1.0)
            section.left_margin = Inches(1.0)
            section.right_margin = Inches(1.0)

        # -------------------------------------------------------------
        # PAGE 1: TITLE / COVER PAGE (Centered)
        # -------------------------------------------------------------
        for _ in range(4):
            doc.add_paragraph()

        # 1. Lab Number
        p_lab = doc.add_paragraph()
        p_lab.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_lab = p_lab.add_run(f"LAB #{manual.lab_number}")
        r_lab.font.bold = True
        r_lab.font.size = Pt(20.0)

        # 2. Lab Title
        p_title = doc.add_paragraph()
        p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_title = p_title.add_run(manual.title)
        r_title.font.bold = True
        r_title.font.size = Pt(16.0)

        doc.add_paragraph()

        # 3. Submitted to
        p_sub_to_lbl = doc.add_paragraph()
        p_sub_to_lbl.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_st = p_sub_to_lbl.add_run("Submitted to")
        r_st.font.bold = True
        r_st.font.size = Pt(20.0)

        p_sub_to = doc.add_paragraph()
        p_sub_to.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_inst = p_sub_to.add_run(self.student.instructor)
        r_inst.font.bold = True
        r_inst.font.size = Pt(16.0)

        doc.add_paragraph()

        # 4. Submitted by
        p_sub_by_lbl = doc.add_paragraph()
        p_sub_by_lbl.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_sb = p_sub_by_lbl.add_run("Submitted by")
        r_sb.font.bold = True
        r_sb.font.size = Pt(20.0)

        p_sub_by = doc.add_paragraph()
        p_sub_by.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_name = p_sub_by.add_run(f"{self.student.name}\n({self.student.roll_number})")
        r_name.font.bold = True
        r_name.font.size = Pt(16.0)

        # Page break after Title Page
        doc.add_page_break()

        # -------------------------------------------------------------
        # PAGES 2+: ONLY THE ASSIGNED TASKS / PROGRAMS
        # -------------------------------------------------------------
        for idx, task in enumerate(manual.tasks):
            sol = next((s for s in solutions if s.task_id == task.task_id), solutions[idx] if idx < len(solutions) else None)
            res = next((r for r in exec_results if r.task_id == task.task_id), exec_results[idx] if idx < len(exec_results) else None)
            code_img, out_img = task_screenshots[idx] if idx < len(task_screenshots) else (None, None)

            # Program / Query Heading
            prefix = "Query" if task.language == "sql" else "Program"
            p_prog = doc.add_paragraph()
            r_prog = p_prog.add_run(f"{prefix} {task.task_id:02d}:  ")
            r_prog.font.bold = True
            r_prog.font.size = Pt(20.0)
            p_prog.paragraph_format.space_before = Pt(0)
            p_prog.paragraph_format.space_after = Pt(4)

            # Subheading: CODE / QUERY:
            p_c_lbl = doc.add_paragraph()
            r_cl = p_c_lbl.add_run("QUERY:" if task.language == "sql" else "CODE:")
            r_cl.font.bold = True
            r_cl.font.size = Pt(18.0)
            p_c_lbl.paragraph_format.space_before = Pt(0)
            p_c_lbl.paragraph_format.space_after = Pt(4)

            # Code Screenshot Image
            if code_img and code_img.exists():
                p_code_img = doc.add_paragraph()
                p_code_img.paragraph_format.space_before = Pt(0)
                p_code_img.paragraph_format.space_after = Pt(6)
                self._add_image_natural(p_code_img, code_img, max_width_in=6.0, max_height_in=5.2)

            # Subheading: OUTPUT:
            p_o_lbl = doc.add_paragraph()
            r_ol = p_o_lbl.add_run("OUTPUT:")
            r_ol.font.bold = True
            r_ol.font.size = Pt(18.0)
            p_o_lbl.paragraph_format.space_before = Pt(4)
            p_o_lbl.paragraph_format.space_after = Pt(4)

            # Output Screenshot Image
            if out_img and out_img.exists():
                p_out_img = doc.add_paragraph()
                p_out_img.paragraph_format.space_before = Pt(0)
                p_out_img.paragraph_format.space_after = Pt(6)
                self._add_image_natural(p_out_img, out_img, max_width_in=6.0, max_height_in=3.8)

            # Page break between programs (except the last one)
            if idx < len(manual.tasks) - 1:
                doc.add_page_break()

        doc.save(output_path)
        return output_path

    @staticmethod
    def _add_image_natural(paragraph, image_path: Path, max_width_in: float = 6.0, max_height_in: float = 5.2):
        """Inserts image preserving 96 DPI natural screen snip scale up to page boundaries."""
        try:
            from PIL import Image
            with Image.open(image_path) as im:
                w_px, h_px = im.size
            
            w_in = w_px / 96.0
            h_in = h_px / 96.0
            
            scale = 1.0
            if w_in > max_width_in:
                scale = min(scale, max_width_in / w_in)
            if h_in > max_height_in:
                scale = min(scale, max_height_in / h_in)
                
            final_w = w_in * scale
            paragraph.add_run().add_picture(str(image_path), width=Inches(final_w))
        except Exception:
            paragraph.add_run().add_picture(str(image_path), width=Inches(min(5.5, max_width_in)))
