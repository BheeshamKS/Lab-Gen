-- ====================================================================
-- DAWOOD UNIVERSITY OF ENGINEERING & TECHNOLOGY
-- Department of Data Science
-- DATABASE SYSTEMS — ASSIGNMENT 01
--
-- Name: Bheesham Kumar Sajnani
-- Roll Number: 25F-DS-020
-- Section: 25F-DS
-- Subject: Database Systems
-- Course Lecturer: Engr. Seema Bughio
-- ====================================================================

-- 1. Table Creation Schema
CREATE TABLE IF NOT EXISTS Student (
    Student_ID VARCHAR(20) PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Department VARCHAR(50) NOT NULL,
    CGPA DECIMAL(3, 2) NOT NULL CHECK (CGPA >= 0.00 AND CGPA <= 4.00)
);

-- 2. Populate Initial Sample Dataset
INSERT INTO Student (Student_ID, Name, Department, CGPA) VALUES
('DS-25-001', 'Sarah Ahmed', 'Data Science', 3.85),
('DS-25-014', 'Bilawal Raza', 'Data Science', 3.42),
('CS-25-022', 'Zohaib Hassan', 'Computer Science', 2.85),
('CS-25-045', 'Hamza Tariq', 'Computer Science', 3.10),
('SE-25-030', 'Fatima Noor', 'Software Engineering', 3.65),
('DS-25-099', 'Ali Murad', 'Data Science', 2.70);

-- Display Initial State
SELECT '--- Initial Student Records ---' AS Info;
SELECT * FROM Student;

-- ====================================================================
-- QUESTION 3: DBMS OPERATIONS
-- ====================================================================

-- Operation 1: Display students with CGPA greater than 3.0
SELECT '--- Operation 1: Students with CGPA > 3.0 ---' AS Info;
SELECT Student_ID, Name, Department, CGPA
FROM Student
WHERE CGPA > 3.00;

-- Operation 2: Change the department of a particular student
SELECT '--- Operation 2: Change Department of Student CS-25-045 to Data Science ---' AS Info;
UPDATE Student
SET Department = 'Data Science'
WHERE Student_ID = 'CS-25-045';

-- Verify Operation 2
SELECT * FROM Student WHERE Student_ID = 'CS-25-045';

-- Operation 3: Remove a student from the table
SELECT '--- Operation 3: Remove Student DS-25-099 ---' AS Info;
DELETE FROM Student
WHERE Student_ID = 'DS-25-099';

-- Verify Operation 3
SELECT * FROM Student WHERE Student_ID = 'DS-25-099';

-- Operation 4: Add a new student
SELECT '--- Operation 4: Add New Student DS-25-102 (Ayesha Khan) ---' AS Info;
INSERT INTO Student (Student_ID, Name, Department, CGPA)
VALUES ('DS-25-102', 'Ayesha Khan', 'Data Science', 3.78);

-- Verify Operation 4 and Final State
SELECT '--- Final State of Student Table ---' AS Info;
SELECT * FROM Student ORDER BY CGPA DESC;

-- ====================================================================
-- QUESTION 4: SECURITY MECHANISMS DEMONSTRATION
-- ====================================================================
-- (Conceptual DCL & RLS implementation as required for Question 4)

-- Table structure for Examination Marks
CREATE TABLE IF NOT EXISTS Examination_Marks (
    Mark_ID INT PRIMARY KEY,
    Student_ID VARCHAR(20) NOT NULL,
    Course_Code VARCHAR(20) NOT NULL,
    Marks DECIMAL(5, 2) CHECK (Marks >= 0 AND Marks <= 100),
    Grade VARCHAR(2),
    FOREIGN KEY (Student_ID) REFERENCES Student(Student_ID)
);

-- Audit Table for Tracking Modifications
CREATE TABLE IF NOT EXISTS Audit_Marks_Log (
    Audit_ID INT AUTO_INCREMENT PRIMARY KEY,
    Student_ID VARCHAR(20),
    Course_Code VARCHAR(20),
    Old_Marks DECIMAL(5, 2),
    New_Marks DECIMAL(5, 2),
    Modified_By VARCHAR(100),
    Modified_Timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Privilege Enforcement Example (PostgreSQL / MySQL Syntax Pattern)
-- REVOKE UPDATE, INSERT, DELETE ON Examination_Marks FROM Student_Role;
-- GRANT SELECT ON Examination_Marks TO Student_Role;
-- GRANT UPDATE (Marks, Grade) ON Examination_Marks TO Faculty_Role;
