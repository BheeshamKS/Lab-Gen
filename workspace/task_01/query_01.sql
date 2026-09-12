-- Name: Bheesham Kumar Sajnani
-- Roll No: 25F-DS-020
-- -------------------------

-- 1. Create Course2 Table with Primary Key
CREATE TABLE Course2 (
    CourseID VARCHAR(10) PRIMARY KEY,
    CourseName VARCHAR(50) NOT NULL,
    CreditHours INT NOT NULL
);

-- 2. Create Student2 Table with Primary Key & Foreign Key
CREATE TABLE Student2 (
    StudentID VARCHAR(15) PRIMARY KEY,
    StudentName VARCHAR(50) NOT NULL,
    Age INT,
    CourseID VARCHAR(10),
    FOREIGN KEY (CourseID) REFERENCES Course2(CourseID)
);
