# LabGenius Studio 🎓

> **Autonomous Academic Lab Completer, Authentic Linux Screenshot Studio & Anti-AI Sanitizer**  
> Takes raw academic lab manuals (`.docx`, `.pdf`, `.txt`, `.md`), executes code locally on your laptop, captures authentic Linux terminal & browser screenshots, compiles a completed academic Word & PDF report with university cover pages, and scrubs all AI footprints so it passes human checks with 100% authenticity.

---

## ⚡ Highlights

- **💻 Genuine Multi-Language Execution**: Executes code natively on your laptop using **Python 3**, **C / C++ (GCC)**, **SQL (SQLite)**, or **Linux Bash**. Features an intelligent auto-healing loop that fixes syntax or runtime errors on the fly.
- **📸 Authentic Linux Terminal Screenshot Studio**: Generates realistic Linux terminal windows with custom username (`student`), hostname (`linux`), native `Fira Mono` / `JetBrains Mono` fonts, window controls, and realistic command execution cycles with block cursors (`█`).
- **🛡️ 100% Anti-AI Sanitization & Metadata Cloaking**:
  - Unpacks the generated `.docx` archive and completely purges `<dc:creator>python-docx</dc:creator>`.
  - Injects real student name, roll number, and department into document metadata.
  - Simulates realistic human work: sets active editing time to ~75–100 minutes, realistic revision counts (5–8), and authentic Microsoft Word application tags.
  - Automatically filters out stereotypical AI buzzwords (*"delve", "crucial role", "testament", "pivotal", "in conclusion it is evident"*).
- **🧠 Intelligent Lab Parser & Structure Engine**:
  - Dynamically extracts tasks from highly varied document styles (e.g., explicit "Experiment 1", numbered bullets, imperative action verbs).
  - Automatically identifies named sections like "Comparative Experiment", "Discussion Questions", and "Challenge Activity".
  - Detects and automatically attaches Observation Tables to the corresponding task for the AI to utilize.
- **🧼 Pure Clean Code Generation**:
  - **Zero student identity in code**: Student name and roll number are strictly excluded from source code comments and terminal `printf` / `print` outputs.
  - **Minimal to no comments**: Code is written in clean, concise, undergraduate human style without robotic step-by-step commentary.
- **📄 Official Academic First-Page / Cover Page**:
  - Direct integration of the Dawood University standard cover page layout.
  - **University Logo Controls**: Toggle university logo on/off (enabled by default). Includes dropdown selection defaulting to Dawood University with support for uploading custom institutional logos.
  - Includes university branding, Faculty of Computing and Information Technology, Department of Data Science & Cyber Security, Subject Name, Course Code, Lab Manual Title, Student Profile, and Performance / Submission Dates.
  - **Instructor Toggle**: Optional "Teacher's Name & Signature" row (disabled by default). When toggled off, no instructor fields or empty signature lines appear in the final document.
  - **Live Cover Details Modal**: Modify course title, subject code, roll number, or dates and re-render the cover page in real time.
- **⚡ High-Speed Groq Cloud API Support**:
  - Direct, lightning-fast inference using Groq Cloud's flagship **Llama 3.3 70B Versatile** and ultra-fast **Llama 3.1 8B Instant** models.
  - Seamlessly switch between Google Gemini Pro, Groq Cloud, OpenAI, or Smart Offline Mode.
- **🖤 Vercel / VS Code Monochrome Dark Studio UI**:
  - High-contrast pure black and white aesthetic with sharp 6px/8px corners, subtle borders, and clean typography.
  - **Inline WYSIWYG Editable Document Canvas**: Click any paragraph, table cell, or header in the live preview and edit text directly. Use the formatting toolbar (Bold, Italic, Code, Headings, Lists) and hit `Ctrl+S` to save.
  - **Real-Time Document Recompilation**: Live canvas edits are automatically persisted back to `.docx` and `.pdf` builds.
  - **Live Code Playground**: Test and run C, Python, SQL, or Bash code on the fly with a simulated interactive terminal window.
  - **Fresh Screenshot Rendering**: Real-time cache busting guarantees that newly executed tasks immediately show their unique terminal screenshots without stale browser memory caching.
- **📦 Clean Academic Export Formats**:
  - Focused strictly on university submission formats: `.docx` (Sanitized Word) and `.pdf` (Print-Ready PDF via LibreOffice).
  - **1-Click Submission ZIP**: Downloads a complete submission bundle containing the final `.docx`, `.pdf`, raw source code files (`.c`, `.py`, `.sql`), and high-resolution terminal screenshots (`.png`).
  - **Multi-Lab Session Management**: Easily close the current lab and upload a new manual without restarting the server.

---

## 🖥️ UI / UX Preview

The Web Studio is engineered with a strict **Vercel / VS Code Monochrome Dark Aesthetic** (`#000000` / `#0a0a0a` background, sharp edges, high-contrast white action buttons, and keyboard navigation):

| View | Description |
| :--- | :--- |
| **Studio Document Preview & WYSIWYG Canvas** | Full-fidelity document preview with Dawood University cover page, inline text editing, live save status pill, and format toolbar. |
| **Interactive Code Playground** | Ad-hoc code execution for Python, C (`-lm`), SQL, and Bash with real-time stdout/stderr and Linux terminal simulator. |
| **Task Breakdown Cards** | Clean task cards with sub-tabs for Code Screenshot, Console Screenshot, and Raw Source Code. |
| **Cover Page Details Modal** | Dedicated editor for course name, subject code, student details, submission dates, and instructor toggle. |
| **Streamlined Upload Stage** | Focused dropzone supporting drag-and-drop `.docx`, `.pdf`, `.txt`, custom solver instructions, and export selection. |

---

## 🚀 Quick Start

### 1. Launch the Web Studio (Recommended)

Start the local web application:
```bash
./run_web.sh
```
Or run directly via Uvicorn (with restricted reload directories to prevent generation loops):
```bash
.venv/bin/uvicorn web_app:app --host 127.0.0.1 --port 8000 --reload --reload-dir labgenius --reload-dir web --reload-include web_app.py
```
Open **`http://127.0.0.1:8000`** in your browser.

- **Drop your lab manual** (`.docx`, `.pdf`, `.txt`, `.md`) onto the upload zone, or click **"Load Sample Data Science Lab 03"**.
- Optionally add custom solver instructions (e.g. *"Use Python 3.10 list comprehensions"*, *"Keep explanations concise"*).
- Click **"Solve Lab Tasks & Capture Screenshots"**.
- Preview the generated report, edit any text directly on the canvas, run code in the playground, or click **"Submission ZIP"** to download your final files.

### 2. Command-Line Interface (CLI)

Run directly on your university lab manual:
```bash
.venv/bin/python -m labgenius.cli --manual /path/to/your_lab_manual.docx
```

#### CLI Flags & Options:
```bash
python3 -m labgenius.cli \
  --manual examples/sample_lab_manual.docx \
  --output output/Completed_Lab_Report.docx \
  --name "Bheesham Kumar Sajnani" \
  --roll "25F-DS-020" \
  --dept "Data Science" \
  --section "25F-DS" \
  --include-instructor \
  --instructor "Engr. Instructor Name" \
  --provider gemini \
  --model gemini-2.5-flash
```

| Flag | Short | Description | Default |
| :--- | :--- | :--- | :--- |
| `--manual` | `-m` | Path to lab manual (`.docx`, `.pdf`, `.txt`) | `examples/sample_lab_manual.docx` |
| `--output` | `-o` | Output path for completed report | `output/LABxx_completed.docx` |
| `--name` | | Override student full name | From `config.yaml` |
| `--roll` | | Override student roll number | From `config.yaml` |
| `--dept` | | Override department | From `config.yaml` |
| `--section` | | Override class section | From `config.yaml` |
| `--include-instructor` | | Include teacher row in cover page table | `False` (disabled) |
| `--instructor` | | Teacher name (only if included) | `""` |
| `--provider` | | AI provider (`gemini`, `openai`, `ollama`, `mock`) | From `config.yaml` |
| `--model` | | Specific model name | `gemini-2.5-flash` |
| `--dry-run` | | Parse manual & show tasks without executing | `False` |
| `--config` | `-c` | Path to custom YAML configuration | `config.yaml` |

### 3. Run Self-Contained Demo
```bash
./run_demo.py
```
Demonstrates parsing, code execution, Linux terminal capture, Word compilation, metadata cloaking, and anti-AI verification.

---

## 🛠️ Supported Languages & Runtimes

| Language | Runtime / Compiler | Capabilities |
| :--- | :--- | :--- |
| **Python 3** | Native `python3` | NumPy, Pandas, Matplotlib, Seaborn, Scikit-learn, DSA algorithms. Graphical plots are automatically captured and captioned. |
| **C** | `gcc -O2 -lm` | Standard C11 / C99 with math library linking. Pointer manipulation, arrays, memory management. |
| **C++** | `g++ -std=c++17 -O2 -lm` | Standard C++ with STL (vectors, maps, sets, algorithms). |
| **SQL** | SQLite 3 | Automated schema initialization, table creation, joins, aggregations, and formatted ASCII query tables. |
| **Bash** | Linux `/bin/bash` | Native shell scripting, piping, file system utilities, environment variable analysis. |

---

## ⚙️ Configuration (`config.yaml`)

Configure your default student profile, terminal appearance, and AI provider in `config.yaml`:

```yaml
student:
  name: "Bheesham Kumar Sajnani"
  roll_number: "25F-DS-020"
  department: "Data Science"
  university: "Department of Data Science & Computing"
  section: "25F-DS"
  batch: "2025"
  semester: "1st"
  include_instructor: false      # Toggle teacher name/signature on cover page (default: false)
  instructor: ""

ai:
  provider: "gemini"             # Options: 'gemini', 'openai', 'anthropic', 'ollama', or 'mock'
  model: "gemini-2.5-flash"
  api_key_env: "GEMINI_API_KEY"
  persona: "undergraduate_student"
  scrub_buzzwords: true          # Removes generic AI buzzwords from discussions

terminal_capture:
  theme: "linux-dark"
  font_family: "Fira Mono, DejaVu Sans Mono, monospace"
  font_size: 13
  window_width: 820
  username: "student"            # Dynamic terminal user prompt
  hostname: "linux"              # Dynamic host prompt

document:
  font_family: "Calibri"
  realistic_editing_minutes: 85  # Human-like Word editing metadata
  realistic_revisions: 6         # Human-like Word revision count
```

---

## 🤖 Supported Intelligence Modes

1. **Google Gemini (Recommended)**: Set `export GEMINI_API_KEY="your-key"` in your shell or enter it directly in the Web UI. Supports `gemini-2.5-flash` and `gemini-2.5-pro`.
2. **OpenAI**: Set `export OPENAI_API_KEY="your-key"` (uses `gpt-4o-mini` or `gpt-4o`).
3. **Groq / OpenRouter**: Ultra-fast generation using `GROQ_API_KEY` or custom OpenAI bases with seamless drop-in routing (e.g., `llama3-8b-8192`).
4. **Local Ollama (100% Free & Offline)**: Run `ollama run qwen2.5-coder:7b` and set `provider: "ollama"`.
5. **Smart Offline Mode (`mock`)**: Built-in algorithmic solver with 18+ pre-engineered templates covering Data Science (Pandas, NumPy, Matplotlib, Regression, EDA), Computer Science, and Data Structures & Algorithms. Runs instantly with zero API keys or external network calls.

---

## 🌐 REST API Reference

The FastAPI backend (`web_app.py`) provides a complete RESTful API:

| Method | Endpoint | Description | Request Body / Parameters |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Web Studio Single-Page Application | None |
| `GET` | `/api/sample-manual` | Returns pre-built sample lab manual text | None |
| `POST` | `/api/run` | Main pipeline: solves tasks, executes code, captures terminal screenshots, and builds reports | Multipart form (`manual_file`, `manual_text`, `custom_instructions`, `student_name`, `roll_number`, `department`, `section`, `include_instructor`, `api_key`, `model`, `username`, `hostname`, `export_formats`) |
| `POST` | `/api/refine` | Refines an entire lab or specific task using natural language prompts | JSON: `{ "instruction": str, "scope": str }` |
| `POST` | `/api/edit-task` | Re-executes a single task with custom code or updated explanation | JSON: `{ "task_id": int, "code": str, "explanation": str }` |
| `POST` | `/api/edit-cover` | Updates cover page metadata and re-renders cover page | JSON: `{ "subject_name": str, "subject_code": str, "lab_title": str, "student_name": str, "roll_number": str, "batch": str, "semester": str, "date_perf": str, "date_sub": str, "include_instructor": bool, "instructor": str }` |
| `GET` | `/api/current-lab` | Retrieves current lab state, tasks, code, screenshots, and document content | None |
| `POST` | `/api/save-document-canvas` | Saves WYSIWYG HTML edits and recompiles `.docx`, `.pdf`, `.html`, and `.md` | JSON: `{ "html_content": str }` |
| `POST` | `/api/execute-scratchpad` | Executes ad-hoc code in Python, C, SQL, or Bash and returns stdout/stderr | JSON: `{ "language": str, "code": str, "stdin": str }` |
| `GET` | `/api/templates` | Returns algorithmic & Data Science starter templates | None |
| `GET` | `/api/download-bundle` | Packages all files (`.docx`, `.pdf`, `.html`, `.md`, source code, screenshots) into a `.zip` | None |
| `GET` | `/api/download/{filename}` | Downloads a specific generated file (`.docx`, `.pdf`, `.html`, `.md`) | Path param: `filename` |
| `GET` | `/api/preview/pdf/{filename}` | Serves high-resolution PDF preview stream | Path param: `filename` |
| `GET` | `/api/preview/html/{filename}` | Serves embedded HTML report | Path param: `filename` |
| `POST` | `/api/close-lab` | Resets active lab session for uploading a new manual | None |

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action | Scope |
| :--- | :--- | :--- |
| `Ctrl + S` / `⌘ + S` | Save Canvas Edits & Recompile Reports | Studio Canvas |
| `Ctrl + Enter` / `⌘ + Enter` | Run Code in Playground | Code Playground |
| `Ctrl + N` / `⌘ + N` | Open "New Lab" Upload Modal | Everywhere |
| `⌘ + K` | Toggle Keyboard Shortcuts Modal | Everywhere |
| `Esc` | Dismiss Open Modals & Dialogs | Everywhere |
| `?` | Show Shortcuts Cheat Sheet | Everywhere |

---

## 📂 Project Architecture

```
Lab-Gen/
├── config.yaml              # Student profile, terminal theme, and AI configuration
├── run_web.sh               # One-click web dashboard launcher
├── run_demo.py              # End-to-end self-contained verification demo
├── web_app.py               # FastAPI backend & REST API endpoints
├── web/                     # Vercel-style Monochrome Dark Frontend
│   ├── index.html           # Studio dashboard structure & modals
│   ├── style.css            # Strict monochrome design system & typography
│   └── app.js               # Reactive client-side logic & canvas sync
├── labgenius/               # Core Python engine
│   ├── __init__.py
│   ├── config.py            # YAML configuration loader & validation
│   ├── parser.py            # DOCX / PDF / TXT task extraction & table parser
│   ├── solver.py            # AI solver, clean code post-processor & buzzword scrubber
│   ├── runner.py            # Native multi-language code runner (Python, C, C++, Bash)
│   ├── sql_runner.py        # SQLite query executor & ASCII table formatter
│   ├── capture.py           # Authentic Linux terminal & graph screenshot studio
│   ├── builder.py           # Academic document compiler & cover page builder
│   ├── sanitizer.py         # Word XML unpacker, metadata cloaker & anti-AI scrubber
│   └── cli.py               # Rich terminal CLI runner
├── examples/                # Sample lab manuals & university templates
│   ├── sample_lab_manual.docx
│   └── first-page.doc       # Official Dawood University reference cover page
└── output/                  # Finalized, sanitized .docx, .pdf, .html, and .zip files
```

---

## 🛡️ Anti-AI & Human Authenticity Verification

When submitting university lab reports, automated systems and human graders inspect document metadata and code structure for signs of AI generation. LabGenius applies a comprehensive four-layer humanization process:

1. **Document Metadata Purge (`sanitizer.py`)**:
   Standard Python libraries inject telltale signatures like `<dc:creator>python-docx</dc:creator>` into the document XML. LabGenius unpacks the Word package, strips all library signatures, replaces them with your configured student profile, and injects realistic Microsoft Office metadata (`Word.Document`, `w:TotalTime`, `cp:revision`).
2. **Realistic Edit Duration**:
   Instead of an instantaneous 0-second file creation time, LabGenius calculates an authentic editing span (~75 to 100 minutes) across 5 to 8 incremental revisions.
3. **Clean Code Protocol**:
   Unlike standard AI chatbots that prepend verbose boilerplate comments (`/* Author: Student Name, Roll: ... */`) and step-by-step commentary (`// Step 1: Initialize variable i`), LabGenius outputs concise, natural undergraduate code. Student identity is strictly isolated to the academic cover page.
4. **Vocabulary & Tone Filter**:
   Natural language answers are scrubbed of high-frequency LLM markers (*"delve", "crucial role", "testament", "pivotal", "in conclusion it is evident"*), ensuring explanations read like genuine student coursework.

---

## ⚖️ Academic Integrity & Disclaimer

LabGenius is built as an educational workflow accelerator and assistive study tool. Users remain responsible for understanding the code and coursework generated. Ensure compliance with your academic institution's policies and guidelines regarding assistive software and automated compilation tools.
