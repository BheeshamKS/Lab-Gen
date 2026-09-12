// LabGenius Web Interface Logic

let currentFile = null;
let timerInterval = null;
let secondsElapsed = 0;

document.addEventListener('DOMContentLoaded', () => {
  initProfile();
  setupDropZone();
  setupEventListeners();
});

function initProfile() {
  // Restore profile from localStorage if present
  const savedName = localStorage.getItem('lg_student_name');
  const savedRoll = localStorage.getItem('lg_roll_no');
  const savedDept = localStorage.getItem('lg_dept');
  const savedInst = localStorage.getItem('lg_instructor');
  const savedKey = localStorage.getItem('lg_api_key');
  const savedProvider = localStorage.getItem('lg_provider');

  if (savedName) document.getElementById('student-name').value = savedName;
  if (savedRoll) document.getElementById('roll-no').value = savedRoll;
  if (savedDept) document.getElementById('dept-name').value = savedDept;
  if (savedInst) document.getElementById('instructor-name').value = savedInst;
  if (savedKey) document.getElementById('api-key').value = savedKey;
  if (savedProvider) document.getElementById('ai-provider').value = savedProvider;

  updateProviderBadge();
}

function setupEventListeners() {
  const providerSelect = document.getElementById('ai-provider');
  providerSelect.addEventListener('change', () => {
    localStorage.setItem('lg_provider', providerSelect.value);
    updateProviderBadge();
  });

  document.getElementById('api-key').addEventListener('input', (e) => {
    localStorage.setItem('lg_api_key', e.target.value);
  });

  document.getElementById('student-name').addEventListener('input', (e) => {
    localStorage.setItem('lg_student_name', e.target.value);
  });

  document.getElementById('roll-no').addEventListener('input', (e) => {
    localStorage.setItem('lg_roll_no', e.target.value);
  });

  document.getElementById('dept-name').addEventListener('input', (e) => {
    localStorage.setItem('lg_dept', e.target.value);
  });

  const instInput = document.getElementById('instructor-name');
  if (instInput) {
    instInput.addEventListener('input', (e) => {
      localStorage.setItem('lg_instructor', e.target.value);
    });
  }

  // Toggle API Key visibility
  document.getElementById('btn-toggle-pass').addEventListener('click', () => {
    const input = document.getElementById('api-key');
    input.type = input.type === 'password' ? 'text' : 'password';
  });

  // Sample lab button
  document.getElementById('btn-sample-lab').addEventListener('click', (e) => {
    e.stopPropagation();
    loadSampleManual();
  });

  // Remove file button
  document.getElementById('btn-remove-file').addEventListener('click', (e) => {
    e.stopPropagation();
    clearSelectedFile();
  });

  // Run button
  document.getElementById('btn-run-all').addEventListener('click', runLabPipeline);

  // Modal close
  document.getElementById('modal-close').addEventListener('click', closeModal);
  document.getElementById('modal-overlay').addEventListener('click', (e) => {
    if (e.target.id === 'modal-overlay') closeModal();
  });
}

function updateProviderBadge() {
  const provider = document.getElementById('ai-provider').value;
  const badge = document.getElementById('provider-badge');
  if (provider === 'gemini-pro' || provider === 'gemini') badge.textContent = 'Gemini 2.5 Pro (Best)';
  else if (provider === 'gemini-flash') badge.textContent = 'Gemini 2.5 Flash';
  else if (provider === 'gemini-1.5-pro') badge.textContent = 'Gemini 1.5 Pro';
  else if (provider === 'mock') badge.textContent = 'Smart Offline Demo';
  else if (provider === 'openai') badge.textContent = 'OpenAI';
  else if (provider === 'ollama') badge.textContent = 'Local Ollama';
}

function setupDropZone() {
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-input');
  const browseBtn = document.getElementById('btn-browse');

  browseBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    fileInput.click();
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      handleFileSelected(e.target.files[0]);
    }
  });

  ['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.classList.remove('dragover');
    });
  });

  dropZone.addEventListener('drop', (e) => {
    if (e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });
}

function handleFileSelected(file) {
  currentFile = file;
  document.getElementById('selected-filename').textContent = file.name;
  document.getElementById('selected-file-info').style.display = 'flex';
  document.getElementById('btn-run-all').removeAttribute('disabled');
}

function clearSelectedFile() {
  currentFile = null;
  document.getElementById('file-input').value = '';
  document.getElementById('selected-file-info').style.display = 'none';
  document.getElementById('btn-run-all').setAttribute('disabled', 'true');
}

async function loadSampleManual() {
  try {
    const res = await fetch('/api/sample-manual');
    const data = await res.json();
    if (data.success) {
      currentFile = { name: data.filename, is_sample: true, sample_path: data.path };
      document.getElementById('selected-filename').textContent = data.filename;
      document.getElementById('selected-file-info').style.display = 'flex';
      document.getElementById('btn-run-all').removeAttribute('disabled');
    }
  } catch (err) {
    alert('Failed to load sample lab manual: ' + err);
  }
}

async function runLabPipeline() {
  if (!currentFile) return;

  // UI state transitions
  document.getElementById('upload-card').style.display = 'none';
  document.getElementById('progress-card').style.display = 'block';
  document.getElementById('results-container').style.display = 'none';

  startTimer();
  updateStep(1, 15, 'Parsing Lab Manual...', 'Extracting objectives and task problems...');

  const formData = new FormData();
  if (currentFile.is_sample) {
    formData.append('is_sample', 'true');
    formData.append('sample_path', currentFile.sample_path);
  } else {
    formData.append('manual_file', currentFile);
  }

  formData.append('name', document.getElementById('student-name').value);
  formData.append('roll_number', document.getElementById('roll-no').value);
  formData.append('department', document.getElementById('dept-name').value);
  const instVal = document.getElementById('instructor-name') ? document.getElementById('instructor-name').value : '';
  if (instVal) formData.append('instructor', instVal);
  formData.append('provider', document.getElementById('ai-provider').value);
  formData.append('api_key', document.getElementById('api-key').value);
  formData.append('theme', document.getElementById('terminal-theme').value);

  // Animate progress simulation while waiting for API
  setTimeout(() => updateStep(2, 35, 'Formulating Student Solutions...', 'Applying Anti-AI persona and writing undergraduate code...'), 1200);
  setTimeout(() => updateStep(3, 55, 'Executing Locally on Laptop...', 'Running code in workspace and collecting outputs...'), 2400);
  setTimeout(() => updateStep(4, 75, 'Capturing Pop!_OS Screenshots...', 'Rendering native terminal windows with Fira Mono...'), 3800);
  setTimeout(() => updateStep(5, 90, 'Deep Metadata Sanitization...', 'Rewriting docProps and wiping python-docx tags...'), 4900);

  try {
    const res = await fetch('/api/run', {
      method: 'POST',
      body: formData,
    });

    const result = await res.json();
    stopTimer();

    if (!result.success) {
      alert('Error during execution: ' + (result.error || 'Unknown error'));
      document.getElementById('upload-card').style.display = 'block';
      document.getElementById('progress-card').style.display = 'none';
      return;
    }

    // Complete progress
    updateStep(5, 100, 'Complete!', 'All tasks completed and verified.');
    setTimeout(() => {
      renderResults(result);
    }, 600);

  } catch (err) {
    stopTimer();
    alert('Pipeline request failed: ' + err);
    document.getElementById('upload-card').style.display = 'block';
    document.getElementById('progress-card').style.display = 'none';
  }
}

function updateStep(stepNum, percent, title, desc) {
  document.getElementById('progress-bar-fill').style.width = percent + '%';
  document.getElementById('progress-step-title').textContent = title;
  document.getElementById('progress-step-desc').textContent = desc;

  for (let i = 1; i <= 5; i++) {
    const el = document.getElementById(`step-${i}`);
    if (i < stepNum) {
      el.className = 'step-node completed';
    } else if (i === stepNum) {
      el.className = 'step-node active';
    } else {
      el.className = 'step-node';
    }
  }
}

function startTimer() {
  secondsElapsed = 0;
  timerInterval = setInterval(() => {
    secondsElapsed++;
    const m = Math.floor(secondsElapsed / 60).toString().padStart(2, '0');
    const s = (secondsElapsed % 60).toString().padStart(2, '0');
    document.getElementById('elapsed-timer').textContent = `${m}:${s}`;
  }, 1000);
}

function stopTimer() {
  clearInterval(timerInterval);
}

function renderResults(data) {
  document.getElementById('progress-card').style.display = 'none';
  document.getElementById('results-container').style.display = 'block';

  // Metadata Card
  document.getElementById('doc-title-text').textContent = data.filename;
  document.getElementById('meta-author').textContent = `Author: ${data.metadata.creator}`;
  document.getElementById('meta-time').textContent = `Active Edit Time: ${data.metadata.total_time_mins} mins`;
  document.getElementById('meta-rev').textContent = `Revision: ${data.metadata.revision}`;
  document.getElementById('btn-download').href = `/api/download/${data.filename}`;

  // Render Tasks Feed
  const feed = document.getElementById('tasks-feed');
  feed.innerHTML = '';

  data.tasks.forEach((task, idx) => {
    const card = document.createElement('div');
    card.className = 'card task-card';

    let plotHtml = '';
    if (task.plot_url) {
      plotHtml = `
        <div class="tab-pane" id="tab-plot-${idx}">
          <div class="screenshot-preview-wrapper" onclick="openModal('${task.plot_url}', 'Matplotlib Graphical Output - Task ${task.task_id}')">
            <img src="${task.plot_url}" alt="Graphical Plot">
            <p class="screenshot-caption">Figure: Graphical Visualization Plot (Click to zoom)</p>
          </div>
        </div>
      `;
    }

    card.innerHTML = `
      <div class="task-header">
        <div class="task-title-row">
          <span class="lang-tag">${task.language}</span>
          <h3>Task ${task.task_id}: ${escapeHtml(task.title)}</h3>
        </div>
      </div>
      <p class="task-desc">${escapeHtml(task.description)}</p>

      <div class="task-tabs">
        <button class="task-tab-btn active" onclick="switchTaskTab(${idx}, 'code-img')">Code Screenshot</button>
        <button class="task-tab-btn" onclick="switchTaskTab(${idx}, 'out-img')">Console Output Screenshot</button>
        <button class="task-tab-btn" onclick="switchTaskTab(${idx}, 'raw-code')">Raw Source Code</button>
      </div>

      <div class="tab-pane active" id="tab-code-img-${idx}">
        <div class="screenshot-preview-wrapper" onclick="openModal('${task.code_screenshot_url || task.screenshot_url}', 'Code Screenshot - Task ${task.task_id}')">
          <img src="${task.code_screenshot_url || task.screenshot_url}" alt="Code Screenshot">
          <p class="screenshot-caption">Figure: Code Screenshot (VS Code Light Theme) - Click to zoom</p>
        </div>
      </div>

      <div class="tab-pane" id="tab-out-img-${idx}">
        <div class="screenshot-preview-wrapper" onclick="openModal('${task.output_screenshot_url || task.screenshot_url}', 'Output Screenshot - Task ${task.task_id}')">
          <img src="${task.output_screenshot_url || task.screenshot_url}" alt="Output Screenshot">
          <p class="screenshot-caption">Figure: Console Output with Name &amp; Roll No - Click to zoom</p>
        </div>
      </div>

      <div class="tab-pane" id="tab-raw-code-${idx}">
        <div class="code-container">
          <button class="btn-copy-code" onclick="copyCode(this, \`${escapeJs(task.code)}\`)">Copy Code</button>
          <pre><code>${escapeHtml(task.code)}</code></pre>
        </div>
      </div>
    `;

    feed.appendChild(card);
  });
}

function switchTaskTab(taskIdx, tabName) {
  const card = document.querySelectorAll('.task-card')[taskIdx];
  const buttons = card.querySelectorAll('.task-tab-btn');
  const panes = card.querySelectorAll('.tab-pane');

  buttons.forEach(btn => btn.classList.remove('active'));
  panes.forEach(p => p.classList.remove('active'));

  event.target.classList.add('active');
  const targetPane = card.querySelector(`#tab-${tabName}-${taskIdx}`);
  if (targetPane) targetPane.classList.add('active');
}

function renderQA(answers) {
  if (!answers || Object.keys(answers).length === 0) {
    return '<p style="color: #94a3b8; font-size: 13px;">No explicit viva/discussion questions recorded for this task.</p>';
  }
  let html = '';
  for (const [q, a] of Object.entries(answers)) {
    html += `
      <div style="margin-bottom: 12px; background: rgba(255,255,255,0.02); padding: 10px 14px; border-radius: 8px; border-left: 3px solid #3b82f6;">
        <strong style="color: #f8fafc; font-size: 13px;">Q: ${escapeHtml(q)}</strong>
        <p style="color: #cbd5e1; font-size: 12.5px; margin-top: 4px;">Answer: ${escapeHtml(a)}</p>
      </div>
    `;
  }
  return html;
}

function copyCode(btn, code) {
  navigator.clipboard.writeText(code);
  const originalText = btn.textContent;
  btn.textContent = 'Copied!';
  setTimeout(() => btn.textContent = originalText, 1500);
}

function openModal(imgSrc, caption) {
  document.getElementById('modal-image').src = imgSrc;
  document.getElementById('modal-caption').textContent = caption;
  document.getElementById('modal-overlay').classList.add('active');
}

function closeModal() {
  document.getElementById('modal-overlay').classList.remove('active');
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function escapeJs(str) {
  if (!str) return '';
  return str.replace(/\\/g, '\\\\').replace(/`/g, '\\`').replace(/\$/g, '\\$');
}
