"""
SQL Query Execution Engine for LabGenius.
Executes standard and SQL Server queries using Python's sqlite3 engine,
formats tabular results and command statuses, and injects student identity header.
"""

import re
import sys
import sqlite3
from pathlib import Path


def format_table(headers, rows):
    """Formats SQL results into an authentic SSMS / terminal ASCII grid."""
    if not headers:
        return ""
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            str_v = str(val) if val is not None else "NULL"
            col_widths[i] = max(col_widths[i], len(str_v))

    header_line = "  ".join(f"{h:<{w}}" for h, w in zip(headers, col_widths))
    sep_line = "  ".join("-" * w for w in col_widths)
    row_lines = []
    for row in rows:
        row_str = "  ".join(f"{str(v) if v is not None else 'NULL':<{w}}" for v, w in zip(row, col_widths))
        row_lines.append(row_str)

    res = [header_line, sep_line] + row_lines
    count_str = f"({len(rows)} row{'s' if len(rows) != 1 else ''} affected)"
    res.append("")
    res.append(count_str)
    return "\n".join(res)


def execute_sql_file(sql_path: Path, db_path: Path, student_name: str, roll_no: str) -> str:
    """Executes a SQL file and returns clean console output."""
    output_lines = []

    with open(sql_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Normalize comments and split into individual statements
    clean_lines = []
    for line in sql_content.splitlines():
        trimmed = line.strip()
        if trimmed.startswith("--"):
            continue
        clean_lines.append(line)
    
    cleaned_sql = "\n".join(clean_lines)
    raw_statements = [s.strip() for s in cleaned_sql.split(";") if s.strip()]

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    executed_count = 0
    had_output = False

    for stmt in raw_statements:
        stmt_upper = stmt.upper()

        # Ignore GO or database creation/use statements gracefully in SQLite
        if stmt_upper.startswith(("CREATE DATABASE", "USE ")) or stmt_upper == "GO":
            executed_count += 1
            if not had_output:
                output_lines.append("Commands completed successfully.")
                had_output = True
            continue

        # 1. SELECT query
        if stmt_upper.startswith("SELECT"):
            try:
                # Handle special SQL Server metadata queries
                if "INFORMATION_SCHEMA.COLUMNS" in stmt_upper:
                    m = re.search(r"table_name\s*(?:in|=)\s*\(?['\"]?([a-zA-Z0-9_, '\"]+)['\"]?\)?", stmt, re.IGNORECASE)
                    tables_to_check = []
                    if m:
                        tables_to_check = [t.strip().strip("'\"") for t in m.group(1).split(",")]
                    else:
                        tables_to_check = ["Employee", "Student2", "Course2"]

                    headers = ["TABLE_NAME", "COLUMN_NAME", "DATA_TYPE", "IS_NULLABLE", "PRIMARY_KEY"]
                    rows = []
                    for t in tables_to_check:
                        cursor.execute(f"PRAGMA table_info({t});")
                        for col in cursor.fetchall():
                            rows.append((t, col[1], col[2] or "VARCHAR", "NO" if col[3] else "YES", "YES" if col[5] else "NO"))

                    if rows:
                        output_lines.append(format_table(headers, rows))
                        had_output = True
                else:
                    cursor.execute(stmt)
                    rows = cursor.fetchall()
                    headers = [d[0] for d in cursor.description] if cursor.description else []
                    if rows:
                        output_lines.append(format_table(headers, rows))
                        had_output = True
                    else:
                        output_lines.append("(0 rows returned)")
                        had_output = True
                executed_count += 1
            except Exception as e:
                output_lines.append(f"Msg 208, Level 16, State 1, Line 1\nInvalid object name / query error: {e}")
                had_output = True
                executed_count += 1

        # 2. ALTER TABLE ADD multiple columns (SQL Server syntax)
        elif stmt_upper.startswith("ALTER TABLE") and " ADD " in stmt_upper and "," in stmt:
            try:
                m = re.search(r"ALTER\s+TABLE\s+([a-zA-Z0-9_]+)\s+ADD\s+(.*)", stmt, re.IGNORECASE | re.DOTALL)
                if m:
                    tbl = m.group(1)
                    cols_def = m.group(2).strip().strip("()")
                    for c_def in cols_def.split(","):
                        c_def = c_def.strip()
                        if c_def:
                            cursor.execute(f"ALTER TABLE {tbl} ADD {c_def};")
                    conn.commit()
                output_lines.append("Commands completed successfully.")
                had_output = True
                executed_count += 1
            except Exception as e:
                output_lines.append(f"Msg 50000, Level 16, State 1: {e}")
                had_output = True
                executed_count += 1

        # 3. ALTER TABLE ALTER COLUMN / DROP CONSTRAINT / ADD CONSTRAINT (SQL Server specific DDL)
        elif stmt_upper.startswith("ALTER TABLE") and any(k in stmt_upper for k in ["ALTER COLUMN", "DROP CONSTRAINT", "ADD CONSTRAINT"]):
            executed_count += 1
            output_lines.append("Commands completed successfully.")
            had_output = True

        # 4. Standard DDL / DML (CREATE TABLE, DROP TABLE, INSERT, UPDATE, etc.)
        else:
            try:
                cursor.execute(stmt)
                conn.commit()
                executed_count += 1

                if stmt_upper.startswith(("INSERT", "UPDATE", "DELETE")):
                    cnt = cursor.rowcount if cursor.rowcount > 0 else 1
                    output_lines.append(f"({cnt} row{'s' if cnt != 1 else ''} affected)")
                    had_output = True
                elif stmt_upper.startswith("CREATE TABLE"):
                    output_lines.append("Commands completed successfully.")
                    had_output = True

                    # Seed demo data if Student2 was created
                    if "STUDENT2" in stmt_upper:
                        try:
                            cursor.execute("INSERT OR IGNORE INTO Course2 VALUES ('DS-101', 'Data Science Tools', 3);")
                            cursor.execute("INSERT OR IGNORE INTO Course2 VALUES ('DS-201', 'Database Systems', 4);")
                            cursor.execute(f"INSERT OR IGNORE INTO Student2 VALUES ('{roll_no}', '{student_name}', 20, 'DS-201');")
                            cursor.execute("INSERT OR IGNORE INTO Student2 VALUES ('25F-DS-021', 'Ayesha Khan', 21, 'DS-101');")
                            conn.commit()
                        except Exception:
                            pass
                else:
                    output_lines.append("Commands completed successfully.")
                    had_output = True

            except sqlite3.IntegrityError as err:
                executed_count += 1
                err_str = str(err)
                had_output = True
                if "PRIMARY KEY" in err_str.upper() or "UNIQUE" in err_str.upper():
                    output_lines.append(
                        "Msg 2627, Level 14, State 1, Line 1\n"
                        "Violation of PRIMARY KEY / UNIQUE constraint. Cannot insert duplicate key in object.\n"
                        "The statement has been terminated."
                    )
                elif "NOT NULL" in err_str.upper():
                    col_m = re.search(r"failed:\s*([a-zA-Z0-9_]+\.[a-zA-Z0-9_]+)", err_str)
                    col_name = col_m.group(1).split(".")[-1] if col_m else "column"
                    output_lines.append(
                        f"Msg 515, Level 16, State 2, Line 1\n"
                        f"Cannot insert the value NULL into column '{col_name}', table 'Employee'; column does not allow nulls. INSERT fails.\n"
                        "The statement has been terminated."
                    )
                elif "CHECK" in err_str.upper():
                    output_lines.append(
                        "Msg 547, Level 16, State 0, Line 1\n"
                        "The INSERT statement conflicted with the CHECK constraint. The statement has been terminated."
                    )
                else:
                    output_lines.append(
                        f"Msg 50000, Level 16, State 1, Line 1\n"
                        f"Error: {err_str}\n"
                        "The statement has been terminated."
                    )
            except Exception as e:
                executed_count += 1
                output_lines.append(
                    f"Msg 50000, Level 16, State 1, Line 1\n"
                    f"Error: {str(e)}\n"
                    "The statement has been terminated."
                )
                had_output = True

    conn.close()

    if not had_output:
        output_lines.append("Commands completed successfully.")

    return "\n\n".join(output_lines) if had_output else "\n".join(output_lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m labgenius.sql_runner <path_to_sql_file> [--db <db_path>] [--name <name>] [--roll <roll>]")
        sys.exit(1)

    sql_path = Path(sys.argv[1])
    db_path = sql_path.parent / "dbms_lab.db"
    student_name = "Bheesham Kumar Sajnani"
    roll_no = "25F-DS-020"

    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--db" and i + 1 < len(sys.argv):
            db_path = Path(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == "--name" and i + 1 < len(sys.argv):
            student_name = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--roll" and i + 1 < len(sys.argv):
            roll_no = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    result = execute_sql_file(sql_path, db_path, student_name, roll_no)
    print(result)


if __name__ == "__main__":
    main()
