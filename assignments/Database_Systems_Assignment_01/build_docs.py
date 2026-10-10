import os
import subprocess
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def set_cell_margins(cell, top=120, bottom=120, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_table_borders(table, color="D0D5DD", sz="4", val="single"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'  <w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:left w:val="none"/>'
        f'  <w:right w:val="none"/>'
        f'  <w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:insideV w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def set_grid_borders(table, color="CCCCCC", sz="4"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>\n'
        f'  <w:top w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f'  <w:bottom w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f'  <w:left w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f'  <w:right w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f'  <w:insideH w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f'  <w:insideV w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def add_code_block(doc, code_text):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, "F4F5F7")
    set_cell_margins(cell, top=140, bottom=140, left=180, right=180)
    
    # Border on left (accent line)
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'  <w:left w:val="single" w:sz="18" w:space="0" w:color="0A66C2"/>'
        f'  <w:top w:val="none"/>'
        f'  <w:bottom w:val="none"/>'
        f'  <w:right w:val="none"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = Pt(13.5)
    
    lines = code_text.strip().split("\n")
    for i, line in enumerate(lines):
        if i > 0:
            p = cell.add_paragraph()
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = Pt(13.5)
        run = p.add_run(line)
        run.font.name = "Consolas"
        run.font.size = Pt(9.5)
        run.font.color.rgb = RGBColor(30, 41, 59)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def add_callout(doc, text, title=None, bg_color="F0F7FF", border_color="0A66C2"):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, bg_color)
    set_cell_margins(cell, top=120, bottom=120, left=160, right=160)
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'  <w:left w:val="single" w:sz="18" w:space="0" w:color="{border_color}"/>'
        f'  <w:top w:val="none"/>'
        f'  <w:bottom w:val="none"/>'
        f'  <w:right w:val="none"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(borders)
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(2)
    if title:
        trun = p.add_run(title + "\n")
        trun.bold = True
        trun.font.name = "Arial"
        trun.font.size = Pt(10)
        trun.font.color.rgb = RGBColor(10, 50, 110)
    r = p.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(10)
    r.font.italic = True
    r.font.color.rgb = RGBColor(51, 65, 85)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def build_assignment_doc():
    doc = Document()
    
    # Page setup
    for s in doc.sections:
        s.top_margin = Inches(0.7)
        s.bottom_margin = Inches(0.7)
        s.left_margin = Inches(0.8)
        s.right_margin = Inches(0.8)
        header = s.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("Database Systems | Data Science | Batch 25 | Assignment 01")
        hrun.font.name = "Arial"
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = RGBColor(120, 120, 120)
        
        footer = s.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        frun = fp.add_run("Dawood University of Engineering & Technology — Department of Data Science")
        frun.font.name = "Arial"
        frun.font.size = Pt(8)
        frun.font.color.rgb = RGBColor(150, 150, 150)

    # Document Header
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_p.paragraph_format.space_after = Pt(2)
    t_run = title_p.add_run("DAWOOD UNIVERSITY OF ENGINEERING & TECHNOLOGY")
    t_run.bold = True
    t_run.font.name = "Arial"
    t_run.font.size = Pt(15)
    t_run.font.color.rgb = RGBColor(17, 24, 39)

    dept_p = doc.add_paragraph()
    dept_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    dept_p.paragraph_format.space_after = Pt(4)
    d_run = dept_p.add_run("Department of Data Science")
    d_run.bold = True
    d_run.font.name = "Arial"
    d_run.font.size = Pt(12)
    d_run.font.color.rgb = RGBColor(55, 65, 81)

    sub_p = doc.add_paragraph()
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_p.paragraph_format.space_after = Pt(6)
    s_run = sub_p.add_run("DATABASE SYSTEMS — ASSIGNMENT 01")
    s_run.bold = True
    s_run.font.name = "Arial"
    s_run.font.size = Pt(13)
    s_run.font.color.rgb = RGBColor(15, 23, 42)

    # Deadline Badge (Yellow/Gold highlighting like the original PDF)
    dl_p = doc.add_paragraph()
    dl_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    dl_p.paragraph_format.space_after = Pt(8)
    dl_run = dl_p.add_run("  DEADLINE : 10-OCT-2026  ")
    dl_run.bold = True
    dl_run.font.name = "Arial"
    dl_run.font.size = Pt(11)
    dl_run.font.color.rgb = RGBColor(180, 83, 9) # Deep amber
    # Yellow background highlight for deadline
    dl_xml = parse_xml(f'<w:highlight {nsdecls("w")} w:val="yellow"/>')
    dl_run._r.get_or_add_rPr().append(dl_xml)

    # Course Metadata Grid (Exact table as on PDF)
    meta_tbl = doc.add_table(rows=3, cols=4)
    meta_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_grid_borders(meta_tbl, color="4B5563")

    meta_data = [
        [("Batch", True), ("25", False), ("Sessional Marks", True), ("5", False)],
        [("Course", True), ("Database Systems", False), ("Lecturer", True), ("Engr. Seema Bughio", False)],
        [("Department", True), ("Data Science", False), ("Assignment", True), ("01", False)]
    ]

    for row_idx, row_content in enumerate(meta_data):
        for col_idx, (text, is_bold) in enumerate(row_content):
            cell = meta_tbl.cell(row_idx, col_idx)
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
            if is_bold:
                set_cell_background(cell, "F3F4F6")
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(text)
            r.font.name = "Arial"
            r.font.size = Pt(9.5)
            r.bold = is_bold
            r.font.color.rgb = RGBColor(17, 24, 39)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # Student Submission Block (Required by prompt: "Write your Name and Roll Number on the first page")
    stu_tbl = doc.add_table(rows=2, cols=2)
    stu_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_grid_borders(stu_tbl, color="9CA3AF")
    
    stu_fields = [
        [("Student Name:", True, " [Write Your Full Name]"), ("Roll Number:", True, " [Write Your Roll No. e.g. 25DS001]")],
        [("Submission Date:", True, " October 10, 2026"), ("Verification:", True, " Solved & Verified")]
    ]
    for r_idx, r_cols in enumerate(stu_fields):
        for c_idx, (label, is_bold, val) in enumerate(r_cols):
            cell = stu_tbl.cell(r_idx, c_idx)
            set_cell_margins(cell, top=70, bottom=70, left=100, right=100)
            set_cell_background(cell, "FAFAFA")
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            lbl_run = p.add_run(label)
            lbl_run.bold = True
            lbl_run.font.name = "Arial"
            lbl_run.font.size = Pt(9.5)
            lbl_run.font.color.rgb = RGBColor(17, 24, 39)
            val_run = p.add_run(val)
            val_run.font.name = "Arial"
            val_run.font.size = Pt(9.5)
            val_run.font.color.rgb = RGBColor(75, 85, 99)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # Instructions box
    add_callout(
        doc,
        "• Answer all questions.\n"
        "• Write clear and well-structured answers.\n"
        "• For SQL questions, write syntactically correct SQL queries.\n"
        "• Where required, explain the purpose of the SQL statement or security mechanism.\n"
        "• Submission Requirements: Submit a neat, properly formatted assignment. Write your Name and Roll Number on the first page.",
        title="INSTRUCTIONS & GUIDELINES",
        bg_color="F8FAFC",
        border_color="3B82F6"
    )

    # ================= QUESTION 1 =================
    h1 = doc.add_heading(level=1)
    h1.paragraph_format.space_before = Pt(14)
    h1.paragraph_format.space_after = Pt(4)
    r = h1.add_run("Q1. Database Role in Information Systems")
    r.font.name = "Arial"
    r.font.size = Pt(13)
    r.bold = True
    r.font.color.rgb = RGBColor(15, 23, 42)

    add_callout(
        doc,
        "Explain how a database supports a University Information System. Identify at least four types of information that can be stored in the database and explain how different users can use this information.",
        title="Question Prompt",
        bg_color="F1F5F9",
        border_color="64748B"
    )

    # Section 1.1
    p = doc.add_paragraph()
    r = p.add_run("1.1 How a Database Supports a University Information System (UIS)")
    r.bold = True
    r.font.name = "Arial"
    r.font.size = Pt(11)
    r.font.color.rgb = RGBColor(30, 41, 59)

    doc.add_paragraph(
        "A University Information System (UIS) is an integrated academic and management platform that coordinates university-wide activities. A modern Relational Database Management System (DBMS) acts as the operational backbone for this system through four critical pillars:"
    )

    bullet_points_1 = [
        ("Centralized Data Repository: ", "Eliminates departmental data silos and redundant record-keeping. Academic records, admissions data, and financial records reside in a unified, normalized database rather than disparate spreadsheets or flat files."),
        ("Data Consistency & Integrity: ", "Enforces strict integrity constraints (Primary Keys, Foreign Keys, Unique Keys, and Check constraints). For example, it ensures that a course grade cannot reference a non-existent student or contain an invalid score."),
        ("Multi-User Concurrency & Transaction Management: ", "Supports concurrent operations by thousands of users simultaneously (e.g., during course enrollment or fee payment weeks) using ACID properties (Atomicity, Consistency, Isolation, Durability) to eliminate race conditions and data conflicts."),
        ("Security & Abstraction Levels: ", "Provides physical and logical data independence along with view-level security. Sensitive records (such as confidential examination marks or faculty compensation) are protected via access control lists.")
    ]
    for b_title, b_desc in bullet_points_1:
        bp = doc.add_paragraph(style='List Bullet')
        bp.paragraph_format.space_before = Pt(2)
        bp.paragraph_format.space_after = Pt(2)
        t_run = bp.add_run(b_title)
        t_run.bold = True
        t_run.font.name = "Calibri"
        d_run = bp.add_run(b_desc)
        d_run.font.name = "Calibri"

    # Section 1.2
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    r = p.add_run("1.2 Four Types of Information Stored in the Database")
    r.bold = True
    r.font.name = "Arial"
    r.font.size = Pt(11)
    r.font.color.rgb = RGBColor(30, 41, 59)

    info_tbl = doc.add_table(rows=5, cols=3)
    info_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_grid_borders(info_tbl, color="CBD5E1")

    headers = ["#", "Information Category", "Attributes & Details Stored"]
    for c_idx, h_text in enumerate(headers):
        cell = info_tbl.cell(0, c_idx)
        set_cell_background(cell, "0F172A")
        set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        hrun = p.add_run(h_text)
        hrun.bold = True
        hrun.font.name = "Arial"
        hrun.font.size = Pt(9.5)
        hrun.font.color.rgb = RGBColor(255, 255, 255)

    info_rows = [
        ("1", "Student Academic & Personal Information", "Student ID, Name, CNIC, Contact Details, Department, Enrollment Year, Courses Enrolled, Attendance, Semester GPAs, and Cumulative CGPA."),
        ("2", "Faculty & Staff Records", "Faculty ID, Full Name, Designation, Department Affiliation, Assigned Courses, Teaching Timetable, Contact Info, and Payroll/Salary Details."),
        ("3", "Course & Curriculum Catalog", "Course Code (e.g. DS-211), Course Title, Credit Hours (Theory + Lab), Prerequisites, Syllabus Content, and Assigned Lecture Hall/Lab Venues."),
        ("4", "Financial & Fee Transactions", "Challan / Voucher Numbers, Tuition Fee Amount, Due Date, Payment Status (Paid/Pending), Bank Transaction Reference, and Scholarship Allocations.")
    ]

    for r_idx, (num, cat, desc) in enumerate(info_rows, start=1):
        bg = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate([num, cat, desc]):
            cell = info_tbl.cell(r_idx, c_idx)
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(val)
            r.font.name = "Calibri"
            r.font.size = Pt(9.5)
            if c_idx == 1:
                r.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # Section 1.3
    p = doc.add_paragraph()
    r = p.add_run("1.3 How Different Users Utilize This Information")
    r.bold = True
    r.font.name = "Arial"
    r.font.size = Pt(11)
    r.font.color.rgb = RGBColor(30, 41, 59)

    user_groups = [
        ("Students: ", "Use the UIS portal to register for semester courses, check weekly schedules, monitor class attendance percentages, review semester examination marks and CGPA, and download fee vouchers."),
        ("Faculty / Lecturers: ", "Access course enrollment rosters, mark attendance, enter and modify assignment/quiz/lab scores, submit midterm and final grades, and track student academic performance trends."),
        ("Academic Administration & Examination Cell: ", "Audit course grade sheets, calculate class grade distributions, verify graduation requirements, generate official transcripts, and manage timetable scheduling."),
        ("Finance & Accounts Staff: ", "Verify student fee payment status to issue admit cards, identify outstanding fee defaulters, and process monthly staff salaries and department operational budgets.")
    ]
    for u_title, u_desc in user_groups:
        bp = doc.add_paragraph(style='List Bullet')
        bp.paragraph_format.space_before = Pt(2)
        bp.paragraph_format.space_after = Pt(2)
        t_run = bp.add_run(u_title)
        t_run.bold = True
        t_run.font.name = "Calibri"
        d_run = bp.add_run(u_desc)
        d_run.font.name = "Calibri"

    # ================= QUESTION 2 =================
    h2 = doc.add_heading(level=1)
    h2.paragraph_format.space_before = Pt(16)
    h2.paragraph_format.space_after = Pt(4)
    r = h2.add_run("Q2. Basic Database Security")
    r.font.name = "Arial"
    r.font.size = Pt(13)
    r.bold = True
    r.font.color.rgb = RGBColor(15, 23, 42)

    add_callout(
        doc,
        "A university database contains students' personal information and examination results. Identify three basic security measures that should be implemented to protect this data. Explain the purpose of each measure.",
        title="Question Prompt",
        bg_color="F1F5F9",
        border_color="64748B"
    )

    sec_measures = [
        (
            "Measure 1: Authentication & Role-Based Access Control (RBAC)",
            "Mechanism & Implementation:",
            "Authentication verifies identity using salted password hashing (e.g., bcrypt, Argon2) and Multi-Factor Authentication (MFA). RBAC then enforces the Principle of Least Privilege (PoLP) by restricting permissions according to user roles. Students have read-only privileges exclusively for their own individual results. Instructors have write privileges only for courses they teach. Administrative and examination staff have audited administrative privileges.",
            "Purpose of Measure:",
            "Prevents unauthorized users, eavesdroppers, and student accounts from accessing confidential administrative data or altering other students' examination marks and personal records."
        ),
        (
            "Measure 2: Data Encryption (In-Transit and At-Rest)",
            "Mechanism & Implementation:",
            "Transport Layer Security (TLS/HTTPS) encrypts all data transmitted between client browsers, application servers, and the database engine. Transparent Data Encryption (TDE) with industry-standard AES-256 encrypts the database data files, tablespaces, and backups residing on physical storage drives.",
            "Purpose of Measure:",
            "Guarantees confidentiality. Even if network traffic is intercepted via packet sniffing or physical storage hard drives/backup tapes are stolen, the information remains unreadable and cryptographically secured without the decryption keys."
        ),
        (
            "Measure 3: Database Auditing, Activity Logging & Data Integrity Constraints",
            "Mechanism & Implementation:",
            "The DBMS maintains an automated, tamper-resistant audit trail logging every modification (who modified a record, previous mark value, updated value, client IP address, and exact timestamp). Database triggers and domain CHECK constraints (e.g., 0 <= Marks <= 100) validate all incoming updates.",
            "Purpose of Measure:",
            "Provides accountability, non-repudiation, and traceability. In the event of unauthorized tampering or grade alteration attempts, administrators can trace the exact user and timestamp, detect anomalies immediately, and roll back changes to verified states."
        )
    ]

    for m_title, m_tech_lbl, m_tech, m_purp_lbl, m_purp in sec_measures:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(m_title)
        r.bold = True
        r.font.name = "Arial"
        r.font.size = Pt(11)
        r.font.color.rgb = RGBColor(30, 41, 59)

        p1 = doc.add_paragraph()
        p1.paragraph_format.space_before = Pt(1)
        p1.paragraph_format.space_after = Pt(2)
        r_lbl1 = p1.add_run(m_tech_lbl + " ")
        r_lbl1.bold = True
        r_lbl1.font.name = "Calibri"
        r_val1 = p1.add_run(m_tech)
        r_val1.font.name = "Calibri"

        p2 = doc.add_paragraph()
        p2.paragraph_format.space_before = Pt(1)
        p2.paragraph_format.space_after = Pt(4)
        r_lbl2 = p2.add_run(m_purp_lbl + " ")
        r_lbl2.bold = True
        r_lbl2.font.color.rgb = RGBColor(180, 83, 9)
        r_lbl2.font.name = "Calibri"
        r_val2 = p2.add_run(m_purp)
        r_val2.font.name = "Calibri"

    # ================= QUESTION 3 =================
    h3 = doc.add_heading(level=1)
    h3.paragraph_format.space_before = Pt(16)
    h3.paragraph_format.space_after = Pt(4)
    r = h3.add_run("Q3. DBMS Operations (SQL Queries)")
    r.font.name = "Arial"
    r.font.size = Pt(13)
    r.bold = True
    r.font.color.rgb = RGBColor(15, 23, 42)

    add_callout(
        doc,
        "Given a Student table containing Student_ID, Name, Department, and CGPA, write SQL queries to perform the following operations:\n"
        "• Display students with CGPA greater than 3.0.\n"
        "• Change the department of a particular student.\n"
        "• Remove a student from the table.\n"
        "• Add a new student.",
        title="Question Prompt",
        bg_color="F1F5F9",
        border_color="64748B"
    )

    doc.add_paragraph(
        "Schema Context: The Student table relation consists of attributes Student_ID (Primary Key), Name (VARCHAR), Department (VARCHAR), and CGPA (DECIMAL)."
    )

    # Op 1
    p = doc.add_paragraph()
    r = p.add_run("Operation 1: Display students with CGPA greater than 3.0")
    r.bold = True
    r.font.name = "Arial"
    r.font.size = Pt(10.5)

    add_code_block(
        doc,
        "-- Operation 1: Retrieve all students with CGPA > 3.0\n"
        "SELECT Student_ID, Name, Department, CGPA\n"
        "FROM Student\n"
        "WHERE CGPA > 3.0;"
    )

    p = doc.add_paragraph()
    r = p.add_run("Purpose & Explanation: ")
    r.bold = True
    p.add_run(
        "The SELECT statement specifies the projection of columns to display. The FROM clause points to the Student table. The WHERE clause filters records with a strict relational condition (CGPA > 3.0), discarding records with CGPA equal to or less than 3.0."
    )

    # Op 2
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    r = p.add_run("Operation 2: Change the department of a particular student")
    r.bold = True
    r.font.name = "Arial"
    r.font.size = Pt(10.5)

    add_code_block(
        doc,
        "-- Operation 2: Update the department of a specific student by Student_ID\n"
        "UPDATE Student\n"
        "SET Department = 'Data Science'\n"
        "WHERE Student_ID = 'DS-25-045';"
    )

    p = doc.add_paragraph()
    r = p.add_run("Purpose & Explanation: ")
    r.bold = True
    p.add_run(
        "The UPDATE statement designates the table to modify. The SET clause assigns the new departmental value ('Data Science'). Crucially, the WHERE clause isolates the exact student using their unique Primary Key (Student_ID = 'DS-25-045') to prevent accidentally updating all student records in the university."
    )

    # Op 3
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    r = p.add_run("Operation 3: Remove a student from the table")
    r.bold = True
    r.font.name = "Arial"
    r.font.size = Pt(10.5)

    add_code_block(
        doc,
        "-- Operation 3: Delete a particular student record from the table\n"
        "DELETE FROM Student\n"
        "WHERE Student_ID = 'DS-25-099';"
    )

    p = doc.add_paragraph()
    r = p.add_run("Purpose & Explanation: ")
    r.bold = True
    p.add_run(
        "The DELETE FROM statement removes tuples from the Student relation. The WHERE Student_ID = 'DS-25-099' condition targets the specific student uniquely, ensuring that only that designated row is deleted while retaining all other student data."
    )

    # Op 4
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    r = p.add_run("Operation 4: Add a new student")
    r.bold = True
    r.font.name = "Arial"
    r.font.size = Pt(10.5)

    add_code_block(
        doc,
        "-- Operation 4: Insert a new student record into the Student table\n"
        "INSERT INTO Student (Student_ID, Name, Department, CGPA)\n"
        "VALUES ('DS-25-102', 'Ayesha Khan', 'Data Science', 3.78);"
    )

    p = doc.add_paragraph()
    r = p.add_run("Purpose & Explanation: ")
    r.bold = True
    p.add_run(
        "The INSERT INTO clause specifies the target relation along with explicit column definitions (Student_ID, Name, Department, CGPA). The VALUES clause provides matching literal values corresponding to the data types, inserting a new tuple into the database."
    )

    # ================= QUESTION 4 =================
    h4 = doc.add_heading(level=1)
    h4.paragraph_format.space_before = Pt(16)
    h4.paragraph_format.space_after = Pt(4)
    r = h4.add_run("Q4. Security Scenario")
    r.font.name = "Arial"
    r.font.size = Pt(13)
    r.bold = True
    r.font.color.rgb = RGBColor(15, 23, 42)

    add_callout(
        doc,
        "Scenario: A student is able to access and modify another student's examination marks through the university database system.\n"
        "a) What security problem exists?\n"
        "b) What database security mechanism could help prevent this problem?",
        title="Question Prompt",
        bg_color="F1F5F9",
        border_color="64748B"
    )

    # Part a
    p = doc.add_paragraph()
    r = p.add_run("4.1 Part (a): What Security Problem Exists?")
    r.bold = True
    r.font.name = "Arial"
    r.font.size = Pt(11)
    r.font.color.rgb = RGBColor(30, 41, 59)

    sec_problems = [
        ("Broken Object-Level Authorization (BOLA) / Broken Access Control: ", "The system fails to verify whether the logged-in student has legitimate authorization to access or alter examination records belonging to other students. This is a critical authorization vulnerability where user-supplied IDs are trusted without backend ownership verification."),
        ("Violation of the Principle of Least Privilege (PoLP): ", "Students have been granted excessive write privileges (UPDATE/INSERT) on examination tables that should strictly belong to instructors and examination controllers."),
        ("Breach of the CIA Triad (Confidentiality & Integrity): ", "Confidentiality is breached because private grades are exposed to peers. Integrity is destroyed because unauthorized users can manipulate academic scores, falsifying institutional academic records."),
        ("Insecure Direct Object Reference (IDOR): ", "If the student modified another student's marks by altering a URL parameter or student ID in a request payload, the application failed to validate server-side session ownership before executing the database command.")
    ]
    for sp_title, sp_desc in sec_problems:
        bp = doc.add_paragraph(style='List Bullet')
        bp.paragraph_format.space_before = Pt(2)
        bp.paragraph_format.space_after = Pt(2)
        t_run = bp.add_run(sp_title)
        t_run.bold = True
        t_run.font.name = "Calibri"
        d_run = bp.add_run(sp_desc)
        d_run.font.name = "Calibri"

    # Part b
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    r = p.add_run("4.2 Part (b): What Database Security Mechanism Could Help Prevent This Problem?")
    r.bold = True
    r.font.name = "Arial"
    r.font.size = Pt(11)
    r.font.color.rgb = RGBColor(30, 41, 59)

    doc.add_paragraph(
        "To prevent this critical vulnerability, the database architecture must enforce multi-layer defense-in-depth security:"
    )

    sol_mechanisms = [
        (
            "1. Role-Based Access Control (RBAC) & Privilege Revocation (DCL):",
            "At the DBMS level, all UPDATE, INSERT, and DELETE privileges on examination tables must be permanently revoked from student roles. Only faculty roles and examination cell administrators should hold update rights on marks."
        ),
        (
            "2. Row-Level Security (RLS):",
            "Relational DBMS engines (such as PostgreSQL and SQL Server) support Row-Level Security policies. RLS automatically evaluates user session identity so that even if a student attempts to query or alter another student's ID, the DBMS kernel restricts row visibility exclusively to rows matching the authenticated user's ID (e.g., USING (Student_ID = CURRENT_USER()))."
        ),
        (
            "3. Secure Database Views & Stored Procedures:",
            "Students should never interact directly with base database tables. Instead, access should be mediated via secure Views that expose only the logged-in user's data, and all grade alterations should be wrapped in Stored Procedures that validate instructor identity and semester grade freeze deadlines."
        ),
        (
            "4. Audit Triggers & Anomaly Detection:",
            "Implement automated database triggers on examination marks tables that write every update attempt to an immutable audit table (recording Old_Marks, New_Marks, User_ID, Client_IP, and Timestamp) and trigger real-time alerts for unauthorized attempts."
        )
    ]
    for sm_title, sm_desc in sol_mechanisms:
        bp = doc.add_paragraph(style='List Bullet')
        bp.paragraph_format.space_before = Pt(2)
        bp.paragraph_format.space_after = Pt(2)
        t_run = bp.add_run(sm_title + " ")
        t_run.bold = True
        t_run.font.name = "Calibri"
        d_run = bp.add_run(sm_desc)
        d_run.font.name = "Calibri"

    add_code_block(
        doc,
        "-- Example Defense: Database Privilege Revocation & Row-Level Security\n"
        "-- 1. Revoke write privileges from students\n"
        "REVOKE INSERT, UPDATE, DELETE ON Examination_Marks FROM Student_Role;\n"
        "\n"
        "-- 2. Enable Row-Level Security (RLS)\n"
        "ALTER TABLE Examination_Marks ENABLE ROW LEVEL SECURITY;\n"
        "\n"
        "-- 3. Policy: Students can only view their own examination marks\n"
        "CREATE POLICY student_view_own_marks ON Examination_Marks\n"
        "    FOR SELECT TO Student_Role\n"
        "    USING (Student_ID = CURRENT_USER());"
    )

    doc.save("/mnt/SSD_Storage/Coding/Lab-Gen/assignments/Database_Systems_Assignment_01/Database_Systems_Assignment_01.docx")
    print("DOCX generated successfully!")

if __name__ == "__main__":
    build_assignment_doc()
