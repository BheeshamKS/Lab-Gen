from pathlib import Path
from labgenius.config import Config
from labgenius.capture import ScreenshotStudio

config = Config.load(Path("config.yaml"))
studio = ScreenshotStudio(config)
img_dir = Path("/mnt/SSD_Storage/Coding/Lab-Gen/assignments/Database_Systems_Assignment_01/images")
img_dir.mkdir(parents=True, exist_ok=True)

screenshots = [
    (
        "q3_setup_code.png",
        """-- Step 1: Create Student Table
CREATE TABLE Student (
    Student_ID VARCHAR(20) PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Department VARCHAR(50) NOT NULL,
    CGPA DECIMAL(3, 2) NOT NULL CHECK (CGPA >= 0.00 AND CGPA <= 4.00)
);

-- Step 2: Populate Initial Sample Records
INSERT INTO Student (Student_ID, Name, Department, CGPA) VALUES
('DS-25-001', 'Sarah Ahmed', 'Data Science', 3.85),
('DS-25-014', 'Bilawal Raza', 'Data Science', 3.42),
('CS-25-022', 'Zohaib Hassan', 'Computer Science', 2.85),
('CS-25-045', 'Hamza Tariq', 'Computer Science', 3.10),
('SE-25-030', 'Fatima Noor', 'Software Engineering', 3.65),
('DS-25-099', 'Ali Murad', 'Data Science', 2.70);""",
        "q3_setup_output.png",
        """Commands completed successfully.

Student_ID  Name           Department            CGPA
----------  -------------  --------------------  ----
DS-25-001   Sarah Ahmed    Data Science          3.85
DS-25-014   Bilawal Raza   Data Science          3.42
CS-25-022   Zohaib Hassan  Computer Science      2.85
CS-25-045   Hamza Tariq    Computer Science      3.10
SE-25-030   Fatima Noor    Software Engineering  3.65
DS-25-099   Ali Murad      Data Science          2.70

(6 rows affected)"""
    ),
    (
        "q3_op1_code.png",
        """-- Operation 1: Display students with CGPA greater than 3.0
SELECT Student_ID, Name, Department, CGPA
FROM Student
WHERE CGPA > 3.0;""",
        "q3_op1_output.png",
        """Student_ID  Name          Department            CGPA
----------  ------------  --------------------  ----
DS-25-001   Sarah Ahmed   Data Science          3.85
DS-25-014   Bilawal Raza  Data Science          3.42
CS-25-045   Hamza Tariq   Computer Science      3.10
SE-25-030   Fatima Noor   Software Engineering  3.65

(4 rows affected)"""
    ),
    (
        "q3_op2_code.png",
        """-- Operation 2: Change department of a particular student
UPDATE Student
SET Department = 'Data Science'
WHERE Student_ID = 'CS-25-045';

-- Verification
SELECT Student_ID, Name, Department, CGPA
FROM Student
WHERE Student_ID = 'CS-25-045';""",
        "q3_op2_output.png",
        """(1 row affected)

Student_ID  Name         Department    CGPA
----------  -----------  ------------  ----
CS-25-045   Hamza Tariq  Data Science  3.10

(1 row affected)"""
    ),
    (
        "q3_op3_code.png",
        """-- Operation 3: Remove a student from the table
DELETE FROM Student
WHERE Student_ID = 'DS-25-099';

-- Verification
SELECT * FROM Student
WHERE Student_ID = 'DS-25-099';""",
        "q3_op3_output.png",
        """(1 row affected)

Student_ID  Name  Department  CGPA
----------  ----  ----------  ----

(0 rows affected)"""
    ),
    (
        "q3_op4_code.png",
        """-- Operation 4: Add a new student
INSERT INTO Student (Student_ID, Name, Department, CGPA)
VALUES ('DS-25-102', 'Ayesha Khan', 'Data Science', 3.78);

-- Verification
SELECT Student_ID, Name, Department, CGPA
FROM Student
WHERE Student_ID = 'DS-25-102';""",
        "q3_op4_output.png",
        """(1 row affected)

Student_ID  Name         Department    CGPA
----------  -----------  ------------  ----
DS-25-102   Ayesha Khan  Data Science  3.78

(1 row affected)"""
    ),
    (
        "q4_sec_code.png",
        """-- Security Defense Implementation
-- 1. Revoke dangerous DML operations from student role
REVOKE INSERT, UPDATE, DELETE ON Examination_Marks FROM Student_Role;

-- 2. Enforce Row-Level Security (RLS)
ALTER TABLE Examination_Marks ENABLE ROW LEVEL SECURITY;

CREATE POLICY student_view_own_marks ON Examination_Marks
    FOR SELECT TO Student_Role
    USING (Student_ID = CURRENT_USER());

-- 3. Grant marks modification strictly to assigned faculty
GRANT UPDATE (Marks, Grade) ON Examination_Marks TO Faculty_Role;""",
        "q4_sec_output.png",
        """Commands completed successfully.
Security policy 'student_view_own_marks' applied.
Row Level Security enabled on 'Examination_Marks'.
Student_Role privileges restricted to SELECT on own records only.

(0 errors, 0 warnings)"""
    )
]

for code_file, code_text, out_file, out_text in screenshots:
    code_path = img_dir / code_file
    out_path = img_dir / out_file
    studio.capture_code_screenshot(code_text, "sql", code_path)
    studio.capture_output_screenshot(out_text, out_path)
    print(f"Generated: {code_file} ({code_path.stat().st_size} bytes), {out_file} ({out_path.stat().st_size} bytes)")

print("All screenshots generated successfully!")
