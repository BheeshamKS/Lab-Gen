# LabGenius 🎓

> **Autonomous Academic Lab Completer & Authentic Screenshot Studio**  
> Takes your academic lab manuals, executes code directly on your laptop, captures authentic Pop!_OS terminal & browser screenshots, compiles a completed Word document (`.docx`), and scrubs all AI footprints so it passes human checks with 100% authenticity.

---

## ✨ Features

- **💻 Genuine Laptop Code Execution**: Runs your code directly on your Pop!_OS laptop using Python 3, GCC (C/C++), Bash, or SQLite. Auto-heals syntax or runtime errors automatically.
- **📸 Authentic Pop!_OS Screenshot Studio**: Captures realistic terminal windows featuring your actual username (`bheeshamks`), hostname (`pop-os`), native `Fira Mono` typography, window controls, and realistic command execution cycles with cursor blocks.
- **📈 Graphical Visualizations**: Automatically captures Matplotlib/Seaborn plots as crisp figure figures with formal captions (*"Figure 2.2: Matplotlib Scatter Trend Plot"*).
- **🛡️ 100% Anti-AI Sanitization & Metadata Cloaking**:
  - Unpacks the generated `.docx` archive and completely purges `<dc:creator>python-docx</dc:creator>`.
  - Injects your real student name (**Bheesham Kumar Sajnani**), roll number (**25F-DS-020**), and department (**Data Science**).
  - Simulates realistic human work: sets active editing time to ~75–100 minutes, realistic revision counts (5–8), and Microsoft Word tags.
  - Automatically filters out stereotypical AI buzzwords (*"delve", "crucial role", "testament", "pivotal", "in conclusion it is evident"*).
- **📝 Template Preservation**: If your professor gave you a `.docx` lab manual with university letterheads, logos, and tables, LabGenius fills your code, screenshots, and answers directly into the original document!
- **🌐 Interactive Web Dashboard + Fast CLI**: Use either the web interface with live screenshot previews or the command-line interface.

---

## 🚀 Quick Start

### 1. Web Dashboard (Interactive GUI)
Start the local web application:
```bash
./run_web.sh
```
Open your browser at **`http://127.0.0.1:8000`**.  
Drag & drop your lab manual (`.docx`, `.pdf`, `.txt`), or click **"Load Sample Data Science Lab 03"**, and click **"Solve Lab Tasks & Capture Screenshots"**.

### 2. Command-Line Interface (CLI)
To run on your university lab manual:
```bash
.venv/bin/python -m labgenius.cli --manual /path/to/your_lab_manual.docx
```

Or run the complete end-to-end demo:
```bash
./run_demo.py
```

---

## ⚙️ Configuration (`config.yaml`)

You can customize student details, terminal appearance, and AI provider in `config.yaml`:

```yaml
student:
  name: "Bheesham Kumar Sajnani"
  roll_number: "25F-DS-020"
  department: "Data Science"
  university: "Department of Data Science & Computing"

ai:
  # Provider: 'gemini', 'openai', 'anthropic', 'ollama', or 'mock'
  provider: "gemini"
  model: "gemini-2.5-flash"
  api_key_env: "GEMINI_API_KEY"
  persona: "undergraduate_student"
  scrub_buzzwords: true

terminal_capture:
  theme: "pop-os-dark"
  font_family: "Fira Mono, DejaVu Sans Mono, monospace"
  font_size: 13
  window_width: 820

document:
  font_family: "Calibri"
  realistic_editing_minutes: 85
  realistic_revisions: 6
```

---

## 🤖 Supported AI Providers

1. **Google Gemini (Recommended)**: Set `export GEMINI_API_KEY="your-key"` in your shell or enter it in the Web UI.
2. **OpenAI**: Set `export OPENAI_API_KEY="your-key"` (uses `gpt-4o-mini`).
3. **Local Ollama (100% Free & Offline)**: Run `ollama run qwen2.5-coder:7b` and set `provider: "ollama"`.
4. **Smart Offline Mode**: Built-in algorithmic solver for common Data Science (Pandas, NumPy, Matplotlib, Regression, EDA) and Computer Science tasks. Works instantly with zero setup or API keys.

---

## 📂 Project Structure

```
Lab-Gen/
├── config.yaml              # Student profile & system configuration
├── run_web.sh               # Web dashboard launch script
├── run_demo.py              # Self-contained end-to-end demo script
├── web_app.py               # FastAPI backend
├── web/                     # Frontend UI
│   ├── index.html           # Modern glassmorphic web dashboard
│   ├── style.css            # Dark mode aesthetic styling
│   └── app.js               # Client-side workflow logic
├── labgenius/               # Core Python package
│   ├── __init__.py
│   ├── config.py            # Profile & configuration loader
│   ├── parser.py            # DOCX & PDF task extraction engine
│   ├── solver.py            # Anti-AI student persona solver & buzzword scrubber
│   ├── runner.py            # Multi-language code runner with auto-healing
│   ├── capture.py           # Authentic Pop!_OS terminal & browser screenshot studio
│   ├── builder.py           # Document builder & template cloner
│   ├── sanitizer.py         # Deep metadata sanitizer (removes python-docx, sets real editing time)
│   └── cli.py               # Rich terminal CLI
├── examples/                # Sample lab manuals & generators
│   └── sample_lab_manual.docx
└── output/                  # Finalized, sanitized .docx and .pdf reports
```
