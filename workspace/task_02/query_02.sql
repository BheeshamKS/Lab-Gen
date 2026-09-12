-- Name: Bheesham Kumar Sajnani
-- Roll No: 25F-DS-020
-- -------------------------

-- View table schemas from information_schema
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name IN ('Student2', 'Course2');

-- Display all records
SELECT * FROM Student2;
SELECT * FROM Course2;
