// LabGenius IDE Studio Interface Logic
// Vercel / VS Code / Antigravity Dark Theme & Interactive Studio Engine

let currentFile = null;
let timerInterval = null;
let secondsElapsed = 0;
let currentLabData = null;
let cachedTemplates = [];
let isCanvasDirty = false;

document.addEventListener('DOMContentLoaded', () => {
  initProfile();
  setupDropZone();
  setupEventListeners();
  setupPlayground();
  setupKeyboardShortcuts();
  restoreActiveLabSession();
});

function initProfile() {
  const savedName = localStorage.getItem('lg_student_name');
  const savedRoll = localStorage.getItem('lg_roll_no');
  const savedSection = localStorage.getItem('lg_section');
  const savedDept = localStorage.getItem('lg_dept');
  const savedInst = localStorage.getItem('lg_instructor');
  const savedIncludeInst = localStorage.getItem('lg_include_instructor');
  const savedKey = localStorage.getItem('lg_api_key');
  const savedProvider = localStorage.getItem('lg_provider');

  if (savedName && document.getElementById('student-name')) document.getElementById('student-name').value = savedName;
  if (savedRoll && document.getElementById('roll-no')) document.getElementById('roll-no').value = savedRoll;
  if (savedSection && document.getElementById('section-name')) document.getElementById('section-name').value = savedSection;
  if (savedDept && document.getElementById('dept-name')) document.getElementById('dept-name').value = savedDept;
  if (savedInst && document.getElementById('instructor-name')) document.getElementById('instructor-name').value = savedInst;
  if (savedKey && document.getElementById('api-key')) document.getElementById('api-key').value = savedKey;
  if (savedProvider && document.getElementById('ai-provider')) document.getElementById('ai-provider').value = savedProvider;

  // Instructor toggle: OFF by default
  const toggleInst = document.getElementById('toggle-instructor');
  const instWrapper = document.getElementById('instructor-input-wrapper');
  if (toggleInst && instWrapper) {
    if (savedIncludeInst === 'true') {
      toggleInst.checked = true;
      instWrapper.style.display = 'block';
    } else {
      toggleInst.checked = false;
      instWrapper.style.display = 'none';
    }
  }

  // University Logo toggle & choice: ON and 'dawood' by default
  const savedIncludeLogo = localStorage.getItem('lg_include_logo');
  const savedLogoChoice = localStorage.getItem('lg_logo_choice') || 'dawood';
  const savedCustomLogoUrl = localStorage.getItem('lg_custom_logo_url');

  const toggleUniLogo = document.getElementById('toggle-uni-logo');
  const logoOptionsWrap = document.getElementById('logo-options-wrapper');
  const logoChoiceSelect = document.getElementById('logo-choice-select');
  const customLogoWrap = document.getElementById('custom-logo-upload-wrapper');
  const customLogoPreview = document.getElementById('custom-logo-preview');

  if (toggleUniLogo) {
    const isLogoOn = savedIncludeLogo !== 'false'; // default true
    toggleUniLogo.checked = isLogoOn;
    if (logoOptionsWrap) logoOptionsWrap.style.display = isLogoOn ? 'block' : 'none';
  }

  if (logoChoiceSelect) {
    logoChoiceSelect.value = savedLogoChoice;
    if (customLogoWrap) customLogoWrap.style.display = savedLogoChoice === 'custom' ? 'block' : 'none';
  }

  if (savedCustomLogoUrl && customLogoPreview) {
    customLogoPreview.src = savedCustomLogoUrl;
  }

  updateProviderBadge();
  initTerminalSettings();
}

function initTerminalSettings() {
  let savedUser = localStorage.getItem('lg_terminal_user');
  if (!savedUser || savedUser === 'bheeshamks') savedUser = 'student';
  let savedHost = localStorage.getItem('lg_terminal_host');
  if (!savedHost || savedHost === 'pop-os') savedHost = 'linux';

  const userEl = document.getElementById('terminal-username');
  const hostEl = document.getElementById('terminal-hostname');

  if (userEl) userEl.value = savedUser;
  if (hostEl) hostEl.value = savedHost;

  updateTerminalPromptSettings();
}

function updateTerminalPromptSettings() {
  const user = document.getElementById('terminal-username')?.value.trim() || 'student';
  const host = document.getElementById('terminal-hostname')?.value.trim() || 'linux';

  localStorage.setItem('lg_terminal_user', user);
  localStorage.setItem('lg_terminal_host', host);

  // Update shell preview in sidebar
  const promptPreview = document.getElementById('terminal-prompt-preview');
  if (promptPreview) {
    promptPreview.value = `${user}@${host}:~/workspace$`;
  }

  // Update navbar user pill
  const userEnvPill = document.getElementById('user-env-pill');
  if (userEnvPill) {
    userEnvPill.textContent = `${user}@${host}`;
  }

  // Update playground terminal prompt line
  const termUserPrompt = document.getElementById('term-user-prompt');
  if (termUserPrompt) {
    termUserPrompt.textContent = `${user}@${host}`;
  }

  // Update terminal window title
  const termTitle = document.getElementById('terminal-pane-title');
  if (termTitle) {
    const lang = document.getElementById('scratch-lang')?.value || 'python';
    const langDetail = lang === 'c' ? '(gcc 13.3 -lm)' : (lang === 'sql' ? '(SQLite 3.45)' : '(Python 3.12)');
    termTitle.textContent = `terminal — ${host} ${langDetail}`;
  }
}

function setupEventListeners() {
  const providerSelect = document.getElementById('ai-provider');
  if (providerSelect) {
    providerSelect.addEventListener('change', () => {
      localStorage.setItem('lg_provider', providerSelect.value);
      updateProviderBadge();
    });
  }

  const apiKeyInput = document.getElementById('api-key');
  if (apiKeyInput) {
    apiKeyInput.addEventListener('input', (e) => {
      localStorage.setItem('lg_api_key', e.target.value);
    });
  }

  const nameInput = document.getElementById('student-name');
  if (nameInput) {
    nameInput.addEventListener('input', (e) => {
      localStorage.setItem('lg_student_name', e.target.value);
    });
  }

  const rollInput = document.getElementById('roll-no');
  if (rollInput) {
    rollInput.addEventListener('input', (e) => {
      localStorage.setItem('lg_roll_no', e.target.value);
    });
  }

  const secInput = document.getElementById('section-name');
  if (secInput) {
    secInput.addEventListener('input', (e) => {
      localStorage.setItem('lg_section', e.target.value);
    });
  }

  const deptInput = document.getElementById('dept-name');
  if (deptInput) {
    deptInput.addEventListener('input', (e) => {
      localStorage.setItem('lg_dept', e.target.value);
    });
  }

  const instInput = document.getElementById('instructor-name');
  if (instInput) {
    instInput.addEventListener('input', (e) => {
      localStorage.setItem('lg_instructor', e.target.value);
    });
  }

  const toggleInst = document.getElementById('toggle-instructor');
  const instWrapper = document.getElementById('instructor-input-wrapper');
  if (toggleInst && instWrapper) {
    toggleInst.addEventListener('change', (e) => {
      instWrapper.style.display = e.target.checked ? 'block' : 'none';
      localStorage.setItem('lg_include_instructor', e.target.checked ? 'true' : 'false');
      if (currentLabData) {
        renderFullDocument(currentLabData);
      }
    });
  }

  // Cover edit modal instructor toggle
  const editCoverToggle = document.getElementById('edit-cover-toggle-inst');
  const editCoverInstWrap = document.getElementById('edit-cover-inst-wrapper');
  if (editCoverToggle && editCoverInstWrap) {
    editCoverToggle.addEventListener('change', (e) => {
      editCoverInstWrap.style.display = e.target.checked ? 'block' : 'none';
    });
  }

  // Toggle API Key visibility
  const btnTogglePass = document.getElementById('btn-toggle-pass');
  if (btnTogglePass) {
    btnTogglePass.addEventListener('click', () => {
      const input = document.getElementById('api-key');
      input.type = input.type === 'password' ? 'text' : 'password';
    });
  }

  // Sample lab button
  const btnSampleLab = document.getElementById('btn-sample-lab');
  if (btnSampleLab) {
    btnSampleLab.addEventListener('click', (e) => {
      e.stopPropagation();
      loadSampleManual();
    });
  }

  // Remove file button
  const btnRemoveFile = document.getElementById('btn-remove-file');
  if (btnRemoveFile) {
    btnRemoveFile.addEventListener('click', (e) => {
      e.stopPropagation();
      clearSelectedFile();
    });
  }

  // Run button
  const btnRunAll = document.getElementById('btn-run-all');
  if (btnRunAll) {
    btnRunAll.addEventListener('click', runLabPipeline);
  }

  // Refine button & enter key
  const btnRefine = document.getElementById('btn-apply-refine');
  if (btnRefine) {
    btnRefine.addEventListener('click', handleRefineSubmit);
  }
  const inputRefine = document.getElementById('refine-input');
  if (inputRefine) {
    inputRefine.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') handleRefineSubmit();
    });
  }

  // Lightbox Modal close
  const modalClose = document.getElementById('modal-close');
  if (modalClose) modalClose.addEventListener('click', closeModal);
  const modalOverlay = document.getElementById('modal-overlay');
  if (modalOverlay) {
    modalOverlay.addEventListener('click', (e) => {
      if (e.target.id === 'modal-overlay') closeModal();
    });
  }

  // Shortcuts overlay click
  const shortcutsOverlay = document.getElementById('shortcuts-modal-overlay');
  if (shortcutsOverlay) {
    shortcutsOverlay.addEventListener('click', (e) => {
      if (e.target.id === 'shortcuts-modal-overlay') closeShortcutsModal();
    });
  }

  // Canvas change listener for unsaved status indicator
  const canvas = document.getElementById('doc-canvas');
  if (canvas) {
    canvas.addEventListener('input', () => {
      markCanvasDirty();
    });
  }
}

function markCanvasDirty() {
  isCanvasDirty = true;
  const indicator = document.getElementById('editor-status-indicator');
  if (indicator) {
    indicator.textContent = '● Unsaved Canvas Changes (Ctrl+S to save)';
    indicator.className = 'editor-mode-badge dirty';
  }
  const saveStatus = document.getElementById('canvas-save-status');
  if (saveStatus) {
    saveStatus.textContent = '● Unsaved Changes (Ctrl+S)';
    saveStatus.className = 'canvas-save-status unsaved';
  }
}

function markCanvasSaved() {
  isCanvasDirty = false;
  const indicator = document.getElementById('editor-status-indicator');
  if (indicator) {
    indicator.textContent = '● All Changes Saved & Recompiled';
    indicator.className = 'editor-mode-badge saved';
    setTimeout(() => {
      if (!isCanvasDirty && indicator) {
        indicator.textContent = '● Edit Mode Active';
        indicator.className = 'editor-mode-badge';
      }
    }, 3500);
  }
  const saveStatus = document.getElementById('canvas-save-status');
  if (saveStatus) {
    saveStatus.textContent = '✓ All Edits Saved';
    saveStatus.className = 'canvas-save-status';
  }
  showToast('All edits saved & recompiled successfully!');
}

function setupKeyboardShortcuts() {
  window.addEventListener('keydown', (e) => {
    // Ctrl+S or Cmd+S -> Save Document Canvas
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
      e.preventDefault();
      saveDocumentCanvasEdits();
      return;
    }

    // Ctrl+K or Cmd+K -> Shortcuts Modal
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      toggleShortcutsModal();
      return;
    }

    // Ctrl+Enter -> Run Scratchpad Code
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      const scratchContainer = document.getElementById('view-scratchpad-container');
      if (scratchContainer && scratchContainer.style.display !== 'none') {
        e.preventDefault();
        runPlaygroundCode();
        return;
      }
    }

    // Escape -> Close any open modal
    if (e.key === 'Escape') {
      closeModal();
      closeEditModal();
      closeCoverEditModal();
      closeShortcutsModal();
    }
  });

  // Support Tab key indentation inside the scratchpad textarea
  const scratchCodeArea = document.getElementById('scratch-code');
  if (scratchCodeArea) {
    scratchCodeArea.addEventListener('keydown', function(e) {
      if (e.key === 'Tab') {
        e.preventDefault();
        const start = this.selectionStart;
        const end = this.selectionEnd;
        this.value = this.value.substring(0, start) + '    ' + this.value.substring(end);
        this.selectionStart = this.selectionEnd = start + 4;
      }
    });
  }
}

function openShortcutsModal() {
  const overlay = document.getElementById('shortcuts-modal-overlay');
  if (overlay) overlay.classList.add('active');
}

function closeShortcutsModal() {
  const overlay = document.getElementById('shortcuts-modal-overlay');
  if (overlay) overlay.classList.remove('active');
}

function toggleShortcutsModal() {
  const overlay = document.getElementById('shortcuts-modal-overlay');
  if (!overlay) return;
  if (overlay.classList.contains('active')) closeShortcutsModal();
  else openShortcutsModal();
}

function handleLogoToggleChange() {
  const toggle = document.getElementById('toggle-uni-logo');
  const optionsWrapper = document.getElementById('logo-options-wrapper');
  if (!toggle) return;
  const isOn = toggle.checked;
  if (optionsWrapper) optionsWrapper.style.display = isOn ? 'block' : 'none';
  localStorage.setItem('lg_include_logo', isOn ? 'true' : 'false');
  if (currentLabData) {
    renderFullDocument(currentLabData);
  }
}

function handleLogoChoiceChange() {
  const choiceSelect = document.getElementById('logo-choice-select');
  const customWrapper = document.getElementById('custom-logo-upload-wrapper');
  if (!choiceSelect) return;
  const val = choiceSelect.value;
  if (customWrapper) customWrapper.style.display = val === 'custom' ? 'block' : 'none';
  localStorage.setItem('lg_logo_choice', val);
  if (currentLabData) {
    renderFullDocument(currentLabData);
  }
}

async function handleCustomLogoSelected(event) {
  const file = event.target?.files?.[0];
  if (!file) return;

  const statusEl = document.getElementById('custom-logo-status');
  const previewImg = document.getElementById('custom-logo-preview');
  if (statusEl) statusEl.textContent = 'Uploading...';

  const formData = new FormData();
  formData.append('logo_file', file);

  try {
    const res = await fetch('/api/upload-logo', {
      method: 'POST',
      body: formData,
    });
    const data = await res.json();
    if (data.success) {
      if (previewImg) previewImg.src = data.url;
      if (statusEl) statusEl.textContent = file.name;
      localStorage.setItem('lg_custom_logo_url', data.url);
      localStorage.setItem('lg_custom_logo_path', data.path);
      if (currentLabData) {
        renderFullDocument(currentLabData);
      }
    } else {
      if (statusEl) statusEl.textContent = 'Upload failed';
      alert('Failed to upload logo: ' + (data.error || 'Unknown error'));
    }
  } catch (err) {
    if (statusEl) statusEl.textContent = 'Error';
    alert('Failed to upload logo: ' + err);
  }
}

function updateProviderBadge() {
  const provider = document.getElementById('ai-provider')?.value;
  const badge = document.getElementById('provider-badge');
  const apiKeyLabel = document.querySelector('#api-key-group label[for="api-key"]');
  const apiKeyInput = document.getElementById('api-key');
  const apiKeyHint = document.querySelector('#api-key-group .hint-text');

  if (badge) {
    if (provider === 'gemini-pro' || provider === 'gemini') badge.textContent = 'Gemini 2.5 Pro (Best)';
    else if (provider === 'gemini-flash') badge.textContent = 'Gemini 2.5 Flash';
    else if (provider === 'gemini-1.5-pro') badge.textContent = 'Gemini 1.5 Pro';
    else if (provider === 'groq') badge.textContent = 'Groq (Llama 3.3 70B)';
    else if (provider === 'groq-8b') badge.textContent = 'Groq (Llama 3.1 8B)';
    else if (provider === 'mock') badge.textContent = 'Smart Offline Demo';
    else if (provider === 'openai') badge.textContent = 'OpenAI';
    else if (provider === 'ollama') badge.textContent = 'Local Ollama';
  }

  if (apiKeyLabel && apiKeyInput && apiKeyHint) {
    if (provider === 'groq' || provider === 'groq-8b') {
      apiKeyLabel.textContent = 'Groq Cloud API Key';
      apiKeyInput.placeholder = 'Paste your Groq API key (gsk_...)';
      apiKeyHint.innerHTML = 'Get free high-speed key from <a href="https://console.groq.com/keys" target="_blank">console.groq.com</a>. Or export GROQ_API_KEY in terminal.';
    } else if (provider === 'openai') {
      apiKeyLabel.textContent = 'OpenAI API Key';
      apiKeyInput.placeholder = 'Paste your OpenAI key (sk-...)';
      apiKeyHint.innerHTML = 'From your OpenAI dashboard. Or export OPENAI_API_KEY in terminal.';
    } else if (provider === 'mock' || provider === 'ollama') {
      apiKeyLabel.textContent = 'API Key (Optional / Offline)';
      apiKeyInput.placeholder = 'No API key needed for offline/local execution';
      apiKeyHint.innerHTML = 'Offline model uses pre-packaged intelligent template engine.';
    } else {
      apiKeyLabel.textContent = 'Google AI Studio API Key';
      apiKeyInput.placeholder = 'Paste your Google AI API key here';
      apiKeyHint.innerHTML = 'From your Google AI Pro account via <a href="https://aistudio.google.com/" target="_blank">aistudio.google.com</a> (Get API Key). Or export GEMINI_API_KEY in terminal.';
    }
  }
}

function setupDropZone() {
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-input');
  const browseBtn = document.getElementById('btn-browse');

  if (!dropZone || !fileInput || !browseBtn) return;

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

function addInstructionPreset(text) {
  const ta = document.getElementById('custom-instructions');
  if (!ta) return;
  if (ta.value.trim().length > 0) {
    if (!ta.value.includes(text)) {
      ta.value += '\n• ' + text;
    }
  } else {
    ta.value = '• ' + text;
  }
}

function setRefinePrompt(text) {
  const input = document.getElementById('refine-input');
  if (!input) return;
  input.value = text;
  input.focus();
}

async function runLabPipeline() {
  if (!currentFile) return;

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
  const secVal = document.getElementById('section-name') ? document.getElementById('section-name').value : '';
  if (secVal) formData.append('section', secVal);
  formData.append('department', document.getElementById('dept-name').value);

  const isInstOn = document.getElementById('toggle-instructor')?.checked || false;
  formData.append('include_instructor', isInstOn ? 'true' : 'false');
  if (isInstOn) {
    const instVal = document.getElementById('instructor-name') ? document.getElementById('instructor-name').value : '';
    if (instVal) formData.append('instructor', instVal);
  }

  // University Logo Settings
  const isLogoOn = document.getElementById('toggle-uni-logo')?.checked ?? true;
  formData.append('include_logo', isLogoOn ? 'true' : 'false');
  const logoChoice = document.getElementById('logo-choice-select')?.value || 'dawood';
  formData.append('logo_choice', logoChoice);
  const customLogoFile = document.getElementById('custom-logo-file')?.files?.[0];
  if (customLogoFile) {
    formData.append('custom_logo', customLogoFile);
  }

  formData.append('provider', document.getElementById('ai-provider').value);
  formData.append('api_key', document.getElementById('api-key').value);
  formData.append('theme', document.getElementById('terminal-theme').value);

  const termUser = document.getElementById('terminal-username')?.value.trim();
  const termHost = document.getElementById('terminal-hostname')?.value.trim();
  if (termUser) formData.append('username', termUser);
  if (termHost) formData.append('hostname', termHost);

  const customInst = document.getElementById('custom-instructions') ? document.getElementById('custom-instructions').value : '';
  if (customInst) formData.append('instructions', customInst);

  // Formats to generate (PDF and Word DOCX only)
  const formats = [];
  if (document.getElementById('fmt-pdf')?.checked) formats.push('pdf');
  if (document.getElementById('fmt-docx')?.checked) formats.push('docx');
  formData.append('formats', formats.join(','));

  let isPipelineRunning = true;
  const stepTimers = [];
  stepTimers.push(setTimeout(() => { if (isPipelineRunning) updateStep(2, 25, 'Formulating Student Solutions...', 'Applying custom instructions and anti-AI persona...'); }, 1200));
  stepTimers.push(setTimeout(() => { if (isPipelineRunning) updateStep(3, 45, 'Solving Tasks & Executing Locally...', 'Executing code solutions locally in isolated workspace...'); }, 3500));

  try {
    const res = await fetch('/api/run', {
      method: 'POST',
      body: formData,
    });

    isPipelineRunning = false;
    stepTimers.forEach(t => clearTimeout(t));
    stopTimer();

    const result = await res.json();

    if (!result.success) {
      alert('Error during execution: ' + (result.error || 'Unknown error'));
      document.getElementById('upload-card').style.display = 'block';
      document.getElementById('progress-card').style.display = 'none';
      return;
    }

    updateStep(5, 100, 'Complete!', 'All formats compiled and verified.');

    // Instantly transition UI to results without requiring browser refresh
    document.getElementById('upload-card').style.display = 'none';
    document.getElementById('progress-card').style.display = 'none';
    document.getElementById('results-container').style.display = 'block';

    try {
      renderResults(result, 'pdf');
    } catch (renderErr) {
      console.error('Error rendering lab results:', renderErr);
    }

    document.getElementById('results-container')?.scrollIntoView({ behavior: 'smooth' });

  } catch (err) {
    isPipelineRunning = false;
    stepTimers.forEach(t => clearTimeout(t));
    stopTimer();
    alert('Pipeline request failed: ' + err);
    document.getElementById('upload-card').style.display = 'block';
    document.getElementById('progress-card').style.display = 'none';
  }
}

function updateStep(stepNum, percent, title, desc) {
  const bar = document.getElementById('progress-bar-fill');
  if (bar) bar.style.width = percent + '%';
  const tEl = document.getElementById('progress-step-title');
  if (tEl) tEl.textContent = title;
  const dEl = document.getElementById('progress-step-desc');
  if (dEl) dEl.textContent = desc;

  for (let i = 1; i <= 5; i++) {
    const el = document.getElementById(`step-${i}`);
    if (el) {
      if (i < stepNum) {
        el.className = 'step-node completed';
      } else if (i === stepNum) {
        el.className = 'step-node active';
      } else {
        el.className = 'step-node';
      }
    }
  }
}

function startTimer() {
  secondsElapsed = 0;
  if (timerInterval) clearInterval(timerInterval);
  timerInterval = setInterval(() => {
    secondsElapsed++;
    const m = Math.floor(secondsElapsed / 60).toString().padStart(2, '0');
    const s = (secondsElapsed % 60).toString().padStart(2, '0');
    const timerEl = document.getElementById('elapsed-timer');
    if (timerEl) timerEl.textContent = `${m}:${s}`;

    // Dynamic adaptive status ticker so user sees continuous progress
    const titleEl = document.getElementById('progress-step-title');
    const descEl = document.getElementById('progress-step-desc');
    const bar = document.getElementById('progress-bar-fill');
    if (secondsElapsed > 5 && secondsElapsed <= 22) {
      if (titleEl && titleEl.textContent !== 'Complete!') {
        updateStep(3, Math.min(65, 45 + Math.floor((secondsElapsed - 5) * 1.2)), 'Solving Tasks & Executing Locally...', `Running code in isolated workspace... (${secondsElapsed}s)`);
      }
    } else if (secondsElapsed > 22 && secondsElapsed <= 38) {
      if (titleEl && titleEl.textContent !== 'Complete!') {
        updateStep(4, Math.min(82, 65 + Math.floor((secondsElapsed - 22) * 1.1)), 'Capturing Terminal Screenshots...', `Rendering terminal windows and syntax highlighted outputs... (${secondsElapsed}s)`);
      }
    } else if (secondsElapsed > 38) {
      if (titleEl && titleEl.textContent !== 'Complete!') {
        const pct = Math.min(95, 82 + Math.floor((secondsElapsed - 38) * 0.4));
        updateStep(5, pct, 'Compiling Academic Reports & Sanitizing...', `Generating Word (.docx), PDF via LibreOffice, and HTML reports... (${secondsElapsed}s)`);
      }
    }
  }, 1000);
}

function stopTimer() {
  if (timerInterval) {
    clearInterval(timerInterval);
    timerInterval = null;
  }
}

function getCurrentActiveView() {
  if (document.getElementById('btn-view-pdf')?.classList.contains('active')) return 'pdf';
  if (document.getElementById('btn-view-doc')?.classList.contains('active')) return 'doc';
  if (document.getElementById('btn-view-tasks')?.classList.contains('active')) return 'tasks';
  if (document.getElementById('btn-view-scratchpad')?.classList.contains('active')) return 'scratchpad';
  return 'pdf';
}

function restoreActiveLabSession() {
  const params = new URLSearchParams(window.location.search);
  const view = params.get('view');
  const modal = params.get('modal');

  if (window.__INITIAL_LAB__ && window.__INITIAL_LAB__.success) {
    updateNavState(true);
    renderResults(window.__INITIAL_LAB__, view || 'pdf');
    if (modal === 'shortcuts') openShortcutsModal();
    if (modal === 'cover') openCoverEditModal();
    return;
  }

  fetch('/api/current-lab')
    .then(r => r.json())
    .then(data => {
      if (data && data.success) {
        updateNavState(true);
        renderResults(data, view || 'pdf');
        if (modal === 'shortcuts') openShortcutsModal();
        if (modal === 'cover') openCoverEditModal();
      } else {
        updateNavState(false);
        if (view === 'scratchpad' || view === 'templates') {
          document.getElementById('upload-card').style.display = 'none';
          document.getElementById('results-container').style.display = 'block';
          switchMainView(view);
        }
        if (modal === 'shortcuts') openShortcutsModal();
        if (modal === 'cover') openCoverEditModal();
      }
    })
    .catch(() => {
      updateNavState(false);
    });
}

function updateNavState(hasLab) {
  const newLabBtn = document.getElementById('btn-nav-new-lab');
  const quickBundleBtn = document.getElementById('btn-quick-bundle');

  if (hasLab) {
    if (newLabBtn) newLabBtn.style.display = 'inline-flex';
    if (quickBundleBtn) quickBundleBtn.style.display = 'inline-flex';
  } else {
    if (newLabBtn) newLabBtn.style.display = 'none';
    if (quickBundleBtn) quickBundleBtn.style.display = 'none';
  }
}

function openNavPlayground() {
  document.getElementById('upload-card').style.display = 'none';
  document.getElementById('results-container').style.display = 'block';
  switchMainView('scratchpad');
}

function openNavTemplates() {
  openNavPlayground();
  const select = document.getElementById('scratch-template-select');
  if (select) {
    select.focus();
    select.scrollIntoView({ behavior: 'smooth' });
  }
}

async function closeAndStartNewLab() {
  if (isCanvasDirty) {
    const ok = confirm('You have unsaved changes on the current lab report. Close anyway and upload a new manual?');
    if (!ok) return;
  }

  try {
    await fetch('/api/close-lab', { method: 'POST' });
  } catch (e) {
    console.warn('Error closing session:', e);
  }

  currentLabData = null;
  window.__INITIAL_LAB__ = null;
  isCanvasDirty = false;
  currentFile = null;

  const fileInput = document.getElementById('file-input');
  if (fileInput) fileInput.value = '';
  const selectedInfo = document.getElementById('selected-file-info');
  if (selectedInfo) selectedInfo.style.display = 'none';
  const customInst = document.getElementById('custom-instructions');
  if (customInst) customInst.value = '';

  const docNavBtn = document.getElementById('btn-doc-nav');
  if (docNavBtn) docNavBtn.style.display = 'none';

  // Clear query params from URL
  window.history.replaceState({}, document.title, window.location.pathname);

  // Show upload card
  document.getElementById('results-container').style.display = 'none';
  document.getElementById('progress-card').style.display = 'none';
  const uploadCard = document.getElementById('upload-card');
  if (uploadCard) {
    uploadCard.style.display = 'block';
    uploadCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  // Clear canvas & tasks
  const canvas = document.getElementById('doc-canvas');
  if (canvas) canvas.innerHTML = '';
  const tasksFeed = document.getElementById('tasks-feed');
  if (tasksFeed) tasksFeed.innerHTML = '';

  updateNavState(false);
  showToast('Lab closed. Ready to upload a new lab manual!');
}

function showToast(msg, duration = 3000) {
  let toast = document.getElementById('studio-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'studio-toast';
    toast.className = 'studio-toast';
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.classList.add('visible');
  clearTimeout(toast._timeout);
  toast._timeout = setTimeout(() => {
    toast.classList.remove('visible');
  }, duration);
}

function renderResults(data, preferredView = null) {
  currentLabData = data;
  isCanvasDirty = false;
  updateNavState(true);

  document.getElementById('upload-card').style.display = 'none';
  document.getElementById('progress-card').style.display = 'none';
  document.getElementById('results-container').style.display = 'block';

  // Metadata Card
  document.getElementById('doc-title-text').textContent = data.filename;
  if (data.metadata) {
    document.getElementById('meta-author').textContent = `Author: ${data.metadata.creator || 'Student'}`;
    document.getElementById('meta-time').textContent = `Active Edit Time: ${data.metadata.total_time_mins || '78'} mins`;
    document.getElementById('meta-rev').textContent = `Revision: ${data.metadata.revision || '6'}`;
  }

  // Multi-format download buttons (PDF and Word DOCX only)
  const pdfBtn = document.getElementById('btn-download-pdf');
  if (pdfBtn) {
    if (data.pdf_filename) {
      pdfBtn.href = `/api/download/${data.pdf_filename}`;
      pdfBtn.style.display = 'inline-flex';
    } else {
      pdfBtn.style.display = 'none';
    }
  }

  const docxBtn = document.getElementById('btn-download-docx');
  if (docxBtn && data.filename) {
    docxBtn.href = `/api/download/${data.filename}`;
  }

  // PDF Preview frame
  const pdfFrame = document.getElementById('pdf-embed-frame');
  const openNewTabBtn = document.getElementById('btn-open-new-tab');
  if (data.pdf_filename) {
    const pdfUrl = `/api/preview/pdf/${data.pdf_filename}?t=${Date.now()}`;
    if (pdfFrame) pdfFrame.src = pdfUrl;
    if (openNewTabBtn) openNewTabBtn.href = pdfUrl;
  }

  // Populate refine task target selector
  const targetSelect = document.getElementById('refine-target-task');
  if (targetSelect && data.tasks) {
    targetSelect.innerHTML = '<option value="all">Scope: Entire Lab Report</option>';
    data.tasks.forEach(t => {
      const opt = document.createElement('option');
      opt.value = t.task_id;
      opt.textContent = `Task ${t.task_id}: ${t.title.slice(0, 30)}`;
      targetSelect.appendChild(opt);
    });
  }

  // Render Full Document Preview & Task Cards
  renderFullDocument(data);
  renderTaskCards(data);

  // Switch to target view: default to 'pdf' so the user directly sees the generated lab PDF
  const params = new URLSearchParams(window.location.search);
  const defaultView = preferredView || (params.get('view') || ((data.pdf_filename || data.has_pdf) ? 'pdf' : 'doc'));
  switchMainView(defaultView);

  if (params.get('modal') === 'shortcuts') {
    openShortcutsModal();
  }
}

// -------------------------------------------------------------
// Interactive Full Document Canvas with Direct Text Editing
// -------------------------------------------------------------
function renderFullDocument(data) {
  const canvas = document.getElementById('doc-canvas');
  if (!canvas) return;

  const studentName = document.getElementById('student-name')?.value || 'Bheesham Kumar Sajnani';
  const rollNo = document.getElementById('roll-no')?.value || '25F-DS-020';
  let section = document.getElementById('section-name')?.value || '';
  if (!section) {
    section = rollNo.includes('-') ? rollNo.split('-')[0] + '-' + rollNo.split('-')[1] : 'A';
  }
  const cleanTitle = data.lab_title || (data.filename ? data.filename.replace('.docx', '').replace(/_/g, ' ') : 'Completed Lab Report');
  const subjectVal = data.course_name || document.getElementById('dept-name')?.value || 'Data Science';

  const isInstOn = document.getElementById('toggle-instructor')?.checked || false;
  const instructor = document.getElementById('instructor-name')?.value || '';

  let instRow = '';
  if (isInstOn && instructor.trim()) {
    instRow = `
      <tr>
        <td class="lbl-col">Instructor</td>
        <td class="val-col" contenteditable="true" spellcheck="false" data-cover-field="instructor">${escapeHtml(instructor.trim())}</td>
      </tr>
    `;
  }

  // University Logo toggle & choice: default ON with Dawood Uni logo
  const isLogoOn = document.getElementById('toggle-uni-logo')?.checked ?? true;
  const logoChoice = document.getElementById('logo-choice-select')?.value || 'dawood';
  let logoImgSrc = '/static/university_logo.png';
  if (logoChoice === 'custom') {
    const customUrl = localStorage.getItem('lg_custom_logo_url');
    if (customUrl) logoImgSrc = customUrl;
  }

  const logoBlock = isLogoOn ? `
      <div class="doc-cover-logo-wrapper">
        <img src="${logoImgSrc}" alt="University Logo" class="doc-cover-logo" />
      </div>
  ` : '';

  let html = `
    <div class="doc-cover-page">
      <div class="doc-cover-action-bar">
        <span class="doc-cover-badge">Academic Cover Page</span>
        <button class="btn-doc-edit" onclick="openCoverEditModal()">Edit Cover Details</button>
      </div>
      ${logoBlock}

      <table class="doc-cover-table">
        <tbody>
          <tr>
            <td class="lbl-col">Name</td>
            <td class="val-col" contenteditable="true" spellcheck="false" data-cover-field="name">${escapeHtml(studentName)}</td>
          </tr>
          <tr>
            <td class="lbl-col">Roll Number</td>
            <td class="val-col" contenteditable="true" spellcheck="false" data-cover-field="roll">${escapeHtml(rollNo)}</td>
          </tr>
          <tr>
            <td class="lbl-col">Section</td>
            <td class="val-col" contenteditable="true" spellcheck="false" data-cover-field="section">${escapeHtml(section)}</td>
          </tr>
          <tr>
            <td class="lbl-col">Lab Title</td>
            <td class="val-col" contenteditable="true" spellcheck="false" data-cover-field="title">${escapeHtml(cleanTitle)}</td>
          </tr>
          <tr>
            <td class="lbl-col">Subject</td>
            <td class="val-col" contenteditable="true" spellcheck="false" data-cover-field="subject">${escapeHtml(subjectVal)}</td>
          </tr>
          ${instRow}
        </tbody>
      </table>
    </div>
  `;

  const ts = Date.now();
  data.tasks.forEach((task) => {
    const prefix = task.language === 'sql' ? 'Query' : 'Program';
    let codeImg = task.code_screenshot_url || task.screenshot_url || '';
    let outImg = task.output_screenshot_url || task.screenshot_url || '';
    if (codeImg && !codeImg.includes('_t=')) {
      codeImg += (codeImg.includes('?') ? `&_t=${ts}` : `?_t=${ts}`);
    }
    if (outImg && !outImg.includes('_t=')) {
      outImg += (outImg.includes('?') ? `&_t=${ts}` : `?_t=${ts}`);
    }

    let vivaHtml = '';
    if (task.answers && Object.keys(task.answers).length > 0) {
      let items = '';
      for (const [q, a] of Object.entries(task.answers)) {
        items += `
          <div class="viva-item-box">
            <strong style="font-size: 13px; color: #000000;">Q: ${escapeHtml(q)}</strong>
            <p contenteditable="true" spellcheck="true" data-task-id="${task.task_id}" data-viva-q="${escapeHtml(q)}" style="font-size: 12.5px; color: #333333; margin: 6px 0 0; padding: 2px 4px;">${escapeHtml(a)}</p>
          </div>
        `;
      }
      vivaHtml = `<div class="doc-viva-section" style="margin-top: 16px;"><strong style="font-size: 13px; color: #000000; display: block; margin-bottom: 8px;">Discussion &amp; Viva Answers (Editable):</strong>${items}</div>`;
    }

    html += `
      <div class="doc-prog-block" id="doc-task-${task.task_id}">
        <div class="doc-prog-header">
          <h2 class="doc-prog-title" contenteditable="true" spellcheck="false" data-task-id="${task.task_id}" data-task-field="title">${prefix} ${String(task.task_id).padStart(2, '0')}: ${escapeHtml(task.title)}</h2>
          <div class="doc-prog-actions">
            <button class="btn-doc-edit" onclick="openEditModal(${task.task_id})">Code Modal</button>
            <button class="btn-doc-edit" onclick="sendTaskToPlayground(${task.task_id})">Playground</button>
          </div>
        </div>
        <p class="doc-prog-desc" contenteditable="true" spellcheck="true" data-task-id="${task.task_id}" data-task-field="description">${escapeHtml(task.description || '')}</p>

        <div class="doc-label">${task.language === 'sql' ? 'QUERY / CODE (Editable):' : 'PROGRAM SOURCE CODE (Editable):'}</div>
        ${codeImg ? `
          <div class="doc-image-frame" onclick="openModal('${codeImg}', 'Code Screenshot - Task ${task.task_id}')">
            <img src="${codeImg}" alt="Code Screenshot">
          </div>
        ` : ''}
        <div class="doc-code-block"><pre><code contenteditable="true" spellcheck="false" data-task-id="${task.task_id}" data-task-field="code">${escapeHtml(task.code)}</code></pre></div>

        <div class="doc-label">EXECUTION CONSOLE OUTPUT (Editable):</div>
        ${outImg ? `
          <div class="doc-image-frame" onclick="openModal('${outImg}', 'Output Screenshot - Task ${task.task_id}')">
            <img src="${outImg}" alt="Output Screenshot">
          </div>
        ` : ''}
        <div class="doc-output-block" style="background:#0a0a0a; border: 1px solid #262626; padding: 10px 14px; margin: 10px 0 16px; border-radius: 4px; font-family: 'Fira Code', monospace; font-size: 12px; color: #ededed;"><pre style="margin:0;"><code contenteditable="true" spellcheck="false" data-task-id="${task.task_id}" data-task-field="output">${escapeHtml(task.output || '')}</code></pre></div>

        <div class="doc-explanation-block">
          <strong style="color: #000000;">Explanation &amp; Methodology:</strong>
          <div contenteditable="true" spellcheck="true" data-task-id="${task.task_id}" data-task-field="explanation" style="margin-top: 4px; color: #222222;">${escapeHtml(task.explanation || 'Authentic student implementation with comprehensive inline comments and edge-case validation.')}</div>
        </div>

        ${vivaHtml}
      </div>
    `;
  });

  canvas.innerHTML = html;
}

// -------------------------------------------------------------
// Save Document Canvas Edits & Recompile All Documents
// -------------------------------------------------------------
async function saveDocumentCanvasEdits() {
  if (!currentLabData) {
    alert('Please generate a lab report first before saving edits.');
    return;
  }

  const btnSaveTop = document.getElementById('btn-save-canvas');
  const btnSaveToolbar = document.getElementById('btn-toolbar-save');
  const oldText = btnSaveTop ? btnSaveTop.textContent : 'Save';

  if (btnSaveTop) {
    btnSaveTop.textContent = 'Saving & Compiling...';
    btnSaveTop.setAttribute('disabled', 'true');
  }
  if (btnSaveToolbar) {
    btnSaveToolbar.textContent = 'Saving...';
    btnSaveToolbar.setAttribute('disabled', 'true');
  }

  // 1. Gather Cover Page values
  const nameEl = document.querySelector('[data-cover-field="name"]');
  const rollEl = document.querySelector('[data-cover-field="roll"]');
  const secEl = document.querySelector('[data-cover-field="section"]');
  const titleEl = document.querySelector('[data-cover-field="title"]');
  const subEl = document.querySelector('[data-cover-field="subject"]');
  const instEl = document.querySelector('[data-cover-field="instructor"]');
  const isInstOn = document.getElementById('toggle-instructor')?.checked || false;

  const isLogoOn = document.getElementById('toggle-uni-logo')?.checked ?? true;
  const logoChoice = document.getElementById('logo-choice-select')?.value || 'dawood';
  const customLogoPath = localStorage.getItem('lg_custom_logo_path');

  const coverData = {
    name: nameEl ? nameEl.innerText.trim() : (document.getElementById('student-name')?.value || ''),
    roll_number: rollEl ? rollEl.innerText.trim() : (document.getElementById('roll-no')?.value || ''),
    section: secEl ? secEl.innerText.trim() : (document.getElementById('section-name')?.value || ''),
    lab_title: titleEl ? titleEl.innerText.trim() : (currentLabData.lab_title || ''),
    department: subEl ? subEl.innerText.trim() : (document.getElementById('dept-name')?.value || ''),
    instructor: instEl ? instEl.innerText.trim() : (document.getElementById('instructor-name')?.value || ''),
    include_instructor: isInstOn,
    include_logo: isLogoOn,
    logo_choice: logoChoice,
    custom_logo_path: customLogoPath,
  };

  // Sync back to sidebar inputs and local storage
  if (document.getElementById('student-name') && coverData.name) document.getElementById('student-name').value = coverData.name;
  if (document.getElementById('roll-no') && coverData.roll_number) document.getElementById('roll-no').value = coverData.roll_number;
  if (document.getElementById('section-name') && coverData.section) document.getElementById('section-name').value = coverData.section;
  if (document.getElementById('dept-name') && coverData.department) document.getElementById('dept-name').value = coverData.department;
  if (document.getElementById('instructor-name') && coverData.instructor) document.getElementById('instructor-name').value = coverData.instructor;

  localStorage.setItem('lg_student_name', coverData.name);
  localStorage.setItem('lg_roll_no', coverData.roll_number);
  localStorage.setItem('lg_section', coverData.section);
  localStorage.setItem('lg_dept', coverData.department);
  localStorage.setItem('lg_instructor', coverData.instructor);

  // 2. Gather Task Values
  const updatedTasks = currentLabData.tasks.map(origTask => {
    const tid = origTask.task_id;
    const titleNode = document.querySelector(`[data-task-id="${tid}"][data-task-field="title"]`);
    const descNode = document.querySelector(`[data-task-id="${tid}"][data-task-field="description"]`);
    const codeNode = document.querySelector(`[data-task-id="${tid}"][data-task-field="code"]`);
    const outNode = document.querySelector(`[data-task-id="${tid}"][data-task-field="output"]`);
    const expNode = document.querySelector(`[data-task-id="${tid}"][data-task-field="explanation"]`);

    let rawTitle = titleNode ? titleNode.innerText.trim() : origTask.title;
    // Strip "Program 01: " or "Query 02: " prefix if the user kept it in heading
    const prefixMatch = rawTitle.match(/^(?:Program|Query)\s+\d+:\s*(.*)$/i);
    if (prefixMatch) {
      rawTitle = prefixMatch[1];
    }

    const answersObj = {};
    const vivaNodes = document.querySelectorAll(`[data-task-id="${tid}"][data-viva-q]`);
    vivaNodes.forEach(vn => {
      const q = vn.getAttribute('data-viva-q');
      const a = vn.innerText.trim();
      if (q) answersObj[q] = a;
    });

    return {
      task_id: tid,
      title: rawTitle || origTask.title,
      description: descNode ? descNode.innerText.trim() : origTask.description,
      language: origTask.language,
      code: codeNode ? codeNode.innerText : origTask.code,
      output: outNode ? outNode.innerText : (origTask.output || ''),
      explanation: expNode ? expNode.innerText.trim() : (origTask.explanation || ''),
      answers: Object.keys(answersObj).length > 0 ? answersObj : (origTask.answers || {}),
    };
  });

  const payload = {
    cover: coverData,
    tasks: updatedTasks,
  };

  try {
    const res = await fetch('/api/save-document-canvas', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const result = await res.json();

    if (btnSaveTop) {
      btnSaveTop.textContent = oldText;
      btnSaveTop.removeAttribute('disabled');
    }
    if (btnSaveToolbar) {
      btnSaveToolbar.textContent = 'Save All Changes';
      btnSaveToolbar.removeAttribute('disabled');
    }

    if (!result.success) {
      alert('Save failed: ' + (result.error || 'Unknown error'));
      return;
    }

    markCanvasSaved();
    renderResults(result, 'doc');

  } catch (err) {
    if (btnSaveTop) {
      btnSaveTop.textContent = oldText;
      btnSaveTop.removeAttribute('disabled');
    }
    if (btnSaveToolbar) {
      btnSaveToolbar.textContent = 'Save All Changes';
      btnSaveToolbar.removeAttribute('disabled');
    }
    alert('Failed to save document changes: ' + err);
  }
}

// -------------------------------------------------------------
// Document Editor Toolbar Formatting Helpers
// -------------------------------------------------------------
function execFormat(command, value = null) {
  document.execCommand(command, false, value);
  markCanvasDirty();
}

function wrapSelectionCode() {
  const selection = window.getSelection();
  if (!selection.rangeCount) return;

  const range = selection.getRangeAt(0);
  const selectedText = range.toString();

  if (selectedText.length > 0) {
    const codeEl = document.createElement('code');
    codeEl.style.background = '#171717';
    codeEl.style.padding = '2px 6px';
    codeEl.style.borderRadius = '3px';
    codeEl.style.fontFamily = "'Fira Code', monospace";
    codeEl.style.color = '#ffffff';
    codeEl.style.border = '1px solid #333333';
    codeEl.textContent = selectedText;

    range.deleteContents();
    range.insertNode(codeEl);
    selection.removeAllRanges();
    markCanvasDirty();
  }
}

// -------------------------------------------------------------
// View Switching
// -------------------------------------------------------------
function switchMainView(viewName) {
  const docContainer = document.getElementById('view-doc-container');
  const pdfContainer = document.getElementById('view-pdf-container');
  const scratchContainer = document.getElementById('view-scratchpad-container');
  const tasksContainer = document.getElementById('view-tasks-container');

  const btnDoc = document.getElementById('btn-view-doc');
  const btnPdf = document.getElementById('btn-view-pdf');
  const btnScratch = document.getElementById('btn-view-scratchpad');
  const btnTasks = document.getElementById('btn-view-tasks');

  [btnDoc, btnPdf, btnScratch, btnTasks].forEach(b => {
    if (b) b.classList.remove('active');
  });

  [docContainer, pdfContainer, scratchContainer, tasksContainer].forEach(c => {
    if (c) c.style.display = 'none';
  });

  if (viewName === 'doc' && docContainer && btnDoc) {
    docContainer.style.display = 'block';
    btnDoc.classList.add('active');
  } else if (viewName === 'pdf' && pdfContainer && btnPdf) {
    pdfContainer.style.display = 'block';
    btnPdf.classList.add('active');
  } else if (viewName === 'scratchpad' && scratchContainer && btnScratch) {
    scratchContainer.style.display = 'block';
    btnScratch.classList.add('active');
    // Ensure scratchpad has code loaded if empty
    const codeEl = document.getElementById('scratch-code');
    if (codeEl && !codeEl.value.trim()) {
      loadStarterCode('python');
    }
  } else if (viewName === 'tasks' && tasksContainer && btnTasks) {
    tasksContainer.style.display = 'block';
    btnTasks.classList.add('active');
  } else {
    if (docContainer && btnDoc) {
      docContainer.style.display = 'block';
      btnDoc.classList.add('active');
    }
  }

  // Update navbar Document Preview button visibility
  const docNavBtn = document.getElementById('btn-doc-nav');
  if (docNavBtn) {
    if (currentLabData) {
      docNavBtn.style.display = (viewName === 'doc') ? 'none' : 'inline-flex';
    } else {
      docNavBtn.style.display = 'none';
    }
  }

  // Only show Save Edits button when in Document Canvas edit mode
  const btnSave = document.getElementById('btn-save-canvas');
  if (btnSave) {
    btnSave.style.display = (viewName === 'doc') ? 'inline-flex' : 'none';
  }
}

function printDocumentPreview() {
  window.print();
}

// -------------------------------------------------------------
// Code Playground & Live Terminal
// -------------------------------------------------------------
function setupPlayground() {
  loadStarterCode('python');
  // Fetch templates for dropdown
  fetch('/api/templates')
    .then(r => r.json())
    .then(data => {
      if (data && data.templates) {
        cachedTemplates = data.templates;
        populateTemplateSelect(cachedTemplates);
      }
    })
    .catch(() => {});
}

function populateTemplateSelect(templates) {
  const select = document.getElementById('scratch-template-select');
  if (!select) return;
  select.innerHTML = '<option value="">Load Starter Template...</option>';
  templates.forEach(t => {
    const opt = document.createElement('option');
    opt.value = t.id;
    opt.textContent = `${t.category}: ${t.name}`;
    select.appendChild(opt);
  });
}

function onScratchLangChange() {
  const lang = document.getElementById('scratch-lang')?.value || 'python';
  const termTitle = document.getElementById('terminal-pane-title');
  if (termTitle) {
    if (lang === 'c') termTitle.textContent = 'terminal — Linux (gcc 13.3 -lm)';
    else if (lang === 'sql') termTitle.textContent = 'terminal — Linux (SQLite 3.45)';
    else termTitle.textContent = 'terminal — Linux (Python 3.12)';
  }

  // Pre-load default starter code if currently empty
  const codeArea = document.getElementById('scratch-code');
  if (codeArea && !codeArea.value.trim()) {
    loadStarterCode(lang);
  }
}

function loadStarterCode(lang) {
  const codeArea = document.getElementById('scratch-code');
  if (!codeArea) return;

  if (lang === 'c') {
    codeArea.value = `#include <stdio.h>\n#include <stdlib.h>\n\nint main() {\n    printf("=== C Algorithm Test Runner ===\\n");\n    int n = 5;\n    int *arr = (int*)malloc(n * sizeof(int));\n    for (int i = 0; i < n; i++) arr[i] = (i + 1) * 10;\n    printf("[+] Allocated array: ");\n    for (int i = 0; i < n; i++) printf("%d ", arr[i]);\n    printf("\\n");\n    free(arr);\n    return 0;\n}\n`;
  } else if (lang === 'sql') {
    codeArea.value = `CREATE TABLE Students (\n    id INTEGER PRIMARY KEY,\n    name TEXT NOT NULL,\n    roll_no TEXT NOT NULL,\n    score REAL\n);\n\nINSERT INTO Students VALUES (1, 'Bheesham Kumar', '25F-DS-020', 98.5);\nINSERT INTO Students VALUES (2, 'Ali Raza', '25F-DS-012', 91.0);\n\nSELECT * FROM Students;\n`;
  } else {
    codeArea.value = `def binary_search(arr, target):\n    low, high = 0, len(arr) - 1\n    while low <= high:\n        mid = (low + high) // 2\n        if arr[mid] == target: return mid\n        elif arr[mid] < target: low = mid + 1\n        else: high = mid - 1\n    return -1\n\ndata = [12, 24, 36, 48, 60, 72, 84]\ntarget = 48\nidx = binary_search(data, target)\nprint(f"[+] Searching for {target} in {data}")\nprint(f"[+] Found at index: {idx}")\n`;
  }
}

function loadSelectedTemplate() {
  const select = document.getElementById('scratch-template-select');
  if (!select) return;
  const templateId = select.value;
  if (!templateId) return;

  const tpl = cachedTemplates.find(t => t.id === templateId);
  if (tpl) {
    const codeArea = document.getElementById('scratch-code');
    const langSelect = document.getElementById('scratch-lang');
    if (codeArea) codeArea.value = tpl.code;
    if (langSelect) langSelect.value = tpl.language;
    onScratchLangChange();
  }
}

async function runPlaygroundCode() {
  const lang = document.getElementById('scratch-lang')?.value || 'python';
  const code = document.getElementById('scratch-code')?.value || '';
  const stdin = document.getElementById('scratch-stdin')?.value || '';

  if (!code.trim()) {
    alert('Please enter or paste code to execute.');
    return;
  }

  const btn = document.getElementById('btn-run-scratchpad');
  const btnTop = document.getElementById('btn-run-scratchpad-top');
  const btnText = document.getElementById('scratch-run-text');
  const spinner = document.getElementById('scratch-spinner');
  const metrics = document.getElementById('scratch-metrics');
  const stdoutEl = document.getElementById('scratch-stdout');
  const stderrEl = document.getElementById('scratch-stderr');
  const cmdDisplay = document.getElementById('term-cmd-display');

  if (btn) btn.setAttribute('disabled', 'true');
  if (btnTop) btnTop.setAttribute('disabled', 'true');
  if (btnText) btnText.textContent = 'Running...';
  if (spinner) spinner.style.display = 'inline-block';
  if (metrics) metrics.textContent = 'Executing...';

  const defaultCmd = lang === 'c' ? 'gcc -O2 -lm main.c && ./a.out' : (lang === 'sql' ? 'sqlite3 lab.db < query.sql' : 'python3 main.py');
  if (cmdDisplay) cmdDisplay.textContent = defaultCmd;

  try {
    const res = await fetch('/api/execute-scratchpad', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ language: lang, code: code, stdin: stdin }),
    });

    const data = await res.json();

    if (btn) btn.removeAttribute('disabled');
    if (btnTop) btnTop.removeAttribute('disabled');
    if (btnText) btnText.textContent = '▶ Run Code (Ctrl+Enter)';
    if (spinner) spinner.style.display = 'none';

    if (data.command && cmdDisplay) cmdDisplay.textContent = data.command;

    if (metrics) {
      const exitBadge = data.exit_code === 0 ? 'Exit 0' : `Exit ${data.exit_code}`;
      metrics.textContent = `${data.execution_time_ms}ms | ${exitBadge}`;
      metrics.style.color = '#ffffff';
    }

    if (stdoutEl) {
      stdoutEl.textContent = data.stdout || '(Process finished with no standard output)';
    }

    if (stderrEl) {
      if (data.stderr && data.stderr.trim()) {
        stderrEl.textContent = data.stderr;
        stderrEl.style.display = 'block';
      } else {
        stderrEl.style.display = 'none';
      }
    }

  } catch (err) {
    if (btn) btn.removeAttribute('disabled');
    if (btnTop) btnTop.removeAttribute('disabled');
    if (btnText) btnText.textContent = '▶ Run Code (Ctrl+Enter)';
    if (spinner) spinner.style.display = 'none';
    if (metrics) metrics.textContent = 'Error';
    if (stdoutEl) stdoutEl.textContent = '';
    if (stderrEl) {
      stderrEl.textContent = 'Failed to communicate with local execution runner: ' + err;
      stderrEl.style.display = 'block';
    }
  }
}

function copyPlaygroundCode() {
  const code = document.getElementById('scratch-code')?.value || '';
  navigator.clipboard.writeText(code);
  showToast('Code copied to clipboard!');
}

function clearPlayground() {
  const code = document.getElementById('scratch-code');
  const stdin = document.getElementById('scratch-stdin');
  const stdout = document.getElementById('scratch-stdout');
  const stderr = document.getElementById('scratch-stderr');
  const metrics = document.getElementById('scratch-metrics');

  if (code) code.value = '';
  if (stdin) stdin.value = '';
  if (stdout) stdout.textContent = 'Terminal reset. Click "▶ Run Code" to execute.';
  if (stderr) stderr.style.display = 'none';
  if (metrics) {
    metrics.textContent = 'Ready';
    metrics.style.color = '#a1a1a1';
  }
}

function sendTaskToPlayground(taskId) {
  if (!currentLabData || !currentLabData.tasks) return;
  const task = currentLabData.tasks.find(t => t.task_id === taskId);
  if (!task) return;

  switchMainView('scratchpad');
  const langSelect = document.getElementById('scratch-lang');
  const codeArea = document.getElementById('scratch-code');
  if (langSelect) {
    langSelect.value = task.language === 'c' ? 'c' : (task.language === 'sql' ? 'sql' : 'python');
    onScratchLangChange();
  }
  if (codeArea) codeArea.value = task.code;
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// -------------------------------------------------------------
// Academic DSA & C Library Grid
// -------------------------------------------------------------
async function loadTemplatesGrid() {
  const grid = document.getElementById('templates-grid');
  if (!grid) return;

  if (cachedTemplates.length === 0) {
    try {
      const res = await fetch('/api/templates');
      const data = await res.json();
      if (data && data.templates) {
        cachedTemplates = data.templates;
      }
    } catch (e) {}
  }

  let html = '';
  cachedTemplates.forEach(t => {
    html += `
      <div class="template-card">
        <div class="template-card-header">
          <div>
            <span class="tpl-badge ${t.language}">${t.language.toUpperCase()}</span>
            <span class="tpl-cat">${escapeHtml(t.category)}</span>
          </div>
          <div class="tpl-actions">
            <button class="btn btn-xs btn-outline" onclick="copyTemplateCode('${t.id}')">Copy</button>
            <button class="btn btn-xs btn-primary" onclick="openTemplateInPlayground('${t.id}')">Open</button>
          </div>
        </div>
        <h4 class="tpl-name">${escapeHtml(t.name)}</h4>
        <div class="tpl-code-preview">
          <pre><code>${escapeHtml(t.code)}</code></pre>
        </div>
      </div>
    `;
  });

  grid.innerHTML = html;
}

function openTemplateInPlayground(id) {
  const tpl = cachedTemplates.find(t => t.id === id);
  if (!tpl) return;

  switchMainView('scratchpad');
  const langSelect = document.getElementById('scratch-lang');
  const codeArea = document.getElementById('scratch-code');
  if (langSelect) {
    langSelect.value = tpl.language;
    onScratchLangChange();
  }
  if (codeArea) codeArea.value = tpl.code;
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function copyTemplateCode(id) {
  const tpl = cachedTemplates.find(t => t.id === id);
  if (!tpl) return;
  navigator.clipboard.writeText(tpl.code);
  alert(`Copied "${tpl.name}" source code to clipboard!`);
}

// -------------------------------------------------------------
// 1-Click Submission Bundle Download
// -------------------------------------------------------------
function downloadSubmissionBundle() {
  window.location.href = '/api/download-bundle';
}

// -------------------------------------------------------------
// Task Cards Feed Rendering
// -------------------------------------------------------------
function renderTaskCards(data) {
  const feed = document.getElementById('tasks-feed');
  if (!feed) return;
  feed.innerHTML = '';

  const ts = Date.now();
  data.tasks.forEach((task, idx) => {
    const card = document.createElement('div');
    card.className = 'card task-card';

    // Clean task title so "Task X: Task X: ..." is avoided
    let cleanTitle = task.title || '';
    cleanTitle = cleanTitle.replace(/^task\s*\d+[\s:.-]*/i, '').trim();

    let codeImg = task.code_screenshot_url || task.screenshot_url || '';
    let outImg = task.output_screenshot_url || task.screenshot_url || '';
    if (codeImg && !codeImg.includes('_t=')) {
      codeImg += (codeImg.includes('?') ? `&_t=${ts}` : `?_t=${ts}`);
    }
    if (outImg && !outImg.includes('_t=')) {
      outImg += (outImg.includes('?') ? `&_t=${ts}` : `?_t=${ts}`);
    }

    card.innerHTML = `
      <div class="task-header">
        <div class="task-title-row">
          <span class="lang-tag">${task.language}</span>
          <h3>Task ${task.task_id}${cleanTitle ? ': ' + escapeHtml(cleanTitle) : ''}</h3>
        </div>
        <div style="display:flex; gap:8px;">
          <button class="btn btn-sm btn-outline" onclick="sendTaskToPlayground(${task.task_id})">Open in Playground</button>
          <button class="btn btn-sm btn-outline" onclick="openEditModal(${task.task_id})">Edit Task</button>
        </div>
      </div>
      <p class="task-desc">${escapeHtml(task.description)}</p>

      <div class="task-tabs">
        <button class="task-tab-btn active" onclick="switchTaskTab(${idx}, 'code-img')">Code Screenshot</button>
        <button class="task-tab-btn" onclick="switchTaskTab(${idx}, 'out-img')">Console Output Screenshot</button>
        <button class="task-tab-btn" onclick="switchTaskTab(${idx}, 'raw-code')">Raw Source Code</button>
      </div>

      <div class="tab-pane active" id="tab-code-img-${idx}">
        <div class="screenshot-preview-wrapper" onclick="openModal('${codeImg}', 'Code Screenshot - Task ${task.task_id}')">
          <img src="${codeImg}" alt="Code Screenshot">
          <p class="screenshot-caption">Figure: Code Screenshot (Linux Terminal Light Theme) - Click to zoom</p>
        </div>
      </div>

      <div class="tab-pane" id="tab-out-img-${idx}">
        <div class="screenshot-preview-wrapper" onclick="openModal('${outImg}', 'Output Screenshot - Task ${task.task_id}')">
          <img src="${outImg}" alt="Output Screenshot">
          <p class="screenshot-caption">Figure: Terminal Console Output Screenshot - Click to zoom</p>
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
  if (!card) return;
  const buttons = card.querySelectorAll('.task-tab-btn');
  const panes = card.querySelectorAll('.tab-pane');

  buttons.forEach(btn => btn.classList.remove('active'));
  panes.forEach(p => p.classList.remove('active'));

  if (window.event && window.event.target) {
    window.event.target.classList.add('active');
  }
  const targetPane = card.querySelector(`#tab-${tabName}-${taskIdx}`);
  if (targetPane) targetPane.classList.add('active');
}

// -------------------------------------------------------------
// Interactive Refine Flow
// -------------------------------------------------------------
async function handleRefineSubmit() {
  const input = document.getElementById('refine-input');
  const instruction = input ? input.value.trim() : '';
  if (!instruction) {
    alert('Please enter an instruction or edit request.');
    return;
  }

  const targetTask = document.getElementById('refine-target-task')?.value || 'all';
  const btn = document.getElementById('btn-apply-refine');
  const btnText = document.getElementById('refine-btn-text');
  const spinner = document.getElementById('refine-spinner');

  if (btn) btn.setAttribute('disabled', 'true');
  if (btnText) btnText.textContent = 'Refining & Re-running...';
  if (spinner) spinner.style.display = 'inline-block';

  const formData = new FormData();
  formData.append('instruction', instruction);
  formData.append('task_id', targetTask);

  try {
    const res = await fetch('/api/refine', {
      method: 'POST',
      body: formData,
    });
    const data = await res.json();

    if (btn) btn.removeAttribute('disabled');
    if (btnText) btnText.textContent = 'Apply & Re-generate';
    if (spinner) spinner.style.display = 'none';

    if (!data.success) {
      alert('Refinement failed: ' + (data.error || 'Unknown error'));
      return;
    }

    if (input) input.value = '';
    renderResults(data, getCurrentActiveView());

  } catch (err) {
    if (btn) btn.removeAttribute('disabled');
    if (btnText) btnText.textContent = 'Apply & Re-generate';
    if (spinner) spinner.style.display = 'none';
    alert('Refine request failed: ' + err);
  }
}

// -------------------------------------------------------------
// Direct Edit Task Modal
// -------------------------------------------------------------
function openEditModal(taskId) {
  if (!currentLabData || !currentLabData.tasks) return;
  const task = currentLabData.tasks.find(t => t.task_id === taskId);
  if (!task) return;

  document.getElementById('edit-task-id').value = task.task_id;
  document.getElementById('edit-modal-title').textContent = `Direct Edit: Task ${task.task_id} (${task.title})`;
  document.getElementById('edit-task-code').value = task.code;
  document.getElementById('edit-task-explanation').value = task.explanation || '';
  document.getElementById('edit-modal-overlay').classList.add('active');
}

function closeEditModal() {
  document.getElementById('edit-modal-overlay').classList.remove('active');
}

async function submitDirectEdit() {
  const taskId = document.getElementById('edit-task-id').value;
  const code = document.getElementById('edit-task-code').value;
  const explanation = document.getElementById('edit-task-explanation').value;

  const btn = document.getElementById('btn-save-direct-edit');
  const originalText = btn.textContent;
  btn.textContent = 'Executing & Rebuilding...';
  btn.setAttribute('disabled', 'true');

  const formData = new FormData();
  formData.append('task_id', taskId);
  formData.append('code', code);
  formData.append('explanation', explanation);

  try {
    const res = await fetch('/api/edit-task', {
      method: 'POST',
      body: formData,
    });
    const data = await res.json();

    btn.textContent = originalText;
    btn.removeAttribute('disabled');

    if (!data.success) {
      alert('Direct edit failed: ' + (data.error || 'Unknown error'));
      return;
    }

    closeEditModal();
    renderResults(data, getCurrentActiveView());

  } catch (err) {
    btn.textContent = originalText;
    btn.removeAttribute('disabled');
    alert('Direct edit request failed: ' + err);
  }
}

// -------------------------------------------------------------
// Cover Page Edit Modal
// -------------------------------------------------------------
function openCoverEditModal() {
  const studentName = document.getElementById('student-name')?.value || 'Bheesham Kumar Sajnani';
  const rollNo = document.getElementById('roll-no')?.value || '25F-DS-020';
  let section = document.getElementById('section-name')?.value || '25F-DS';
  const dept = currentLabData?.course_name || document.getElementById('dept-name')?.value || 'Data Science';
  const cleanTitle = currentLabData?.lab_title || (currentLabData?.filename ? currentLabData.filename.replace('.docx', '').replace(/_/g, ' ') : 'Completed Lab Report');

  const isInstOn = document.getElementById('toggle-instructor')?.checked || false;
  const instructor = document.getElementById('instructor-name')?.value || '';

  document.getElementById('edit-cover-name').value = studentName;
  document.getElementById('edit-cover-roll').value = rollNo;
  document.getElementById('edit-cover-section').value = section;
  document.getElementById('edit-cover-subject').value = dept;
  document.getElementById('edit-cover-lab-title').value = cleanTitle;

  const toggleInst = document.getElementById('edit-cover-toggle-inst');
  const instWrapper = document.getElementById('edit-cover-inst-wrapper');
  const instInput = document.getElementById('edit-cover-instructor');

  if (toggleInst && instWrapper && instInput) {
    toggleInst.checked = isInstOn;
    instWrapper.style.display = isInstOn ? 'block' : 'none';
    instInput.value = instructor;
  }

  document.getElementById('edit-cover-modal-overlay').classList.add('active');
}

function closeCoverEditModal() {
  document.getElementById('edit-cover-modal-overlay').classList.remove('active');
}

async function submitCoverEdit() {
  const name = document.getElementById('edit-cover-name').value;
  const rollNo = document.getElementById('edit-cover-roll').value;
  const section = document.getElementById('edit-cover-section').value;
  const subject = document.getElementById('edit-cover-subject').value;
  const labTitle = document.getElementById('edit-cover-lab-title').value;
  const isInstOn = document.getElementById('edit-cover-toggle-inst')?.checked || false;
  const instructor = document.getElementById('edit-cover-instructor')?.value || '';

  if (document.getElementById('student-name')) document.getElementById('student-name').value = name;
  if (document.getElementById('roll-no')) document.getElementById('roll-no').value = rollNo;
  if (document.getElementById('section-name')) document.getElementById('section-name').value = section;
  if (document.getElementById('dept-name')) document.getElementById('dept-name').value = subject;
  if (document.getElementById('toggle-instructor')) {
    document.getElementById('toggle-instructor').checked = isInstOn;
    const sideInstWrap = document.getElementById('instructor-input-wrapper');
    if (sideInstWrap) sideInstWrap.style.display = isInstOn ? 'block' : 'none';
  }
  if (document.getElementById('instructor-name')) document.getElementById('instructor-name').value = instructor;

  localStorage.setItem('lg_student_name', name);
  localStorage.setItem('lg_roll_no', rollNo);
  localStorage.setItem('lg_section', section);
  localStorage.setItem('lg_dept', subject);
  localStorage.setItem('lg_include_instructor', isInstOn ? 'true' : 'false');
  localStorage.setItem('lg_instructor', instructor);

  const btn = document.getElementById('btn-save-cover-edit');
  const originalText = btn.textContent;
  btn.textContent = 'Rebuilding Documents...';
  btn.setAttribute('disabled', 'true');

  const formData = new FormData();
  formData.append('name', name);
  formData.append('roll_number', rollNo);
  formData.append('section', section);
  formData.append('department', subject);
  formData.append('lab_title', labTitle);
  formData.append('include_instructor', isInstOn ? 'true' : 'false');
  if (isInstOn && instructor) {
    formData.append('instructor', instructor);
  }

  const isLogoOn = document.getElementById('toggle-uni-logo')?.checked ?? true;
  formData.append('include_logo', isLogoOn ? 'true' : 'false');
  const logoChoice = document.getElementById('logo-choice-select')?.value || 'dawood';
  formData.append('logo_choice', logoChoice);
  const customLogoFile = document.getElementById('custom-logo-file')?.files?.[0];
  if (customLogoFile) {
    formData.append('custom_logo', customLogoFile);
  }

  try {
    const res = await fetch('/api/edit-cover', {
      method: 'POST',
      body: formData,
    });
    const data = await res.json();

    btn.textContent = originalText;
    btn.removeAttribute('disabled');

    if (!data.success) {
      alert('Failed to update cover page: ' + (data.error || 'Unknown error'));
      return;
    }

    closeCoverEditModal();
    renderResults(data, getCurrentActiveView());

  } catch (err) {
    btn.textContent = originalText;
    btn.removeAttribute('disabled');
    alert('Cover page update request failed: ' + err);
  }
}

// -------------------------------------------------------------
// Utilities
// -------------------------------------------------------------
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
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function escapeJs(str) {
  if (!str) return '';
  return String(str).replace(/\\/g, '\\\\').replace(/`/g, '\\`').replace(/\$/g, '\\$');
}
