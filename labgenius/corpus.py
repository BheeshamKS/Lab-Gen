"""
Reference Corpus System for LabGenius.
Maintains verified academic reference examples, architectural guidelines,
and subject-specific conventions across Data Structures & Algorithms (DSA)
and Database Management Systems (DBMS).
"""

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional


@dataclass
class ReferenceTask:
    lab_id: str                      # e.g. "DSA_LAB01", "DBMS_LAB04"
    task_id: int
    title: str
    original_task_statement: str
    subject: str                     # "dsa" or "dbms"
    topic: str                       # e.g. "Singly Linked List", "SQL Integrity Constraints"
    keywords: List[str]
    solution_approach: str           # Architectural strategy (OOP, T-SQL, etc.)
    code_pattern: str                # Canonical clean implementation pattern
    explanation_depth: str           # Standard academic explanation depth
    assumptions_and_limitations: str
    verified: bool                   # True only when execution was verified against runtime


class ReferenceCorpus:
    """Manages persistent reference corpus across application restarts."""

    DEFAULT_CORPUS_FILE = Path(__file__).parent / "assets" / "reference_corpus.json"

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or self.DEFAULT_CORPUS_FILE
        self.entries: List[ReferenceTask] = []
        if self.storage_path.exists():
            self.load()
        else:
            self._initialize_canonical_corpus()
            self.save()

    def _initialize_canonical_corpus(self):
        """Initializes verified corpus derived from the 10 reference labs."""
        self.entries = [
            # -------------------------------------------------------------
            # DSA LAB 01: OOP, Arrays & Matrix Operations
            # -------------------------------------------------------------
            ReferenceTask(
                lab_id="DSA_LAB01",
                task_id=1,
                title="Matrix Arithmetic & 2D Arrays",
                original_task_statement="Write a program to perform addition, subtraction, and multiplication on two 2D matrices.",
                subject="dsa",
                topic="2D Arrays & Matrices",
                keywords=["matrix", "2d array", "matrix multiplication", "addition", "subtraction", "matrix operations"],
                solution_approach="Clean procedural or OOP matrix manipulation without external libraries like numpy unless requested. Verify dimension compatibility before multiplication.",
                code_pattern=(
                    "def add_matrices(A, B):\n"
                    "    return [[A[i][j] + B[i][j] for j in range(len(A[0]))] for i in range(len(A))]\n\n"
                    "def multiply_matrices(A, B):\n"
                    "    rA, cA, cB = len(A), len(A[0]), len(B[0])\n"
                    "    res = [[0] * cB for _ in range(rA)]\n"
                    "    for i in range(rA):\n"
                    "        for j in range(cB):\n"
                    "            for k in range(cA):\n"
                    "                res[i][j] += A[i][k] * B[k][j]\n"
                    "    return res"
                ),
                explanation_depth="Validates dimension conditions (c1 == r2 for multiplication), iterates through row/column indices with O(n^3) time complexity.",
                assumptions_and_limitations="Assumes regular rectangular matrices of compatible numerical types.",
                verified=True,
            ),
            ReferenceTask(
                lab_id="DSA_LAB01",
                task_id=2,
                title="Matrix Transpose & Symmetry Check",
                original_task_statement="Write a program to find the transpose of a square matrix and determine whether it is symmetric.",
                subject="dsa",
                topic="Matrix Properties",
                keywords=["transpose", "symmetric matrix", "square matrix", "in-place", "symmetry"],
                solution_approach="Swaps A[i][j] with A[j][i] across main diagonal. Checks equality of original and transpose.",
                code_pattern=(
                    "def is_symmetric(matrix):\n"
                    "    n = len(matrix)\n"
                    "    for i in range(n):\n"
                    "        for j in range(i + 1, n):\n"
                    "            if matrix[i][j] != matrix[j][i]:\n"
                    "                return False\n"
                    "    return True"
                ),
                explanation_depth="Iterates strictly upper triangular entries in O(n^2) runtime to verify A == A^T.",
                assumptions_and_limitations="Requires square matrix (nxn).",
                verified=True,
            ),

            # -------------------------------------------------------------
            # DSA LAB 02: Singly Linked List
            # -------------------------------------------------------------
            ReferenceTask(
                lab_id="DSA_LAB02",
                task_id=1,
                title="Singly Linked List Implementation",
                original_task_statement="Implement a Singly Linked List with operations: insert at beginning, insert at end, delete node by value, and search.",
                subject="dsa",
                topic="Singly Linked List",
                keywords=["singly linked list", "linked list", "node", "insert at head", "insert at tail", "delete value", "pointer traversal"],
                solution_approach="Define explicit Node class with data and next pointer. SinglyLinkedList class manages head pointer.",
                code_pattern=(
                    "class Node:\n"
                    "    def __init__(self, data):\n"
                    "        self.data = data\n"
                    "        self.next = None\n\n"
                    "class SinglyLinkedList:\n"
                    "    def __init__(self):\n"
                    "        self.head = None\n\n"
                    "    def insert_at_beginning(self, data):\n"
                    "        new_node = Node(data)\n"
                    "        new_node.next = self.head\n"
                    "        self.head = new_node\n\n"
                    "    def insert_at_end(self, data):\n"
                    "        new_node = Node(data)\n"
                    "        if not self.head:\n"
                    "            self.head = new_node\n"
                    "            return\n"
                    "        curr = self.head\n"
                    "        while curr.next:\n"
                    "            curr = curr.next\n"
                    "        curr.next = new_node"
                ),
                explanation_depth="Covers pointer updates, null checks for empty lists, O(1) head insertion, and O(n) tail insertion.",
                assumptions_and_limitations="Unidirectional traversal; deletion requires tracking predecessor pointer.",
                verified=True,
            ),

            # -------------------------------------------------------------
            # DSA LAB 03: Doubly & Circular Linked Lists
            # -------------------------------------------------------------
            ReferenceTask(
                lab_id="DSA_LAB03",
                task_id=1,
                title="Doubly Linked List Bidirectional Traversal",
                original_task_statement="Implement a Doubly Linked List supporting forward and backward traversal and deletion at arbitrary index.",
                subject="dsa",
                topic="Doubly Linked List",
                keywords=["doubly linked list", "prev pointer", "next pointer", "bidirectional", "delete node"],
                solution_approach="Node holds data, next, and prev references. Operations update both forward and backward links synchronously.",
                code_pattern=(
                    "class DNode:\n"
                    "    def __init__(self, data):\n"
                    "        self.data = data\n"
                    "        self.prev = None\n"
                    "        self.next = None\n\n"
                    "class DoublyLinkedList:\n"
                    "    def __init__(self):\n"
                    "        self.head = None\n"
                    "        self.tail = None\n\n"
                    "    def append(self, data):\n"
                    "        new_node = DNode(data)\n"
                    "        if not self.head:\n"
                    "            self.head = self.tail = new_node\n"
                    "        else:\n"
                    "            self.tail.next = new_node\n"
                    "            new_node.prev = self.tail\n"
                    "            self.tail = new_node"
                ),
                explanation_depth="Maintains head and tail pointers for O(1) append and bidirectional iteration. Care taken when deleting head or tail.",
                assumptions_and_limitations="Requires 2x pointer storage overhead compared to singly linked list.",
                verified=True,
            ),
            ReferenceTask(
                lab_id="DSA_LAB03",
                task_id=2,
                title="Circular Linked List",
                original_task_statement="Implement a Circular Linked List where the last node points back to the head.",
                subject="dsa",
                topic="Circular Linked List",
                keywords=["circular linked list", "circular list", "last node points to head", "round robin"],
                solution_approach="Ensure tail.next always refers back to self.head. Traversal loops until curr.next == self.head.",
                code_pattern=(
                    "class CircularLinkedList:\n"
                    "    def __init__(self):\n"
                    "        self.head = None\n\n"
                    "    def append(self, data):\n"
                    "        new_node = Node(data)\n"
                    "        if not self.head:\n"
                    "            self.head = new_node\n"
                    "            new_node.next = self.head\n"
                    "            return\n"
                    "        curr = self.head\n"
                    "        while curr.next != self.head:\n"
                    "            curr = curr.next\n"
                    "        curr.next = new_node\n"
                    "        new_node.next = self.head"
                ),
                explanation_depth="Guarantees circularity for round-robin scheduling algorithms without encountering null pointer.",
                assumptions_and_limitations="Infinite loop risk if traversal condition checks curr is None instead of curr.next == head.",
                verified=True,
            ),

            # -------------------------------------------------------------
            # DSA LAB 04: Stacks, Queues & Priority Queues
            # -------------------------------------------------------------
            ReferenceTask(
                lab_id="DSA_LAB04",
                task_id=1,
                title="Stack & Balanced Parentheses",
                original_task_statement="Implement a LIFO Stack and use it to check whether brackets in an expression are balanced.",
                subject="dsa",
                topic="Stack & Expression Parsing",
                keywords=["stack", "lifo", "push", "pop", "peek", "balanced parentheses", "bracket matching"],
                solution_approach="Array-backed Stack class with push, pop, is_empty. Matching bracket dictionary for O(n) expression validation.",
                code_pattern=(
                    "class Stack:\n"
                    "    def __init__(self):\n"
                    "        self._items = []\n"
                    "    def push(self, val): self._items.append(val)\n"
                    "    def pop(self): return self._items.pop() if self._items else None\n"
                    "    def is_empty(self): return len(self._items) == 0\n\n"
                    "def is_balanced(expr):\n"
                    "    stk = Stack()\n"
                    "    mapping = {')': '(', '}': '{', ']': '['}\n"
                    "    for ch in expr:\n"
                    "        if ch in mapping.values(): stk.push(ch)\n"
                    "        elif ch in mapping.keys():\n"
                    "            if stk.is_empty() or stk.pop() != mapping[ch]: return False\n"
                    "    return stk.is_empty()"
                ),
                explanation_depth="LIFO processing ensures innermost opening bracket matches the first closing bracket encountered.",
                assumptions_and_limitations="Ignores non-bracket characters in expression string.",
                verified=True,
            ),
            ReferenceTask(
                lab_id="DSA_LAB04",
                task_id=2,
                title="Queue, Circular Queue & Priority Queue",
                original_task_statement="Implement a Circular Queue with fixed capacity and a Priority Queue ordered by priority key.",
                subject="dsa",
                topic="Queues & Priority Queues",
                keywords=["queue", "fifo", "circular queue", "enqueue", "dequeue", "priority queue", "deque"],
                solution_approach="Use modulo arithmetic (rear = (rear + 1) % size) for circular queue. Ordered insertion for priority queue.",
                code_pattern=(
                    "class CircularQueue:\n"
                    "    def __init__(self, capacity):\n"
                    "        self.cap = capacity\n"
                    "        self.q = [None] * capacity\n"
                    "        self.front = self.rear = -1\n\n"
                    "    def enqueue(self, val):\n"
                    "        if (self.rear + 1) % self.cap == self.front: return False  # Full\n"
                    "        if self.front == -1: self.front = 0\n"
                    "        self.rear = (self.rear + 1) % self.cap\n"
                    "        self.q[self.rear] = val\n"
                    "        return True\n\n"
                    "    def dequeue(self):\n"
                    "        if self.front == -1: return None  # Empty\n"
                    "        val = self.q[self.front]\n"
                    "        if self.front == self.rear: self.front = self.rear = -1\n"
                    "        else: self.front = (self.front + 1) % self.cap\n"
                    "        return val"
                ),
                explanation_depth="Circular indexing eliminates memory drift inherent in plain linear array queue shifting.",
                assumptions_and_limitations="Fixed capacity buffer; overflow condition returned cleanly as False.",
                verified=True,
            ),

            # -------------------------------------------------------------
            # DSA LAB 05: Sorting & Performance Benchmarking
            # -------------------------------------------------------------
            ReferenceTask(
                lab_id="DSA_LAB05",
                task_id=1,
                title="Sorting Algorithms & Execution Time Benchmarking",
                original_task_statement="Implement Bubble Sort, Selection Sort, Insertion Sort, Merge Sort, and Quick Sort. Benchmark runtime across array sizes 500, 5000, 10000.",
                subject="dsa",
                topic="Sorting & Empirical Complexity",
                keywords=["bubble sort", "selection sort", "insertion sort", "merge sort", "quick sort", "execution time", "worst case", "time complexity"],
                solution_approach="Implement pure algorithm functions without built-in sort. Use time.perf_counter() to measure execution times in milliseconds.",
                code_pattern=(
                    "import time\n\n"
                    "def bubble_sort(arr):\n"
                    "    a = arr.copy()\n"
                    "    n = len(a)\n"
                    "    for i in range(n):\n"
                    "        swapped = False\n"
                    "        for j in range(0, n - i - 1):\n"
                    "            if a[j] > a[j + 1]:\n"
                    "                a[j], a[j + 1] = a[j + 1], a[j]\n"
                    "                swapped = True\n"
                    "        if not swapped: break\n"
                    "    return a\n\n"
                    "def benchmark(algo_fn, data):\n"
                    "    t0 = time.perf_counter()\n"
                    "    algo_fn(data)\n"
                    "    return (time.perf_counter() - t0) * 1000.0"
                ),
                explanation_depth="Compares O(n^2) quadratic algorithms against O(n log n) divide-and-conquer algorithms under worst-case reversed arrays.",
                assumptions_and_limitations="Recursion depth limit for Quick Sort on sorted/reversed arrays mitigated by iterative partitioning or small sample tests.",
                verified=True,
            ),

            # -------------------------------------------------------------
            # DSA LAB 06: Iterative vs Recursive Binary Search
            # -------------------------------------------------------------
            ReferenceTask(
                lab_id="DSA_LAB06",
                task_id=1,
                title="Performance Comparison of Iterative and Recursive Binary Search",
                original_task_statement="Create a Python program that generates a sorted list containing at least 100,000 integers, searches for a target using both Iterative Binary Search and Recursive Binary Search, measures execution times with time.perf_counter(), displays search results and execution times, and compares both methods.",
                subject="dsa",
                topic="Searching Algorithms & Empirical Recursion Overhead",
                keywords=["binary search", "iterative binary search", "recursive binary search", "recursion overhead", "sorted array", "execution time", "100000 integers"],
                solution_approach="Implement while-loop iterative search and divide-and-conquer recursive search. Benchmark both on identical sorted dataset of 100,000 integers using time.perf_counter().",
                code_pattern=(
                    "import time\n\n"
                    "def iterative_binary_search(arr, target):\n"
                    "    low, high = 0, len(arr) - 1\n"
                    "    while low <= high:\n"
                    "        mid = (low + high) // 2\n"
                    "        if arr[mid] == target: return mid\n"
                    "        elif arr[mid] < target: low = mid + 1\n"
                    "        else: high = mid - 1\n"
                    "    return -1\n\n"
                    "def recursive_binary_search(arr, target, low, high):\n"
                    "    if low > high: return -1\n"
                    "    mid = (low + high) // 2\n"
                    "    if arr[mid] == target: return mid\n"
                    "    elif arr[mid] < target: return recursive_binary_search(arr, target, mid + 1, high)\n"
                    "    else: return recursive_binary_search(arr, target, low, mid - 1)\n"
                ),
                explanation_depth="Both algorithms exhibit O(log n) time complexity. Iterative execution outperforms recursive execution due to eliminating call stack allocation frames.",
                assumptions_and_limitations="Requires monotonically sorted array. Recursive approach is subject to call stack overhead on deep divides.",
                verified=True,
            ),

            # -------------------------------------------------------------
            # DBMS LAB 01: SQL Server Setup & Instance Architecture
            # -------------------------------------------------------------
            ReferenceTask(
                lab_id="DBMS_LAB01",
                task_id=1,
                title="SQL Server Connection & Server Metadata Verification",
                original_task_statement="Verify connection to local SQL Server instance in SSMS and query system properties.",
                subject="dbms",
                topic="SQL Server Environment & System Properties",
                keywords=["sql server 2022", "ssms", "object explorer", "instance", "@@version", "database engine", "system properties"],
                solution_approach="Execute standard SQL Server configuration and version functions via T-SQL.",
                code_pattern=(
                    "-- Verify SQL Server Version and Named Instance Name\n"
                    "SELECT @@VERSION AS [SQL Server Version];\n"
                    "SELECT @@SERVERNAME AS [Server Instance Name];\n\n"
                    "-- Inspect Database Engine Properties\n"
                    "SELECT SERVERPROPERTY('ProductVersion') AS ProductVersion,\n"
                    "       SERVERPROPERTY('Edition') AS Edition;"
                ),
                explanation_depth="Explains Database Engine as the core transaction/storage service and SSMS as the GUI client.",
                assumptions_and_limitations="Requires running SQL Server Database Engine service (SQLEXPRESS or default).",
                verified=True,
            ),

            # -------------------------------------------------------------
            # DBMS LAB 02: Database DDL (CREATE / ALTER / DROP DATABASE)
            # -------------------------------------------------------------
            ReferenceTask(
                lab_id="DBMS_LAB02",
                task_id=1,
                title="Database DDL Lifecycle & State Modification",
                original_task_statement="Write SQL statements to create, rename, change access modes (READ_ONLY, SINGLE_USER), take OFFLINE, bring ONLINE, and drop databases.",
                subject="dbms",
                topic="Database Management DDL",
                keywords=["create database", "alter database", "modify name", "set read_only", "set read_write", "single_user", "multi_user", "set offline", "set online", "drop database"],
                solution_approach="Use canonical T-SQL DDL statements. Use WITH ROLLBACK IMMEDIATE for connection isolation during state transitions.",
                code_pattern=(
                    "CREATE DATABASE Employee1;\n"
                    "ALTER DATABASE Employee1 MODIFY NAME = Employee;\n"
                    "ALTER DATABASE Employee SET READ_ONLY;\n"
                    "ALTER DATABASE Employee SET READ_WRITE;\n"
                    "ALTER DATABASE Student SET SINGLE_USER WITH ROLLBACK IMMEDIATE;\n"
                    "ALTER DATABASE Student SET MULTI_USER;\n"
                    "ALTER DATABASE Test SET OFFLINE;\n"
                    "ALTER DATABASE Test SET ONLINE;\n"
                    "DROP DATABASE Test;"
                ),
                explanation_depth="Modifies database catalog state in master database; rollbacks existing user transactions when entering SINGLE_USER mode.",
                assumptions_and_limitations="Requires sysadmin or dbcreator server roles in SQL Server.",
                verified=True,
            ),

            # -------------------------------------------------------------
            # DBMS LAB 03: Table DDL, Schema Definition & Alteration
            # -------------------------------------------------------------
            ReferenceTask(
                lab_id="DBMS_LAB03",
                task_id=1,
                title="Table DDL & Schema Evolution",
                original_task_statement="Create tables Student2 and Course2 with primary and foreign keys. Modify columns using ALTER TABLE, ADD, DROP COLUMN, and ALTER COLUMN.",
                subject="dbms",
                topic="Table DDL & Schema Management",
                keywords=["create table", "alter table", "add column", "drop column", "alter column", "primary key", "foreign key", "drop table"],
                solution_approach="Define parent table before referenced foreign key table. Execute schema alterations with proper T-SQL syntax.",
                code_pattern=(
                    "CREATE TABLE Course2 (\n"
                    "    CourseID VARCHAR(10) PRIMARY KEY,\n"
                    "    CourseName VARCHAR(50) NOT NULL,\n"
                    "    CreditHours INT NOT NULL\n"
                    ");\n\n"
                    "CREATE TABLE Student2 (\n"
                    "    StudentID VARCHAR(15) PRIMARY KEY,\n"
                    "    StudentName VARCHAR(50) NOT NULL,\n"
                    "    Age INT,\n"
                    "    CourseID VARCHAR(10),\n"
                    "    FOREIGN KEY (CourseID) REFERENCES Course2(CourseID)\n"
                    ");\n\n"
                    "ALTER TABLE Student2 ADD Email VARCHAR(50);\n"
                    "ALTER TABLE Student2 DROP COLUMN Age;\n"
                    "ALTER TABLE Student2 ALTER COLUMN StudentName VARCHAR(75);"
                ),
                explanation_depth="Enforces referential integrity between tables and demonstrates non-destructive schema evolution.",
                assumptions_and_limitations="Dropping a parent table requires dropping child foreign key constraint or child table first.",
                verified=True,
            ),

            # -------------------------------------------------------------
            # DBMS LAB 04: Integrity Constraints
            # -------------------------------------------------------------
            ReferenceTask(
                lab_id="DBMS_LAB04",
                task_id=1,
                title="SQL Integrity Constraints & Constraint Testing",
                original_task_statement="Create Employee table with PRIMARY KEY, NOT NULL, UNIQUE, CHECK, and DEFAULT constraints. Test violations for duplicate PK, duplicate UNIQUE, NULL, and CHECK.",
                subject="dbms",
                topic="Integrity Constraints",
                keywords=["sql constraints", "primary key", "not null", "unique", "check constraint", "default constraint", "violation error", "named constraint"],
                solution_approach="Define column-level and table-level constraints. Write deliberately invalid INSERT statements to demonstrate constraint enforcement.",
                code_pattern=(
                    "CREATE TABLE Employee (\n"
                    "    Employee_ID INT PRIMARY KEY,\n"
                    "    Employee_Name VARCHAR(50) NOT NULL,\n"
                    "    Email VARCHAR(100) UNIQUE,\n"
                    "    Age INT CHECK (Age >= 18),\n"
                    "    Department VARCHAR(50) DEFAULT 'Data Science',\n"
                    "    Gender CHAR(1) CHECK (Gender IN ('M', 'F'))\n"
                    ");\n\n"
                    "-- Valid Insert\n"
                    "INSERT INTO Employee VALUES (1, 'Ali Khan', 'ali@example.com', 22, 'Data Science', 'M');\n\n"
                    "-- Violation Test: Duplicate Primary Key\n"
                    "INSERT INTO Employee VALUES (1, 'Duplicate ID', 'dup@example.com', 24, 'Data Science', 'M');\n\n"
                    "-- Alter table to add named constraint\n"
                    "ALTER TABLE Project ADD CONSTRAINT UQ_ProjectCode UNIQUE (Project_Code);"
                ),
                explanation_depth="Validates domain integrity (CHECK), entity integrity (PRIMARY KEY), and semantic integrity (DEFAULT, NOT NULL).",
                assumptions_and_limitations="Violations terminate transaction with specific error levels (e.g. Msg 2627 for unique violation).",
                verified=True,
            ),

            # -------------------------------------------------------------
            # DBMS LAB 05: DML & SELECT Queries
            # -------------------------------------------------------------
            ReferenceTask(
                lab_id="DBMS_LAB05",
                task_id=1,
                title="DML Operations (INSERT, UPDATE, DELETE) & SELECT Projections",
                original_task_statement="Create CLIENT_MASTER, PRODUCT_MASTER, SALESMAN_MASTER tables, insert multi-row data, execute filtered SELECT queries, update records, and conditionally delete records.",
                subject="dbms",
                topic="Data Manipulation Language (DML)",
                keywords=["dml", "insert into", "update", "delete from", "select where", "client_master", "product_master", "salesman_master", "projections"],
                solution_approach="Multi-table creation, column-explicit and implicit inserts, filtered queries with WHERE clauses, updates, and targeted deletes.",
                code_pattern=(
                    "INSERT INTO CLIENT_MASTER (CLIENTNO, NAME, CITY, STATE, BALDUE)\n"
                    "VALUES ('C00001', 'Ivan Bayross', 'Karachi', 'Sindh', 1500.00);\n\n"
                    "SELECT NAME, CITY FROM CLIENT_MASTER WHERE CITY = 'Karachi';\n\n"
                    "UPDATE CLIENT_MASTER SET BALDUE = 1000.00 WHERE CLIENTNO = 'C00001';\n\n"
                    "DELETE FROM SALESMAN_MASTER WHERE SALARY = 3500.00;\n\n"
                    "SELECT * FROM CLIENT_MASTER;"
                ),
                explanation_depth="Details row-level modifications, atomic execution, and query projections under relational algebra.",
                assumptions_and_limitations="DELETE statements without WHERE clauses truncate entire table contents.",
                verified=True,
            ),
        ]

    def save(self):
        """Persists reference corpus to JSON file."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(e) for e in self.entries]
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self):
        """Loads reference corpus from JSON file."""
        with open(self.storage_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        self.entries = [ReferenceTask(**item) for item in raw]

    def find_relevant_references(
        self,
        subject: str,
        task_title: str,
        task_desc: str,
        exclude_lab_id: Optional[str] = None,
        max_results: int = 2
    ) -> List[ReferenceTask]:
        """
        Retrieves the most relevant reference tasks for an incoming assignment task.
        Guarantees that during leave-one-out testing, exclude_lab_id is completely held out.
        """
        sub_clean = (subject or "").lower().strip()
        query_text = f"{task_title} {task_desc}".lower()

        scored = []
        for entry in self.entries:
            # Exclude held-out lab
            if exclude_lab_id and entry.lab_id.lower() == exclude_lab_id.lower():
                continue

            # Subject match filter
            if sub_clean and entry.subject.lower() != sub_clean:
                continue

            score = 0
            for kw in entry.keywords:
                if kw.lower() in query_text:
                    score += 3
            if entry.topic.lower() in query_text:
                score += 5

            if score > 0:
                scored.append((score, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:max_results]]

    def format_guidance_for_prompt(self, references: List[ReferenceTask]) -> str:
        """Formats reference guidance to steer AI without answer copying."""
        if not references:
            return ""

        guidance_lines = [
            "ARCHITECTURAL & SOLUTION CONVENTIONS FROM VERIFIED LAB CORPUS:",
            "- Study the solution structure and coding style below for reference.",
            "- DO NOT copy the specific identifiers or data from the reference. Solve the ACTUAL requirements of the assigned task.",
        ]
        for ref in references:
            guidance_lines.append(f"\n[Exemplar Concept: {ref.topic}]")
            guidance_lines.append(f"Approach: {ref.solution_approach}")
            guidance_lines.append(f"Canonical Code Pattern:\n```\n{ref.code_pattern}\n```")
            guidance_lines.append(f"Explanation Style: {ref.explanation_depth}")

        return "\n".join(guidance_lines)
