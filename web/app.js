// LabGenius IDE Studio Interface Logic
// Vercel / VS Code / Antigravity Dark Theme & Interactive Studio Engine

let currentFile = null;
let timerInterval = null;
let secondsElapsed = 0;
let currentLabData = null;
let cachedTemplates = [];
let isCanvasDirty = false;

document.addEventListener('DOMContentLoaded', () => {
  initAppTheme();
  initProfile();
  initScreenshotThemeSystem();
  setupDropZone();
  setupEventListeners();
  setupPlayground();
  setupKeyboardShortcuts();
  restoreActiveLabSession();
  registerWebMCPTools();

  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('view') === 'doctools' || window.location.hash === '#doctools') {
    openNavDocTools();
    if (urlParams.get('sample') === '1') {
      mergerQueue = [
        {
          id: 'sample_1',
          name: 'Data_Structures_Lab1.pdf',
          sizeFormatted: '2.4 MB',
          type: 'pdf',
          file: new File([new Blob(["dummy pdf content"])], 'Data_Structures_Lab1.pdf', { type: 'application/pdf' })
        },
        {
          id: 'sample_2',
          name: 'Algorithms_Notes.docx',
          sizeFormatted: '1.8 MB',
          type: 'docx',
          file: new File([new Blob(["dummy docx content"])], 'Algorithms_Notes.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
        },
        {
          id: 'sample_3',
          name: 'Example_Code.txt',
          sizeFormatted: '432 KB',
          type: 'txt',
          file: new File([new Blob(["dummy txt content"])], 'Example_Code.txt', { type: 'text/plain' })
        }
      ];
      currentMergerStep = 2;
      renderMergerQueue();
    }
    const tool = urlParams.get('tool');
    if (tool) {
      switchDocTool(tool);
    }
  } else if (urlParams.get('view') === 'playground') {
    openNavPlayground();
  } else {
    navigateToView('home');
  }
});

// ============================================================================
// APP UI THEME (Dark / Light Mode)
// ============================================================================
function initAppTheme() {
  const savedTheme = localStorage.getItem('labgenius_app_theme') || 'dark';
  applyAppTheme(savedTheme, false);
}

function toggleAppTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'dark';
  const next = current === 'dark' ? 'light' : 'dark';
  applyAppTheme(next, true);
}

function applyAppTheme(theme, notify = false) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('labgenius_app_theme', theme);

  const iconEl = document.getElementById('app-theme-icon');
  const labelEl = document.getElementById('app-theme-label');
  const btnEl = document.getElementById('btn-theme-toggle');

  if (theme === 'light') {
    if (iconEl) {
      iconEl.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>`;
    }
    if (labelEl) labelEl.textContent = 'Light';
    if (btnEl) btnEl.title = 'Switch to Dark Mode';
    if (notify) showToast('☀️ Switched to Light mode');
  } else {
    if (iconEl) {
      iconEl.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"></path></svg>`;
    }
    if (labelEl) labelEl.textContent = 'Dark';
    if (btnEl) btnEl.title = 'Switch to Light Mode';
    if (notify) showToast('🌙 Switched to Dark mode');
  }
}

// ============================================================================
// SCREENSHOT & DOCUMENT THEME STUDIO
// ============================================================================
const THEME_PRESETS = {
  'modern-dark': {
    name: 'Midnight Modern',
    bg: '#161821',
    headerBg: '#1f232b',
    border: '#2d3142',
    text: '#d2d7de',
    promptColor: '#b48ead',
    cmdColor: '#ededed',
    outColor: '#abb2bf',
  },
  'slate-grey': {
    name: 'Charcoal Slate (Grey)',
    bg: '#282c34',
    headerBg: '#21252b',
    border: '#3c424e',
    text: '#abb2bf',
    promptColor: '#61afef',
    cmdColor: '#98c379',
    outColor: '#abb2bf',
  },
  'cyber-black': {
    name: 'Cyber OLED (Pitch Black)',
    bg: '#0a0c10',
    headerBg: '#10141a',
    border: '#30363d',
    text: '#e6edf3',
    promptColor: '#3fb950',
    cmdColor: '#58a6ff',
    outColor: '#8b949e',
  },
  'paper-warm': {
    name: 'Editorial Parchment (Warm Light)',
    bg: '#f5f1e9',
    headerBg: '#ece6dc',
    border: '#d8cfbc',
    text: '#2e3440',
    promptColor: '#856621',
    cmdColor: '#b58900',
    outColor: '#4c566a',
  },
  'cobalt-blue': {
    name: 'Deep Cobalt (Navy)',
    bg: '#0f172a',
    headerBg: '#1e293b',
    border: '#334155',
    text: '#e2e8f0',
    promptColor: '#38bdf8',
    cmdColor: '#818cf8',
    outColor: '#cbd5e1',
  },
};

let activeScreenshotTheme = 'modern-dark';
let isSecretEnvActive = false;

async function initScreenshotThemeSystem() {
  try {
    const res = await fetch('/api/themes');
    if (res.ok) {
      const data = await res.json();
      if (data.success) {
        isSecretEnvActive = !!data.is_custom_env;
        const secretWrap = document.getElementById('secret-theme-indicator-wrapper');
        if (secretWrap) {
          secretWrap.style.display = isSecretEnvActive ? 'block' : 'none';
        }

        const selectEl = document.getElementById('terminal-theme');
        if (selectEl && Array.isArray(data.themes)) {
          selectEl.innerHTML = '';
          data.themes.forEach(t => {
            const opt = document.createElement('option');
            opt.value = t.id;
            opt.textContent = `${t.name}`;
            selectEl.appendChild(opt);
          });
        }

        const savedUserTheme = localStorage.getItem('lg_screenshot_theme');
        const customInput = document.getElementById('custom-theme-input');

        if (savedUserTheme) {
          if (THEME_PRESETS[savedUserTheme]) {
            if (selectEl) selectEl.value = savedUserTheme;
            onThemeChanged(savedUserTheme, false);
          } else {
            // Restore custom / secret theme
            if (customInput) customInput.value = savedUserTheme;
            try {
              const tr = await fetch(`/api/theme/${encodeURIComponent(savedUserTheme)}`);
              const td = await tr.json();
              if (td.success && td.theme) {
                const t = td.theme;
                THEME_PRESETS[t.id] = {
                  name: t.name,
                  bg: t.bg_hex,
                  headerBg: t.header_bg_hex,
                  border: t.border_hex,
                  text: t.text_hex,
                  promptColor: t.prompt_hex,
                  cmdColor: t.accent_hex || '#0000ff',
                  outColor: t.text_hex,
                  isSecret: t.is_secret,
                  windowStyle: t.window_style,
                };
                activeScreenshotTheme = t.id;
                if (selectEl) {
                  let opt = Array.from(selectEl.options).find(o => o.value === t.id);
                  if (!opt) {
                    opt = document.createElement('option');
                    opt.value = t.id;
                    opt.textContent = `✨ ${t.name} (Custom Active)`;
                    selectEl.appendChild(opt);
                  }
                  selectEl.value = t.id;
                }
                updateMiniTerminalPreview(t.id, t.is_secret);
                const statusEl = document.getElementById('custom-theme-status');
                if (statusEl) {
                  statusEl.style.display = 'flex';
                  statusEl.className = 'custom-theme-status success';
                  statusEl.innerHTML = `<span>✓ Active: <strong>${t.name}</strong> (${t.id})</span>`;
                }
              } else {
                onThemeChanged(data.active_theme || 'modern-dark', false);
              }
            } catch (e) {
              onThemeChanged(data.active_theme || 'modern-dark', false);
            }
          }
        } else if (isSecretEnvActive) {
          // Auto-load signature theme from .env
          if (customInput) customInput.value = 'bheeshamks';
          try {
            const tr = await fetch('/api/theme/bheeshamks');
            const td = await tr.json();
            if (td.success && td.theme) {
              const t = td.theme;
              THEME_PRESETS[t.id] = {
                name: t.name,
                bg: t.bg_hex,
                headerBg: t.header_bg_hex,
                border: t.border_hex,
                text: t.text_hex,
                promptColor: t.prompt_hex,
                cmdColor: t.accent_hex || '#0000ff',
                outColor: t.text_hex,
                isSecret: t.is_secret,
                windowStyle: t.window_style,
              };
              activeScreenshotTheme = t.id;
              if (selectEl) {
                let opt = Array.from(selectEl.options).find(o => o.value === t.id);
                if (!opt) {
                  opt = document.createElement('option');
                  opt.value = t.id;
                  opt.textContent = `✨ ${t.name} (Custom Active)`;
                  selectEl.appendChild(opt);
                }
                selectEl.value = t.id;
              }
              updateMiniTerminalPreview(t.id, true);
              const statusEl = document.getElementById('custom-theme-status');
              if (statusEl) {
                statusEl.style.display = 'flex';
                statusEl.className = 'custom-theme-status success';
                statusEl.innerHTML = `<span>✓ Active: <strong>${t.name}</strong> (${t.id})</span>`;
              }
            }
          } catch (e) {
            updateMiniTerminalPreview('modern-dark', true);
          }
        } else {
          onThemeChanged(data.active_theme || 'modern-dark', false);
        }
      }
    }
  } catch (err) {
    console.warn('Could not load themes from API, using client presets', err);
    onThemeChanged('modern-dark', false);
  }
}

async function applyCustomTheme() {
  const input = document.getElementById('custom-theme-input');
  const statusEl = document.getElementById('custom-theme-status');
  const rawTheme = (input ? input.value : '').trim().toLowerCase();

  if (!rawTheme) {
    if (statusEl) {
      statusEl.style.display = 'flex';
      statusEl.className = 'custom-theme-status error';
      statusEl.innerHTML = '<span>⚠️ Please enter a theme name.</span>';
    }
    showToast('Please enter a theme name');
    return;
  }

  try {
    const res = await fetch(`/api/theme/${encodeURIComponent(rawTheme)}`);
    const data = await res.json();

    if (data.success && data.theme) {
      const t = data.theme;
      THEME_PRESETS[t.id] = {
        name: t.name,
        bg: t.bg_hex,
        headerBg: t.header_bg_hex,
        border: t.border_hex,
        text: t.text_hex,
        promptColor: t.prompt_hex,
        cmdColor: t.accent_hex || '#0000ff',
        outColor: t.text_hex,
        isSecret: t.is_secret,
        windowStyle: t.window_style,
      };

      activeScreenshotTheme = t.id;
      localStorage.setItem('lg_screenshot_theme', t.id);

      // Deselect all swatch chips
      document.querySelectorAll('.theme-swatch-chip').forEach(chip => chip.classList.remove('active'));

      // Update or add select option in #terminal-theme
      const selectEl = document.getElementById('terminal-theme');
      if (selectEl) {
        let opt = Array.from(selectEl.options).find(o => o.value === t.id);
        if (!opt) {
          opt = document.createElement('option');
          opt.value = t.id;
          opt.textContent = `✨ ${t.name} (Custom Active)`;
          selectEl.appendChild(opt);
        }
        selectEl.value = t.id;
      }

      // Update theme active badge in drawer
      const badge = document.getElementById('theme-active-badge');
      if (badge) {
        badge.textContent = t.name;
      }

      // Update mini terminal preview
      updateMiniTerminalPreview(t.id, t.is_secret);

      // Update status message
      if (statusEl) {
        statusEl.style.display = 'flex';
        statusEl.className = 'custom-theme-status success';
        statusEl.innerHTML = `<span>✓ Active: <strong>${t.name}</strong> (${t.id})</span>`;
      }

      showToast(`✨ Applied theme: ${t.name}`);
    } else {
      if (statusEl) {
        statusEl.style.display = 'flex';
        statusEl.className = 'custom-theme-status error';
        statusEl.innerHTML = `<span>❌ Theme "${rawTheme}" not recognized. Type full name (e.g. bheeshamks).</span>`;
      }
      showToast(`Theme "${rawTheme}" not found`);
    }
  } catch (err) {
    console.error('Error applying custom theme:', err);
    if (statusEl) {
      statusEl.style.display = 'flex';
      statusEl.className = 'custom-theme-status error';
      statusEl.innerHTML = '<span>❌ Network error resolving theme.</span>';
    }
    showToast('Error applying theme');
  }
}

function selectThemeFromSwatch(themeId) {
  const selectEl = document.getElementById('terminal-theme');
  if (selectEl) {
    selectEl.value = themeId;
  }
  onThemeChanged(themeId, true);
}

function onThemeChanged(themeId, notify = true) {
  if (themeId === 'env_default') {
    updateMiniTerminalPreview('modern-dark', true);
    if (notify) showToast('✨ Signature theme from .env activated');
    return;
  }

  activeScreenshotTheme = themeId;
  localStorage.setItem('lg_screenshot_theme', themeId);

  // Update active swatch chip
  document.querySelectorAll('.theme-swatch-chip').forEach(chip => {
    chip.classList.remove('active');
  });
  const activeSwatch = document.getElementById(`swatch-${themeId}`);
  if (activeSwatch) {
    activeSwatch.classList.add('active');
  }

  // Update theme active badge in header
  const preset = THEME_PRESETS[themeId] || THEME_PRESETS['modern-dark'];
  const badge = document.getElementById('theme-active-badge');
  if (badge) {
    badge.textContent = preset.name.split(' (')[0];
  }

  // Clear custom theme status if user switched to a preset
  const statusEl = document.getElementById('custom-theme-status');
  if (statusEl && preset && !preset.isSecret) {
    statusEl.style.display = 'none';
  }

  // Update Live Mini Terminal Preview
  updateMiniTerminalPreview(themeId, !!preset.isSecret);

  if (notify) {
    showToast(`Screenshot theme set to ${preset.name.split(' (')[0]}`);
  }
}

function updateMiniTerminalPreview(themeId, isSecret = false) {
  const preset = THEME_PRESETS[themeId] || THEME_PRESETS['modern-dark'];
  const win = document.getElementById('mini-term-window');
  const bar = document.getElementById('mini-term-bar');
  const body = document.getElementById('mini-term-body');
  const promptEl = document.getElementById('mini-term-prompt-display');
  const cmdEl = document.getElementById('mini-term-cmd-display');
  const outEl = document.getElementById('mini-term-output');
  const paletteName = document.getElementById('mini-term-palette-name');
  const metaTag = document.getElementById('mini-term-meta-tag');

  const user = document.getElementById('terminal-username')?.value.trim() || 'student';
  const host = document.getElementById('terminal-hostname')?.value.trim() || 'linux';

  if (promptEl) {
    promptEl.textContent = `${user}@${host}:~/workspace$`;
    promptEl.style.color = preset.promptColor;
  }

  if (cmdEl) {
    cmdEl.style.color = preset.cmdColor;
  }

  if (outEl) {
    outEl.style.color = preset.outColor;
  }

  if (win) {
    win.style.borderColor = preset.border;
    win.style.background = preset.bg;
  }

  if (bar) {
    bar.style.background = preset.headerBg;
    bar.style.borderBottomColor = preset.border;
  }

  if (body) {
    body.style.background = preset.bg;
    body.style.color = preset.text;
  }

  if (paletteName) {
    paletteName.textContent = isSecret ? preset.name : preset.name.split(' (')[0];
  }

  if (metaTag) {
    metaTag.textContent = isSecret ? `⚡ Active: ${preset.name}` : `Theme: ${preset.name.split(' (')[0]}`;
  }
}

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

  // Update live mini terminal preview prompt and title
  const miniPrompt = document.getElementById('mini-term-prompt-display');
  if (miniPrompt) {
    miniPrompt.textContent = `${user}@${host}:~/workspace$`;
  }
  const miniTitle = document.getElementById('mini-term-title');
  if (miniTitle) {
    miniTitle.textContent = `${user}@${host}: ~/workspace (bash)`;
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

  // Review tasks wizard button
  const btnReviewTasks = document.getElementById('btn-review-tasks');
  if (btnReviewTasks) {
    btnReviewTasks.addEventListener('click', startWizardExtraction);
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

    // Escape -> Close any open modal or settings drawer
    if (e.key === 'Escape') {
      closeModal();
      closeEditModal();
      closeCoverEditModal();
      closeShortcutsModal();
      closeSidebarSettings();
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
  const btnRun = document.getElementById('btn-run-all');
  if (btnRun) btnRun.removeAttribute('disabled');
  const btnReview = document.getElementById('btn-review-tasks');
  if (btnReview) btnReview.removeAttribute('disabled');
}

function clearSelectedFile() {
  currentFile = null;
  document.getElementById('file-input').value = '';
  document.getElementById('selected-file-info').style.display = 'none';
  const btnRun = document.getElementById('btn-run-all');
  if (btnRun) btnRun.setAttribute('disabled', 'true');
  const btnReview = document.getElementById('btn-review-tasks');
  if (btnReview) btnReview.setAttribute('disabled', 'true');
}

async function loadSampleManual() {
  try {
    const res = await fetch('/api/sample-manual');
    const data = await res.json();
    if (data.success) {
      currentFile = { name: data.filename, is_sample: true, sample_path: data.path };
      document.getElementById('selected-filename').textContent = data.filename;
      document.getElementById('selected-file-info').style.display = 'flex';
      const btnRun = document.getElementById('btn-run-all');
      if (btnRun) btnRun.removeAttribute('disabled');
      const btnReview = document.getElementById('btn-review-tasks');
      if (btnReview) btnReview.removeAttribute('disabled');
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

function handleSubjectSelectChange() {
  const select = document.getElementById('subject-select');
  const box = document.getElementById('subject-selection-box');
  const otherContainer = document.getElementById('other-subject-container');
  const otherInput = document.getElementById('other-subject-input');
  const badge = document.getElementById('subject-hint-badge');

  if (box) box.classList.remove('highlight-required');

  const val = select ? select.value : 'auto';
  if (val === 'other') {
    if (otherContainer) otherContainer.style.display = 'block';
    if (otherInput) otherInput.focus();
    if (badge) {
      badge.textContent = 'Custom Subject';
      badge.className = 'hint-badge';
    }
  } else if (val === 'dbms') {
    if (otherContainer) otherContainer.style.display = 'none';
    if (badge) {
      badge.textContent = 'DBMS Active';
      badge.className = 'hint-badge active-badge';
    }
  } else if (val === 'dsa') {
    if (otherContainer) otherContainer.style.display = 'none';
    if (badge) {
      badge.textContent = 'DSA Active';
      badge.className = 'hint-badge active-badge';
    }
  } else {
    if (otherContainer) otherContainer.style.display = 'none';
    if (badge) {
      badge.textContent = 'Auto-Detect';
      badge.className = 'hint-badge active-badge';
    }
  }
}

async function runLabPipeline() {
  if (!currentFile) return;

  const subjectSelect = document.getElementById('subject-select');
  const selectedSubject = subjectSelect && subjectSelect.value ? subjectSelect.value.trim() : 'auto';
  const otherInput = document.getElementById('other-subject-input');
  const customSubjectName = otherInput ? otherInput.value.trim() : '';

  if (selectedSubject === 'other' && !customSubjectName) {
    if (otherInput) {
      otherInput.focus();
      otherInput.style.borderColor = '#ef4444';
    }
    alert('⚠️ Please enter your custom Subject / Course name.');
    return;
  }

  navigateToView('progress');

  startTimer();
  updateStep(1, 15, 'Parsing Lab Manual...', 'Extracting objectives and task problems...');

  const formData = new FormData();
  if (currentFile.is_sample) {
    formData.append('is_sample', 'true');
    formData.append('sample_path', currentFile.sample_path);
  } else {
    formData.append('manual_file', currentFile);
  }

  formData.append('subject', selectedSubject);
  if (selectedSubject === 'other') {
    formData.append('custom_subject', customSubjectName);
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

  const selectedProvider = document.getElementById('ai-provider').value;
  const enteredApiKey = document.getElementById('api-key')?.value.trim() || '';
  const customInst = document.getElementById('custom-instructions') ? document.getElementById('custom-instructions').value.trim() : '';

  if ((selectedProvider === 'groq' || selectedProvider === 'groq-8b') && !enteredApiKey) {
    alert("Groq Cloud requires an API Key. Please paste your free Groq API key (starts with 'gsk_...') in the API Key input box, or choose 'Smart Offline Demo Mode'.");
    document.getElementById('api-key')?.focus();
    return;
  }

  if ((selectedProvider.startsWith('gemini') || selectedProvider === 'openai') && !enteredApiKey && customInst) {
    const proceed = confirm(
      `Notice: You specified Custom Instructions, but no API Key was entered for ${selectedProvider}.\n\n` +
      `Without an API Key, LabGenius will run in Smart Offline Mode using rule-based heuristics.\n\n` +
      `• Click OK to continue in Smart Offline Mode.\n` +
      `• Click Cancel to paste your API Key in the left sidebar.`
    );
    if (!proceed) {
      document.getElementById('api-key')?.focus();
      return;
    }
  }

  formData.append('provider', selectedProvider);
  formData.append('api_key', enteredApiKey);
  formData.append('theme', document.getElementById('terminal-theme').value);

  const termUser = document.getElementById('terminal-username')?.value.trim();
  const termHost = document.getElementById('terminal-hostname')?.value.trim();
  if (termUser) formData.append('username', termUser);
  if (termHost) formData.append('hostname', termHost);

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
    navigateToView('results');

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

// ============================================================================
// APP NAVIGATION & 3-ZONE ROUTING
// ============================================================================

function navigateToView(viewName) {
  const views = ['home', 'wizard', 'progress', 'results', 'doctools', 'playground'];
  views.forEach(v => {
    const el = document.getElementById(`view-${v}`);
    if (el) {
      if (v === viewName) {
        el.style.display = 'block';
        el.classList.add('active');
      } else {
        el.style.display = 'none';
        el.classList.remove('active');
      }
    }
  });

  const uploadCard = document.getElementById('upload-card');
  const wizardCard = document.getElementById('wizard-review-card');
  const progressCard = document.getElementById('progress-card');
  const resultsContainer = document.getElementById('results-container');
  const doctoolsWorkspace = document.getElementById('doctools-workspace');

  if (viewName === 'home') {
    if (uploadCard) uploadCard.style.display = 'block';
    if (wizardCard) wizardCard.style.display = 'none';
    if (progressCard) progressCard.style.display = 'none';
    if (resultsContainer) resultsContainer.style.display = 'none';
    if (doctoolsWorkspace) doctoolsWorkspace.style.display = 'none';
  } else if (viewName === 'wizard') {
    if (uploadCard) uploadCard.style.display = 'none';
    if (wizardCard) wizardCard.style.display = 'block';
    if (progressCard) progressCard.style.display = 'none';
    if (resultsContainer) resultsContainer.style.display = 'none';
    if (doctoolsWorkspace) doctoolsWorkspace.style.display = 'none';
  } else if (viewName === 'progress') {
    if (uploadCard) uploadCard.style.display = 'none';
    if (wizardCard) wizardCard.style.display = 'none';
    if (progressCard) progressCard.style.display = 'block';
    if (resultsContainer) resultsContainer.style.display = 'none';
    if (doctoolsWorkspace) doctoolsWorkspace.style.display = 'none';
  } else if (viewName === 'results') {
    if (uploadCard) uploadCard.style.display = 'none';
    if (wizardCard) wizardCard.style.display = 'none';
    if (progressCard) progressCard.style.display = 'none';
    if (resultsContainer) resultsContainer.style.display = 'block';
    if (doctoolsWorkspace) doctoolsWorkspace.style.display = 'none';
  } else if (viewName === 'doctools') {
    if (doctoolsWorkspace) doctoolsWorkspace.style.display = 'block';
  }

  // Update topbar breadcrumb title
  const titleMap = {
    'home': 'Lab Generator',
    'wizard': 'Requirement Review',
    'progress': 'Pipeline Execution',
    'results': 'Output Studio',
    'doctools': 'Document Tools',
    'playground': 'Code Playground'
  };
  const titleEl = document.getElementById('top-bar-view-title');
  if (titleEl && titleMap[viewName]) {
    titleEl.textContent = titleMap[viewName];
  }

  // Update rail navigation active highlight
  const railHome = document.getElementById('rail-item-home');
  const railDoc = document.getElementById('rail-item-doctools');
  const railPlay = document.getElementById('rail-item-playground');
  if (railHome) railHome.classList.remove('active');
  if (railDoc) railDoc.classList.remove('active');
  if (railPlay) railPlay.classList.remove('active');

  if (viewName === 'home' || viewName === 'wizard' || viewName === 'progress' || viewName === 'results') {
    if (railHome) railHome.classList.add('active');
  } else if (viewName === 'doctools') {
    if (railDoc) railDoc.classList.add('active');
  } else if (viewName === 'playground') {
    if (railPlay) railPlay.classList.add('active');
  }

  // Active Lab Name in header
  const labNameEl = document.getElementById('top-bar-lab-name');
  if (labNameEl) {
    if (currentLabData && currentLabData.filename) {
      labNameEl.textContent = currentLabData.filename;
    } else if (currentFile && currentFile.name) {
      labNameEl.textContent = currentFile.name;
    } else {
      labNameEl.textContent = 'Workspace Ready';
    }
  }

  const viewport = document.getElementById('workspace-viewport');
  if (viewport) viewport.scrollTop = 0;
}

function toggleSidebarSettings(tabId = null) {
  const drawer = document.getElementById('settings-drawer');
  const backdrop = document.getElementById('drawer-backdrop');
  if (!drawer) return;
  const isOpen = drawer.classList.contains('open');
  if (isOpen && !tabId) {
    closeSidebarSettings();
  } else {
    drawer.classList.add('open');
    if (backdrop) backdrop.classList.add('open');
    if (tabId) switchDrawerTab(tabId);
  }
}

function closeSidebarSettings() {
  const drawer = document.getElementById('settings-drawer');
  const backdrop = document.getElementById('drawer-backdrop');
  if (drawer) drawer.classList.remove('open');
  if (backdrop) backdrop.classList.remove('open');
}

function switchDrawerTab(tabId) {
  const tabs = ['profile', 'ai', 'theme'];
  tabs.forEach(t => {
    const btn = document.getElementById(`dtab-${t}`);
    const pane = document.getElementById(`drawer-pane-${t}`);
    if (btn) btn.classList.toggle('active', t === tabId);
    if (pane) pane.classList.toggle('active', t === tabId);
  });
}

function returnToLabGeniusHome() {
  closeSidebarSettings();
  if (currentLabData) {
    navigateToView('results');
    switchMainView('pdf');
  } else {
    navigateToView('home');
  }
  showToast('Returned to Lab Generator');
}

function openNavPlayground() {
  closeSidebarSettings();
  navigateToView('playground');
  // Sync editor with code
  const codeMain = document.getElementById('scratch-code')?.value || '';
  const codeStandalone = document.getElementById('scratch-code-standalone');
  if (codeStandalone && !codeStandalone.value && codeMain) {
    codeStandalone.value = codeMain;
  }
}

function openNavTemplates() {
  openNavPlayground();
  const select = document.getElementById('scratch-template-standalone') || document.getElementById('scratch-template-select');
  if (select) {
    select.focus();
  }
}

function syncScratchLang(val) {
  const s1 = document.getElementById('scratch-lang');
  const s2 = document.getElementById('scratch-lang-standalone');
  if (s1 && s1.value !== val) s1.value = val;
  if (s2 && s2.value !== val) s2.value = val;
  onScratchLangChange();
}

function syncScratchTemplate(val) {
  const s1 = document.getElementById('scratch-template-select');
  const s2 = document.getElementById('scratch-template-standalone');
  if (s1 && s1.value !== val) s1.value = val;
  if (s2 && s2.value !== val) s2.value = val;
  loadSelectedTemplate();
}

function syncCodeTextareas(val) {
  const c1 = document.getElementById('scratch-code');
  const c2 = document.getElementById('scratch-code-standalone');
  if (c1 && c1.value !== val) c1.value = val;
  if (c2 && c2.value !== val) c2.value = val;
}

function syncStdinInputs(val) {
  const i1 = document.getElementById('scratch-stdin');
  const i2 = document.getElementById('scratch-stdin-standalone');
  if (i1 && i1.value !== val) i1.value = val;
  if (i2 && i2.value !== val) i2.value = val;
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

  navigateToView('home');
  clearSelectedFile();
  showToast('Lab closed. Ready for new manual.');
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
  navigateToView('results');

  // Quality Gate Validation Banner
  const gateBanner = document.getElementById('quality-gate-banner');
  if (gateBanner && data.validation_report) {
    const vr = data.validation_report;
    const gateTitle = document.getElementById('gate-title');
    const gateDesc = document.getElementById('gate-desc');
    const gateIcon = document.getElementById('gate-icon');
    const gatePill = document.getElementById('gate-pill-status');
    const warningsBox = document.getElementById('gate-warnings-box');
    const warningsList = document.getElementById('gate-warnings-list');

    if (vr.is_valid && (!vr.warnings || vr.warnings.length === 0)) {
      gateBanner.className = 'card quality-gate-card';
      if (gateTitle) gateTitle.textContent = 'Quality Gate Passed';
      if (gateDesc) gateDesc.textContent = '0 Execution errors • Strict undergraduate anti-AI tone • Verified output screenshots';
      if (gateIcon) gateIcon.textContent = '✓';
      if (gatePill) {
        gatePill.textContent = 'Verified Valid';
        gatePill.className = 'meta-pill meta-safe';
      }
      if (warningsBox) warningsBox.style.display = 'none';
    } else if (vr.is_valid && vr.warnings && vr.warnings.length > 0) {
      gateBanner.className = 'card quality-gate-card has-warnings';
      if (gateTitle) gateTitle.textContent = `Quality Gate Passed (${vr.warnings.length} Advisory Note${vr.warnings.length > 1 ? 's' : ''})`;
      if (gateDesc) gateDesc.textContent = 'Report generated successfully with minor observations.';
      if (gateIcon) gateIcon.textContent = '⚠';
      if (gatePill) {
        gatePill.textContent = `${vr.warnings.length} Warning${vr.warnings.length > 1 ? 's' : ''}`;
        gatePill.className = 'meta-pill';
      }
      if (warningsBox && warningsList) {
        warningsList.innerHTML = vr.warnings.map(w => `<li><strong>${w.component}:</strong> ${w.message}</li>`).join('');
        warningsBox.style.display = 'block';
      }
    } else {
      gateBanner.className = 'card quality-gate-card has-errors';
      if (gateTitle) gateTitle.textContent = `Quality Gate Check Failed (${vr.errors.length} Error${vr.errors.length > 1 ? 's' : ''})`;
      if (gateDesc) gateDesc.textContent = 'One or more tasks encountered execution or quality issues.';
      if (gateIcon) gateIcon.textContent = '✕';
      if (gatePill) {
        gatePill.textContent = 'Errors Detected';
        gatePill.className = 'meta-pill meta-danger';
      }
      if (warningsBox && warningsList) {
        warningsList.innerHTML = vr.errors.map(e => `<li><strong>${e.component}:</strong> ${e.message}</li>`).join('');
        warningsBox.style.display = 'block';
      }
    }
  }

  // Metadata Card
  document.getElementById('doc-title-text').textContent = data.filename;
  if (data.metadata) {
    document.getElementById('meta-author').textContent = `Author: ${data.metadata.creator || 'Student'}`;
    document.getElementById('meta-time').textContent = `Active Edit Time: ${data.metadata.total_time_mins || '78'} mins`;
    document.getElementById('meta-rev').textContent = `Revision: ${data.metadata.revision || '6'}`;
  }

  const enginePill = document.getElementById('meta-engine');
  if (enginePill && data.provider_used) {
    enginePill.textContent = `Engine: ${data.provider_used}`;
    enginePill.style.display = 'inline-block';
  }

  const instPill = document.getElementById('meta-custom-inst');
  if (instPill) {
    if (data.custom_instructions) {
      const truncated = data.custom_instructions.length > 35 ? data.custom_instructions.slice(0, 32) + '...' : data.custom_instructions;
      instPill.textContent = `Applied Instructions: "${truncated}"`;
      instPill.title = data.custom_instructions;
      instPill.style.display = 'inline-block';
    } else {
      instPill.style.display = 'none';
    }
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
  const subjectVal = data.course_name || 'Database Systems';

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

    const rawTitle = (task.title || '').trim();
    const cleanTitle = rawTitle.replace(/^(?:task|query|program|experiment)\s*#?\s*[0-9]+[\s:\.\u2013\u2014\-]+/i, '').trim() || rawTitle;
    const rawDesc = (task.description || '').trim();
    const cleanDesc = rawDesc.replace(/^(?:task|query|program|experiment)\s*#?\s*[0-9]+[\s:\.\u2013\u2014\-]+/i, '').trim();

    html += `
      <div class="doc-prog-block" id="doc-task-${task.task_id}">
        <div class="doc-prog-header">
          <h2 class="doc-prog-title" contenteditable="true" spellcheck="false" data-task-id="${task.task_id}" data-task-field="title">Task ${String(task.task_id).padStart(2, '0')}: ${escapeHtml(cleanTitle)}</h2>
          <div class="doc-prog-actions">
            <button class="btn-doc-edit" onclick="openEditModal(${task.task_id})">Code Modal</button>
            <button class="btn-doc-edit" onclick="sendTaskToPlayground(${task.task_id})">Playground</button>
          </div>
        </div>
        ${cleanDesc && cleanDesc.toLowerCase() !== cleanTitle.toLowerCase() ? `
          <p class="doc-prog-desc" contenteditable="true" spellcheck="true" data-task-id="${task.task_id}" data-task-field="description"><strong style="color:#111;">Question / Details:</strong> ${escapeHtml(cleanDesc)}</p>
        ` : ''}

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

  if (data.observation_tables && data.observation_tables.length > 0) {
    let obsTablesHtml = '';
    data.observation_tables.forEach((tbl, tIdx) => {
      const headers = tbl.headers || [];
      const rows = tbl.rows || [];
      const headerThs = headers.map(h => `<th style="border: 1px solid #cbd5e1; padding: 8px 12px; background: #f1f5f9; text-align: left; font-weight: 600; font-size: 12px; color: #0f172a;">${escapeHtml(h)}</th>`).join('');
      let rowTrs = '';
      rows.forEach((r, rIdx) => {
        const cells = r.map((c, cIdx) => `<td contenteditable="true" spellcheck="false" data-tbl-idx="${tIdx}" data-row-idx="${rIdx}" data-col-idx="${cIdx}" style="border: 1px solid #e2e8f0; padding: 8px 12px; font-size: 12px; color: #1e293b; outline: none;">${escapeHtml(String(c))}</td>`).join('');
        rowTrs += `<tr>${cells}</tr>`;
      });
      obsTablesHtml += `
        <div class="doc-obs-table-wrapper" style="margin-bottom: 22px;">
          <h3 style="font-size: 13.5px; font-weight: 700; color: #0f172a; margin-bottom: 8px;">${escapeHtml(tbl.title || `Table ${tIdx + 1}`)}</h3>
          <table class="doc-obs-table" style="width: 100%; border-collapse: collapse; margin-bottom: 8px;">
            <thead><tr>${headerThs}</tr></thead>
            <tbody>${rowTrs}</tbody>
          </table>
        </div>
      `;
    });
    html += `
      <div class="doc-prog-block doc-obs-block" id="doc-obs-section" style="margin-top: 24px; padding-top: 16px; border-top: 2px dashed #ccc;">
        <h2 class="doc-prog-title" style="color: #000; font-size: 16px; margin-bottom: 14px;">OBSERVATION &amp; BENCHMARK TABLES (EDITABLE)</h2>
        ${obsTablesHtml}
      </div>
    `;
  }

  if (data.analysis_answers && data.analysis_answers.length > 0) {
    let analysisCards = '';
    data.analysis_answers.forEach((item, aIdx) => {
      analysisCards += `
        <div class="doc-analysis-qa-item" style="margin-bottom: 12px; padding: 10px 14px; background: #f8fafc; border-left: 3px solid #2563eb; border-radius: 3px;">
          <div style="font-weight: 700; font-size: 13px; color: #111;">Q${aIdx + 1}: ${escapeHtml(item.question)}</div>
          <div style="font-size: 12.5px; color: #333; margin-top: 4px; line-height: 1.5;">
            <strong>Answer / Finding:</strong> <span contenteditable="true" spellcheck="true" data-analysis-idx="${aIdx}" class="editable-analysis-ans" style="padding: 1px 4px; outline: none; border-radius: 2px;">${escapeHtml(item.answer)}</span>
          </div>
        </div>
      `;
    });
    html += `
      <div class="doc-prog-block doc-analysis-block" id="doc-analysis-section" style="margin-top: 24px; padding-top: 16px; border-top: 2px dashed #ccc;">
        <h2 class="doc-prog-title" style="color: #000; font-size: 16px; margin-bottom: 14px;">PERFORMANCE ANALYSIS QUESTIONS &amp; FINDINGS (EDITABLE)</h2>
        ${analysisCards}
      </div>
    `;
  }

  if (data.viva_answers && data.viva_answers.length > 0) {
    let vivaCards = '';
    data.viva_answers.forEach((v, vIdx) => {
      vivaCards += `
        <div class="doc-viva-qa-item" style="margin-bottom: 12px; padding: 10px 14px; background: #f8f9fa; border-left: 3px solid #000; border-radius: 3px;">
          <div style="font-weight: 700; font-size: 13px; color: #111;">Q${vIdx + 1}: ${escapeHtml(v.question)}</div>
          <div style="font-size: 12.5px; color: #333; margin-top: 4px; line-height: 1.5;">
            <strong>Answer:</strong> <span contenteditable="true" spellcheck="true" data-viva-idx="${vIdx}" class="editable-viva-ans" style="padding: 1px 4px; outline: none; border-radius: 2px;">${escapeHtml(v.answer)}</span>
          </div>
        </div>
      `;
    });
    html += `
      <div class="doc-prog-block doc-viva-block" id="doc-viva-section" style="margin-top: 24px; padding-top: 16px; border-top: 2px dashed #ccc;">
        <h2 class="doc-prog-title" style="color: #000; font-size: 16px; margin-bottom: 14px;">VIVA QUESTIONS &amp; HUMANIZED ANSWERS (EDITABLE)</h2>
        ${vivaCards}
      </div>
    `;
  }

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

  const deptVal = document.getElementById('dept-name')?.value.trim() || localStorage.getItem('lg_dept') || 'Data Science';
  const subjectVal = subEl ? subEl.innerText.trim() : (currentLabData.course_name || 'Database Systems');

  const coverData = {
    name: nameEl ? nameEl.innerText.trim() : (document.getElementById('student-name')?.value || ''),
    roll_number: rollEl ? rollEl.innerText.trim() : (document.getElementById('roll-no')?.value || ''),
    section: secEl ? secEl.innerText.trim() : (document.getElementById('section-name')?.value || ''),
    lab_title: titleEl ? titleEl.innerText.trim() : (currentLabData.lab_title || ''),
    department: deptVal,
    subject: subjectVal,
    course_name: subjectVal,
    instructor: instEl ? instEl.innerText.trim() : (document.getElementById('instructor-name')?.value || ''),
    include_instructor: isInstOn,
    include_logo: isLogoOn,
    logo_choice: logoChoice,
    custom_logo_path: customLogoPath,
  };

  if (currentLabData) {
    currentLabData.course_name = subjectVal;
  }

  // Sync back to sidebar inputs and local storage
  if (document.getElementById('student-name') && coverData.name) document.getElementById('student-name').value = coverData.name;
  if (document.getElementById('roll-no') && coverData.roll_number) document.getElementById('roll-no').value = coverData.roll_number;
  if (document.getElementById('section-name') && coverData.section) document.getElementById('section-name').value = coverData.section;
  if (document.getElementById('dept-name') && deptVal) document.getElementById('dept-name').value = deptVal;
  if (document.getElementById('instructor-name') && coverData.instructor) document.getElementById('instructor-name').value = coverData.instructor;

  localStorage.setItem('lg_student_name', coverData.name);
  localStorage.setItem('lg_roll_no', coverData.roll_number);
  localStorage.setItem('lg_section', coverData.section);
  localStorage.setItem('lg_dept', deptVal);
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

  const updatedObservationTables = [];
  if (currentLabData.observation_tables && currentLabData.observation_tables.length > 0) {
    currentLabData.observation_tables.forEach((origTbl, tIdx) => {
      const updatedRows = (origTbl.rows || []).map((row, rIdx) => {
        return row.map((cellVal, cIdx) => {
          const cellEl = document.querySelector(`[data-tbl-idx="${tIdx}"][data-row-idx="${rIdx}"][data-col-idx="${cIdx}"]`);
          return cellEl ? cellEl.innerText.trim() : cellVal;
        });
      });
      updatedObservationTables.push({
        title: origTbl.title,
        headers: origTbl.headers,
        rows: updatedRows,
      });
    });
  }

  const updatedAnalysisAnswers = [];
  if (currentLabData.analysis_answers && currentLabData.analysis_answers.length > 0) {
    currentLabData.analysis_answers.forEach((origA, aIdx) => {
      const aNode = document.querySelector(`[data-analysis-idx="${aIdx}"]`);
      let ansText = aNode ? aNode.innerText.trim() : origA.answer;
      if (ansText.startsWith('Answer / Finding:')) {
        ansText = ansText.replace(/^Answer\s*\/\s*Finding:\s*/i, '').trim();
      } else if (ansText.startsWith('Answer:')) {
        ansText = ansText.replace(/^Answer:\s*/i, '').trim();
      }
      updatedAnalysisAnswers.push({
        question: origA.question,
        answer: ansText || origA.answer,
      });
    });
  }

  const updatedVivaAnswers = [];
  if (currentLabData.viva_answers && currentLabData.viva_answers.length > 0) {
    currentLabData.viva_answers.forEach((origV, vIdx) => {
      const vNode = document.querySelector(`[data-viva-idx="${vIdx}"]`);
      let ansText = vNode ? vNode.innerText.trim() : origV.answer;
      if (ansText.startsWith('Answer:')) {
        ansText = ansText.replace(/^Answer:\s*/i, '').trim();
      }
      updatedVivaAnswers.push({
        question: origV.question,
        answer: ansText || origV.answer,
      });
    });
  }

  const payload = {
    cover: coverData,
    tasks: updatedTasks,
    observation_tables: updatedObservationTables,
    analysis_answers: updatedAnalysisAnswers,
    viva_answers: updatedVivaAnswers,
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
  const doctoolsContainer = document.getElementById('view-doctools-container');

  const btnDoc = document.getElementById('btn-view-doc');
  const btnPdf = document.getElementById('btn-view-pdf');
  const btnScratch = document.getElementById('btn-view-scratchpad');
  const btnTasks = document.getElementById('btn-view-tasks');
  const btnDocTools = document.getElementById('btn-view-doctools');

  [btnDoc, btnPdf, btnScratch, btnTasks, btnDocTools].forEach(b => {
    if (b) b.classList.remove('active');
  });

  [docContainer, pdfContainer, scratchContainer, tasksContainer, doctoolsContainer].forEach(c => {
    if (c) c.style.display = 'none';
  });

  // Hide Doc Tools workspace for general lab views
  const doctoolsWorkspace = document.getElementById('doctools-workspace');
  if (viewName !== 'doctools' && doctoolsWorkspace) {
    doctoolsWorkspace.style.display = 'none';
  }

  // Handle download-card and refine-card visibility:
  const downloadCard = document.querySelector('.download-card');
  const refineCard = document.getElementById('refine-card');
  const previewActions = document.querySelector('.preview-actions');

  if (viewName === 'doctools') {
    openNavDocTools();
    return;
  } else {
    if (currentLabData) {
      if (downloadCard) downloadCard.style.display = 'flex';
      if (refineCard) refineCard.style.display = 'block';
      if (previewActions) previewActions.style.display = 'flex';
    } else {
      if (downloadCard) downloadCard.style.display = 'none';
      if (refineCard) refineCard.style.display = 'none';
      if (previewActions) previewActions.style.display = 'none';
    }
  }

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
  const lang = document.getElementById('scratch-lang-standalone')?.value || document.getElementById('scratch-lang')?.value || 'python';
  const code = (document.getElementById('scratch-code-standalone')?.value || document.getElementById('scratch-code')?.value || '').trim();
  const stdin = document.getElementById('scratch-stdin-standalone')?.value || document.getElementById('scratch-stdin')?.value || '';

  if (!code) {
    alert('Please enter or paste code to execute.');
    return;
  }

  const btn = document.getElementById('btn-run-scratchpad');
  const btnTop = document.getElementById('btn-run-scratchpad-top');
  const btnText = document.getElementById('scratch-run-text');
  const spinner = document.getElementById('scratch-spinner');
  const metrics = document.getElementById('scratch-metrics');
  const stdoutEl = document.getElementById('scratch-stdout');
  const stdoutStandaloneEl = document.getElementById('scratch-stdout-standalone');
  const stderrEl = document.getElementById('scratch-stderr');
  const stderrStandaloneEl = document.getElementById('scratch-stderr-standalone');
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

    const outText = data.stdout || '(Process finished with no standard output)';
    if (stdoutEl) stdoutEl.textContent = outText;
    if (stdoutStandaloneEl) stdoutStandaloneEl.textContent = outText;

    if (data.stderr && data.stderr.trim()) {
      if (stderrEl) {
        stderrEl.textContent = data.stderr;
        stderrEl.style.display = 'block';
      }
      if (stderrStandaloneEl) {
        stderrStandaloneEl.textContent = data.stderr;
        stderrStandaloneEl.style.display = 'block';
      }
    } else {
      if (stderrEl) stderrEl.style.display = 'none';
      if (stderrStandaloneEl) stderrStandaloneEl.style.display = 'none';
    }

  } catch (err) {
    if (btn) btn.removeAttribute('disabled');
    if (btnTop) btnTop.removeAttribute('disabled');
    if (btnText) btnText.textContent = '▶ Run Code (Ctrl+Enter)';
    if (spinner) spinner.style.display = 'none';
    if (metrics) metrics.textContent = 'Error';
    if (stdoutEl) stdoutEl.textContent = '';
    if (stdoutStandaloneEl) stdoutStandaloneEl.textContent = '';
    const errText = 'Failed to communicate with local execution runner: ' + err;
    if (stderrEl) {
      stderrEl.textContent = errText;
      stderrEl.style.display = 'block';
    }
    if (stderrStandaloneEl) {
      stderrStandaloneEl.textContent = errText;
      stderrStandaloneEl.style.display = 'block';
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

  if (data.observation_tables && data.observation_tables.length > 0) {
    const obsCard = document.createElement('div');
    obsCard.className = 'card task-card obs-card';
    let obsTablesHtml = '';
    data.observation_tables.forEach((tbl, tIdx) => {
      const headers = tbl.headers || [];
      const rows = tbl.rows || [];
      const ths = headers.map(h => `<th style="padding: 10px 14px; background: rgba(255,255,255,0.04); color: #fff; font-size: 12.5px; border: 1px solid var(--border-color); text-align: left;">${escapeHtml(h)}</th>`).join('');
      let trs = '';
      rows.forEach(r => {
        const tds = r.map(c => `<td style="padding: 10px 14px; color: var(--text-color); font-size: 12.5px; border: 1px solid var(--border-color);">${escapeHtml(String(c))}</td>`).join('');
        trs += `<tr>${tds}</tr>`;
      });
      obsTablesHtml += `
        <div style="margin-bottom: 20px;">
          <h4 style="color: #fff; font-size: 14px; font-weight: 600; margin-bottom: 10px;">${escapeHtml(tbl.title || `Table ${tIdx + 1}`)}</h4>
          <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; border: 1px solid var(--border-color); border-radius: 6px;">
              <thead><tr>${ths}</tr></thead>
              <tbody>${trs}</tbody>
            </table>
          </div>
        </div>
      `;
    });
    obsCard.innerHTML = `
      <div class="task-header">
        <div class="task-title-row">
          <span class="lang-tag" style="background: rgba(59,130,246,0.15); color: #3b82f6; border-color: rgba(59,130,246,0.3);">Benchmarks</span>
          <h3>Observation &amp; Performance Comparison Tables</h3>
        </div>
      </div>
      <p class="task-desc" style="color: var(--text-muted); margin-bottom: 16px;">Authentic experimental execution times and comparative rankings across tested array sizes.</p>
      ${obsTablesHtml}
    `;
    feed.appendChild(obsCard);
  }

  if (data.analysis_answers && data.analysis_answers.length > 0) {
    const analysisCard = document.createElement('div');
    analysisCard.className = 'card task-card analysis-card';
    let analysisQas = '';
    data.analysis_answers.forEach((item, aIdx) => {
      analysisQas += `
        <div style="margin-bottom: 14px; padding: 12px 14px; background: rgba(255,255,255,0.02); border-left: 3px solid #3b82f6; border-radius: 4px;">
          <div style="font-weight: 600; color: #fff; font-size: 13.5px;">Q${aIdx + 1}: ${escapeHtml(item.question)}</div>
          <div style="color: var(--text-muted); font-size: 13px; margin-top: 5px; line-height: 1.5;"><strong>Answer / Finding:</strong> ${escapeHtml(item.answer)}</div>
        </div>
      `;
    });
    analysisCard.innerHTML = `
      <div class="task-header">
        <div class="task-title-row">
          <span class="lang-tag" style="background: rgba(99,102,241,0.15); color: #818cf8; border-color: rgba(99,102,241,0.3);">Analysis</span>
          <h3>Performance Analysis &amp; Findings (${data.analysis_answers.length} Questions)</h3>
        </div>
      </div>
      <p class="task-desc" style="color: var(--text-muted); margin-bottom: 14px;">Detailed technical analysis explaining benchmark observations and theoretical complexity alignment.</p>
      <div class="viva-questions-list">
        ${analysisQas}
      </div>
    `;
    feed.appendChild(analysisCard);
  }

  if (data.viva_answers && data.viva_answers.length > 0) {
    const vivaCard = document.createElement('div');
    vivaCard.className = 'card task-card viva-card';
    let qas = '';
    data.viva_answers.forEach((item, vIdx) => {
      qas += `
        <div style="margin-bottom: 14px; padding: 12px 14px; background: rgba(255,255,255,0.02); border-left: 3px solid #10b981; border-radius: 4px;">
          <div style="font-weight: 600; color: #fff; font-size: 13.5px;">Q${vIdx + 1}: ${escapeHtml(item.question)}</div>
          <div style="color: var(--text-muted); font-size: 13px; margin-top: 5px; line-height: 1.5;"><strong>Answer:</strong> ${escapeHtml(item.answer)}</div>
        </div>
      `;
    });
    vivaCard.innerHTML = `
      <div class="task-header">
        <div class="task-title-row">
          <span class="lang-tag" style="background: rgba(16,185,129,0.15); color: #10b981; border-color: rgba(16,185,129,0.3);">Viva Voce</span>
          <h3>Viva Questions &amp; Humanized Answers (${data.viva_answers.length} Questions)</h3>
        </div>
      </div>
      <p class="task-desc" style="color: var(--text-muted); margin-bottom: 14px;">Natural, humanized student answers to oral examination questions detected in your lab manual.</p>
      <div class="viva-questions-list">
        ${qas}
      </div>
    `;
    feed.appendChild(vivaCard);
  }
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
  const subjectVal = currentLabData?.course_name || 'Database Systems';
  const cleanTitle = currentLabData?.lab_title || (currentLabData?.filename ? currentLabData.filename.replace('.docx', '').replace(/_/g, ' ') : 'Completed Lab Report');

  const isInstOn = document.getElementById('toggle-instructor')?.checked || false;
  const instructor = document.getElementById('instructor-name')?.value || '';

  document.getElementById('edit-cover-name').value = studentName;
  document.getElementById('edit-cover-roll').value = rollNo;
  document.getElementById('edit-cover-section').value = section;
  document.getElementById('edit-cover-subject').value = subjectVal;
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

  const deptVal = document.getElementById('dept-name')?.value || localStorage.getItem('lg_dept') || 'Data Science';

  if (document.getElementById('student-name')) document.getElementById('student-name').value = name;
  if (document.getElementById('roll-no')) document.getElementById('roll-no').value = rollNo;
  if (document.getElementById('section-name')) document.getElementById('section-name').value = section;
  if (document.getElementById('toggle-instructor')) {
    document.getElementById('toggle-instructor').checked = isInstOn;
    const sideInstWrap = document.getElementById('instructor-input-wrapper');
    if (sideInstWrap) sideInstWrap.style.display = isInstOn ? 'block' : 'none';
  }
  if (document.getElementById('instructor-name')) document.getElementById('instructor-name').value = instructor;

  if (currentLabData) {
    currentLabData.course_name = subject;
  }

  localStorage.setItem('lg_student_name', name);
  localStorage.setItem('lg_roll_no', rollNo);
  localStorage.setItem('lg_section', section);
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
  formData.append('department', deptVal);
  formData.append('subject', subject);
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

// =============================================================
// Doc Tools Studio Engine (Multi-Document Merger, Converter, Splitter, Inspector)
// =============================================================

let mergerQueue = []; // Array of { id, file, name, sizeFormatted, type }
let mergerExportFormat = 'pdf';
let lastMergedResult = null;
let currentConverterMode = 'docx2pdf';
let selectedConverterFile = null;
let selectedSplitterFile = null;
let selectedInspectorFile = null;

function openNavDocTools() {
  closeSidebarSettings();
  navigateToView('doctools');
  setupMergerDropzone();
  renderMergerQueue();
}

function updateMergerTabCount() {
  const tabBadge = document.getElementById('merger-tab-count');
  if (tabBadge) {
    tabBadge.textContent = mergerQueue.length;
    tabBadge.style.display = mergerQueue.length > 0 ? 'inline-flex' : 'none';
  }
}

function switchDocTool(toolId) {
  const tabs = ['merger', 'converter', 'splitter', 'extractor'];
  tabs.forEach(t => {
    const btn = document.getElementById(`tab-btn-${t}`);
    const panel = document.getElementById(`panel-doc-${t}`);
    if (btn) {
      if (t === toolId) {
        btn.classList.add('active');
        btn.setAttribute('aria-selected', 'true');
      } else {
        btn.classList.remove('active');
        btn.setAttribute('aria-selected', 'false');
      }
    }
    if (panel) {
      panel.style.display = (t === toolId) ? 'block' : 'none';
      if (t === toolId) panel.classList.add('active');
      else panel.classList.remove('active');
    }
  });
}

function formatByteSize(bytes) {
  if (!bytes || isNaN(bytes)) return '0 KB';
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

function getFileBadgeHtml(type) {
  const t = (type || '').toLowerCase();
  if (t === 'pdf') {
    return `<div class="file-badge pdf" title="PDF Document">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><path d="M10 12h4"></path><path d="M10 16h4"></path></svg>
    </div>`;
  }
  if (t === 'docx') {
    return `<div class="file-badge docx" title="Word Document">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><path d="M9 13v4"></path><path d="M12 15l1.5-2"></path><path d="M15 13v4"></path></svg>
    </div>`;
  }
  return `<div class="file-badge txt" title="Text Document">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>
  </div>`;
}

// -------------------------------------------------------------
// Document Merger Workspace Logic (Matching Reference input_file_0.png)
// -------------------------------------------------------------

let currentMergerStep = 1;
let mergerDropzoneInitialized = false;

function setupMergerDropzone() {
  if (mergerDropzoneInitialized) return;
  const dropzone = document.getElementById('merger-dropzone');
  if (!dropzone) return;

  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add('drag-active');
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('drag-active');
    }, false);
  });

  dropzone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    if (dt && dt.files && dt.files.length) {
      handleMergerFileList(dt.files);
    }
  }, false);

  mergerDropzoneInitialized = true;
}

function focusMergerStep(stepNum) {
  currentMergerStep = stepNum;
  updateStepperState();
}

function updateStepperState() {
  const stepCount = mergerQueue.length;
  const node1 = document.getElementById('step-node-1');
  const node2 = document.getElementById('step-node-2');
  const node3 = document.getElementById('step-node-3');
  const conn1 = document.getElementById('step-conn-1');
  const conn2 = document.getElementById('step-conn-2');

  if (node1) {
    node1.classList.toggle('active', currentMergerStep === 1 || stepCount === 0);
    node1.classList.toggle('completed', stepCount > 0 && currentMergerStep > 1);
  }
  if (node2) {
    node2.classList.toggle('active', currentMergerStep === 2 || (stepCount > 0 && currentMergerStep !== 3));
    node2.classList.toggle('completed', currentMergerStep === 3);
  }
  if (node3) {
    node3.classList.toggle('active', currentMergerStep === 3);
  }
  if (conn1) {
    conn1.classList.toggle('active', stepCount > 0);
  }
  if (conn2) {
    conn2.classList.toggle('active', currentMergerStep === 3);
  }
}

function handleMergerFilesSelected(event) {
  const files = event.target.files;
  if (!files || !files.length) return;
  handleMergerFileList(files);
  event.target.value = '';
}

function handleMergerFileList(filesList) {
  const files = Array.from(filesList);
  if (!files.length) return;

  let addedCount = 0;
  files.forEach(file => {
    const ext = file.name.split('.').pop().toLowerCase();
    if (ext !== 'pdf' && ext !== 'docx' && ext !== 'txt') {
      showToast(`Skipped "${file.name}" (supports PDF, DOCX, TXT)`);
      return;
    }
    mergerQueue.push({
      id: 'doc_' + Math.random().toString(36).substring(2, 9),
      file: file,
      name: file.name,
      sizeFormatted: formatByteSize(file.size),
      type: ext
    });
    addedCount++;
  });

  if (addedCount > 0) {
    currentMergerStep = 2;
    showToast(`Added ${addedCount} document${addedCount === 1 ? '' : 's'}!`);
  }
  renderMergerQueue();
}

function renderMergerQueue() {
  const listEl = document.getElementById('merger-selected-files-list');
  const selectedCountEl = document.getElementById('merger-selected-count');
  const clearBtn = document.getElementById('btn-clear-queue');
  const summaryCountEl = document.getElementById('summary-file-count');
  const summarySizeEl = document.getElementById('summary-total-size');
  const summaryOrderList = document.getElementById('summary-file-order-list');
  const executeBtn = document.getElementById('btn-execute-merge');

  updateMergerTabCount();
  updateStepperState();

  const count = mergerQueue.length;

  if (selectedCountEl) selectedCountEl.textContent = count;
  if (clearBtn) clearBtn.style.display = count > 0 ? 'inline-block' : 'none';
  if (summaryCountEl) {
    summaryCountEl.textContent = `${count} file${count === 1 ? '' : 's'} selected`;
  }

  // Calculate total size
  let totalBytes = 0;
  mergerQueue.forEach(item => {
    if (item.file && typeof item.file.size === 'number' && item.file.size > 1000) {
      totalBytes += item.file.size;
    } else if (item.sizeFormatted) {
      const parts = item.sizeFormatted.trim().split(' ');
      const val = parseFloat(parts[0]);
      if (!isNaN(val)) {
        if (parts[1] === 'MB') totalBytes += val * 1024 * 1024;
        else if (parts[1] === 'KB') totalBytes += val * 1024;
        else totalBytes += val;
      }
    }
  });
  if (summarySizeEl) {
    summarySizeEl.textContent = `Total size: ${formatByteSize(totalBytes)}`;
  }

  // Render Selected Files List in Left Column
  if (listEl) {
    if (count === 0) {
      listEl.innerHTML = `
        <div class="merger-empty-row-hint">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" style="opacity:0.4; margin-bottom: 6px;"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
          <p>No documents selected yet. Upload files above or load sample documents.</p>
        </div>
      `;
    } else {
      listEl.innerHTML = mergerQueue.map((item, idx) => `
        <div class="merger-file-card" draggable="true" data-index="${idx}" id="merger-file-card-${idx}">
          <div class="file-card-left">
            ${getFileBadgeHtml(item.type)}
            <div class="file-card-details">
              <span class="file-card-name" title="${escapeHtml(item.name)}">${escapeHtml(item.name)}</span>
              <span class="file-card-sub">${item.sizeFormatted} • ${item.type.toUpperCase()}</span>
            </div>
          </div>
          <div class="file-card-actions">
            <div class="file-drag-grip" title="Drag to reorder sequence" aria-label="Drag handle">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="9" cy="5" r="1.5"></circle><circle cx="9" cy="12" r="1.5"></circle><circle cx="9" cy="19" r="1.5"></circle><circle cx="15" cy="5" r="1.5"></circle><circle cx="15" cy="12" r="1.5"></circle><circle cx="15" cy="19" r="1.5"></circle></svg>
            </div>
            <button type="button" class="file-delete-btn" onclick="removeMergerItem(${idx})" title="Remove file" aria-label="Remove ${escapeHtml(item.name)}">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
            </button>
          </div>
        </div>
      `).join('');
      attachMergerDragAndDrop();
    }
  }

  // Render File Order in Right Column Summary
  if (summaryOrderList) {
    if (count === 0) {
      summaryOrderList.innerHTML = '<div class="empty-order-hint">Add documents to arrange order</div>';
    } else {
      summaryOrderList.innerHTML = mergerQueue.map((item, idx) => `
        <div class="summary-order-item">
          <span class="summary-order-num">${idx + 1}</span>
          <span class="summary-order-name" title="${escapeHtml(item.name)}">${escapeHtml(item.name)}</span>
        </div>
      `).join('');
    }
  }

  // Update Execution Button
  if (executeBtn) {
    executeBtn.disabled = count === 0;
  }
}

function attachMergerDragAndDrop() {
  const cards = document.querySelectorAll('.merger-file-card');
  let draggedIndex = null;

  cards.forEach(card => {
    card.addEventListener('dragstart', (e) => {
      draggedIndex = parseInt(card.getAttribute('data-index'), 10);
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', draggedIndex);
      setTimeout(() => card.classList.add('dragging'), 0);
    });

    card.addEventListener('dragend', () => {
      card.classList.remove('dragging');
      document.querySelectorAll('.merger-file-card').forEach(el => {
        el.classList.remove('drag-over-top', 'drag-over-bottom');
      });
    });

    card.addEventListener('dragover', (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      const rect = card.getBoundingClientRect();
      const mid = rect.top + rect.height / 2;
      card.classList.remove('drag-over-top', 'drag-over-bottom');
      if (e.clientY < mid) {
        card.classList.add('drag-over-top');
      } else {
        card.classList.add('drag-over-bottom');
      }
    });

    card.addEventListener('dragleave', () => {
      card.classList.remove('drag-over-top', 'drag-over-bottom');
    });

    card.addEventListener('drop', (e) => {
      e.preventDefault();
      const targetIndex = parseInt(card.getAttribute('data-index'), 10);
      card.classList.remove('drag-over-top', 'drag-over-bottom');

      if (draggedIndex === null || draggedIndex === targetIndex) return;

      const rect = card.getBoundingClientRect();
      const mid = rect.top + rect.height / 2;
      let newIndex = (e.clientY < mid) ? targetIndex : targetIndex + 1;
      if (draggedIndex < newIndex) {
        newIndex--;
      }

      const moved = mergerQueue.splice(draggedIndex, 1)[0];
      mergerQueue.splice(newIndex, 0, moved);
      renderMergerQueue();
      showToast('Reordered merge sequence');
    });
  });
}

function removeMergerItem(index) {
  if (index >= 0 && index < mergerQueue.length) {
    const removed = mergerQueue.splice(index, 1)[0];
    renderMergerQueue();
    showToast(`Removed "${removed.name}"`);
  }
}

function clearMergerQueue() {
  if (!mergerQueue.length) return;
  if (confirm('Are you sure you want to clear all selected documents?')) {
    mergerQueue = [];
    currentMergerStep = 1;
    renderMergerQueue();
    const resultCard = document.getElementById('merger-result-card');
    if (resultCard) resultCard.style.display = 'none';
    showToast('Cleared all documents');
  }
}

function selectExportFormat(format) {
  mergerExportFormat = format;
  const cardPdf = document.getElementById('format-card-pdf');
  const cardDocx = document.getElementById('format-card-docx');

  if (cardPdf) cardPdf.classList.toggle('active', format === 'pdf');
  if (cardDocx) cardDocx.classList.toggle('active', format === 'docx');
}

async function loadSampleMergeFiles() {
  try {
    showToast('Loading sample documents...');
    const res = await fetch('/api/doc-tools/sample-files');
    const data = await res.json();
    if (!data.samples || !data.samples.length) {
      throw new Error('No sample files available.');
    }

    mergerQueue = []; // Reset to load fresh reference sample set
    for (const s of data.samples) {
      const fileRes = await fetch(s.url);
      const blob = await fileRes.blob();
      let mimeType = 'text/plain';
      if (s.type === 'pdf') mimeType = 'application/pdf';
      else if (s.type === 'docx') mimeType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';

      const fileObj = new File([blob], s.name, { type: mimeType });
      mergerQueue.push({
        id: 'sample_' + Math.random().toString(36).substring(2, 9),
        file: fileObj,
        name: s.name,
        sizeFormatted: s.size_formatted,
        type: s.type
      });
    }

    currentMergerStep = 2;
    renderMergerQueue();
    showToast('Loaded 3 sample documents! Ready to merge.');
  } catch (err) {
    console.error('Failed to load samples:', err);
    showToast('Failed to load sample documents: ' + err.message);
  }
}

async function executeDocumentMerge() {
  if (!mergerQueue.length) {
    showToast('Please add at least one document to merge.');
    return;
  }

  const btn = document.getElementById('btn-execute-merge');
  const spinner = document.getElementById('merger-spinner');
  const btnText = document.getElementById('btn-merge-text');
  const resultCard = document.getElementById('merger-result-card');

  btn.disabled = true;
  if (spinner) spinner.style.display = 'inline-block';
  if (btnText) btnText.textContent = 'Merging Documents...';
  if (resultCard) resultCard.style.display = 'none';

  try {
    const formData = new FormData();
    const orderedNames = [];

    mergerQueue.forEach(item => {
      formData.append('files', item.file, item.name);
      orderedNames.push(item.name);
    });

    formData.append('order', JSON.stringify(orderedNames));
    formData.append('export_format', mergerExportFormat);
    const filenameInput = document.getElementById('merger-out-filename');
    if (filenameInput && filenameInput.value.trim()) {
      formData.append('filename', filenameInput.value.trim());
    }
    formData.append('page_break', 'true');

    const res = await fetch('/api/doc-tools/merge', {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Merging failed');
    }

    const data = await res.json();
    lastMergedResult = data;
    currentMergerStep = 3;
    updateStepperState();

    // Display Result Card
    if (resultCard) {
      resultCard.style.display = 'block';
      const titleEl = document.getElementById('result-title');
      const filenamePill = document.getElementById('result-filename-pill');
      const sizePill = document.getElementById('result-size-pill');
      const pagesPill = document.getElementById('result-pages-pill');
      const downloadBtn = document.getElementById('btn-download-merged');
      const previewBtn = document.getElementById('btn-preview-merged');

      if (titleEl) titleEl.textContent = `Merged Successfully into ${data.format.toUpperCase()}`;
      if (filenamePill) filenamePill.textContent = data.filename;
      if (sizePill) sizePill.textContent = data.size_formatted;
      if (pagesPill) {
        if (data.format === 'pdf' && data.page_count) {
          pagesPill.textContent = `${data.page_count} Pages`;
          pagesPill.style.display = 'inline-block';
        } else if (data.format === 'docx' && data.paragraph_count) {
          pagesPill.textContent = `${data.paragraph_count} Paragraphs`;
          pagesPill.style.display = 'inline-block';
        } else {
          pagesPill.style.display = 'none';
        }
      }

      if (downloadBtn) {
        downloadBtn.href = data.download_url;
        downloadBtn.setAttribute('download', data.filename);
      }

      if (previewBtn) {
        previewBtn.style.display = (data.format === 'pdf' || data.preview_url) ? 'inline-flex' : 'none';
      }

      resultCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    showToast(`Successfully merged into ${data.filename}!`);
  } catch (err) {
    console.error('Merge error:', err);
    showToast('Document merge failed: ' + err.message);
  } finally {
    btn.disabled = false;
    if (spinner) spinner.style.display = 'none';
    if (btnText) btnText.textContent = 'Merge Documents >';
  }
}

function previewMergedDocument() {
  if (!lastMergedResult) return;
  if (lastMergedResult.preview_url) {
    const frame = document.getElementById('pdf-embed-frame');
    if (frame) {
      frame.src = lastMergedResult.preview_url;
    }
    const doctoolsWorkspace = document.getElementById('doctools-workspace');
    if (doctoolsWorkspace) doctoolsWorkspace.style.display = 'none';
    const resultsContainer = document.getElementById('results-container');
    if (resultsContainer) resultsContainer.style.display = 'block';
    switchMainView('pdf');
  } else {
    window.open(lastMergedResult.download_url, '_blank');
  }
}

function resetMergerWorkflow() {
  mergerQueue = [];
  lastMergedResult = null;
  const resultCard = document.getElementById('merger-result-card');
  if (resultCard) resultCard.style.display = 'none';
  currentMergerStep = 1;
  renderMergerQueue();
}

function resetMergerForm() {
  resetMergerWorkflow();
}

// -------------------------------------------------------------
// Format Converter Logic
// -------------------------------------------------------------

function setConverterMode(mode) {
  currentConverterMode = mode;
  const btnDocx = document.getElementById('btn-mode-docx2pdf');
  const btnPdf = document.getElementById('btn-mode-pdf2docx');
  const title = document.getElementById('converter-drop-title');
  const input = document.getElementById('converter-file-input');
  const selectedPill = document.getElementById('converter-selected-file');
  const convertBtn = document.getElementById('btn-run-convert');
  const resultBox = document.getElementById('converter-result-box');

  if (resultBox) resultBox.style.display = 'none';
  if (selectedPill) selectedPill.style.display = 'none';
  selectedConverterFile = null;
  if (convertBtn) convertBtn.disabled = true;

  if (mode === 'docx2pdf') {
    if (btnDocx) btnDocx.classList.add('active');
    if (btnPdf) btnPdf.classList.remove('active');
    if (title) title.textContent = 'Select Word (.docx) file to convert to PDF';
    if (input) input.accept = '.docx';
  } else {
    if (btnPdf) btnPdf.classList.add('active');
    if (btnDocx) btnDocx.classList.remove('active');
    if (title) title.textContent = 'Select PDF file to convert to Word (.docx)';
    if (input) input.accept = '.pdf';
  }
}

function handleConverterFileSelected(event) {
  const file = event.target.files[0];
  if (!file) return;
  selectedConverterFile = file;

  const pill = document.getElementById('converter-selected-file');
  if (pill) {
    pill.innerHTML = `
      <div style="display:flex;align-items:center;gap:6px;">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
        <span>${escapeHtml(file.name)}</span>
        <span style="color:var(--text-muted);">(${formatByteSize(file.size)})</span>
      </div>
    `;
    pill.style.display = 'inline-block';
  }

  const btn = document.getElementById('btn-run-convert');
  if (btn) btn.disabled = false;
  showToast(`Selected ${file.name}`);
}

async function runDocumentConvert() {
  if (!selectedConverterFile) return;

  const btn = document.getElementById('btn-run-convert');
  const spinner = document.getElementById('converter-spinner');
  const resultBox = document.getElementById('converter-result-box');
  const resultText = document.getElementById('converter-result-text');
  const downloadLink = document.getElementById('btn-download-converted');

  btn.disabled = true;
  if (spinner) spinner.style.display = 'inline-block';
  if (resultBox) resultBox.style.display = 'none';

  try {
    const formData = new FormData();
    formData.append('file', selectedConverterFile);
    formData.append('target_format', currentConverterMode === 'docx2pdf' ? 'pdf' : 'docx');

    const res = await fetch('/api/doc-tools/convert', {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Conversion failed');
    }

    const data = await res.json();
    if (resultBox) resultBox.style.display = 'flex';
    if (resultText) resultText.textContent = `Converted: ${data.filename} (${data.size_formatted})`;
    if (downloadLink) {
      downloadLink.href = data.download_url;
      downloadLink.setAttribute('download', data.filename);
    }
    showToast(`Converted into ${data.filename}!`);
  } catch (err) {
    showToast('Conversion error: ' + err.message);
  } finally {
    btn.disabled = false;
    if (spinner) spinner.style.display = 'none';
  }
}

// -------------------------------------------------------------
// PDF Page Splitter Logic
// -------------------------------------------------------------

function handleSplitterFileSelected(event) {
  const file = event.target.files[0];
  if (!file) return;
  selectedSplitterFile = file;

  const pill = document.getElementById('splitter-selected-file');
  if (pill) {
    pill.innerHTML = `
      <div style="display:flex;align-items:center;gap:6px;">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
        <span>${escapeHtml(file.name)}</span>
        <span style="color:var(--text-muted);">(${formatByteSize(file.size)})</span>
      </div>
    `;
    pill.style.display = 'inline-block';
  }

  const controls = document.getElementById('splitter-controls');
  if (controls) controls.style.display = 'block';

  // Inspect total pages
  const form = new FormData();
  form.append('file', file);
  fetch('/api/doc-tools/inspect', { method: 'POST', body: form })
    .then(r => r.json())
    .then(data => {
      const totalEl = document.getElementById('splitter-total-pages');
      if (totalEl) totalEl.textContent = data.page_count || '1+';
      showToast(`Detected ${data.page_count || 1} pages in ${file.name}`);
    })
    .catch(() => {});
}

async function runDocumentSplit() {
  if (!selectedSplitterFile) return;

  const rangeInput = document.getElementById('splitter-range-input');
  const rangeVal = rangeInput ? rangeInput.value.trim() : '1';
  if (!rangeVal) {
    showToast('Please enter a valid page range (e.g. 1-3, 5).');
    return;
  }

  const btn = document.getElementById('btn-run-split');
  const spinner = document.getElementById('splitter-spinner');
  const resultBox = document.getElementById('splitter-result-box');
  const resultText = document.getElementById('splitter-result-text');
  const downloadLink = document.getElementById('btn-download-split');

  btn.disabled = true;
  if (spinner) spinner.style.display = 'inline-block';
  if (resultBox) resultBox.style.display = 'none';

  try {
    const formData = new FormData();
    formData.append('file', selectedSplitterFile);
    formData.append('page_ranges', rangeVal);

    const res = await fetch('/api/doc-tools/extract-pages', {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Extraction failed');
    }

    const data = await res.json();
    if (resultBox) resultBox.style.display = 'flex';
    if (resultText) resultText.textContent = `Extracted ${data.extracted_pages_count} pages (${data.size_formatted})`;
    if (downloadLink) {
      downloadLink.href = data.download_url;
      downloadLink.setAttribute('download', data.filename);
    }
    showToast(`Pages extracted into ${data.filename}!`);
  } catch (err) {
    showToast('Split error: ' + err.message);
  } finally {
    btn.disabled = false;
    if (spinner) spinner.style.display = 'none';
  }
}

// -------------------------------------------------------------
// Document Text & Info Inspector Logic
// -------------------------------------------------------------

async function handleInspectorFileSelected(event) {
  const file = event.target.files[0];
  if (!file) return;

  const resultsDiv = document.getElementById('inspector-results');
  if (resultsDiv) resultsDiv.style.display = 'block';

  document.getElementById('inspect-filename').textContent = `File: ${file.name}`;
  document.getElementById('inspect-size').textContent = formatByteSize(file.size);
  document.getElementById('inspect-text-content').value = 'Analyzing document and extracting text...';

  try {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch('/api/doc-tools/inspect', {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Inspection failed');
    }

    const data = await res.json();
    document.getElementById('inspect-words').textContent = `${data.word_count} Words`;
    document.getElementById('inspect-chars').textContent = `${data.char_count} Chars`;
    if (data.format === 'pdf') {
      document.getElementById('inspect-pages').textContent = `${data.page_count} Pages`;
    } else {
      document.getElementById('inspect-pages').textContent = `${data.paragraph_count} Paragraphs`;
    }
    document.getElementById('inspect-text-content').value = data.text_preview || '(No text extracted)';
    showToast(`Extracted text from ${file.name}`);
  } catch (err) {
    document.getElementById('inspect-text-content').value = 'Error extracting text: ' + err.message;
    showToast('Inspection failed: ' + err.message);
  }
}

function copyInspectedText() {
  const area = document.getElementById('inspect-text-content');
  if (area && area.value) {
    navigator.clipboard.writeText(area.value);
    showToast('Copied extracted text!');
  }
}

// ==========================================================================
// Wizard Step 2: Extraction & Interactive Review
// ==========================================================================

let wizardSessionData = null;

async function startWizardExtraction() {
  if (!currentFile) return;

  const subjectSelect = document.getElementById('subject-select');
  const selectedSubject = subjectSelect && subjectSelect.value ? subjectSelect.value.trim() : 'auto';
  const otherInput = document.getElementById('other-subject-input');
  const customSubjectName = otherInput ? otherInput.value.trim() : '';

  if (selectedSubject === 'other' && !customSubjectName) {
    if (otherInput) {
      otherInput.focus();
      otherInput.style.borderColor = '#ef4444';
    }
    alert('⚠️ Please enter your custom Subject / Course name.');
    return;
  }

  const btnReview = document.getElementById('btn-review-tasks');
  const originalBtnText = btnReview ? btnReview.innerHTML : '';
  if (btnReview) {
    btnReview.setAttribute('disabled', 'true');
    btnReview.innerHTML = '<span>⏳ Analyzing Manual &amp; Extracting...</span>';
  }

  const formData = new FormData();
  if (currentFile.is_sample) {
    formData.append('is_sample', 'true');
    formData.append('sample_path', currentFile.sample_path);
  } else {
    formData.append('manual_file', currentFile);
  }

  formData.append('subject', selectedSubject);
  if (selectedSubject === 'other') formData.append('custom_subject', customSubjectName);
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

  const isLogoOn = document.getElementById('toggle-uni-logo')?.checked ?? true;
  formData.append('include_logo', isLogoOn ? 'true' : 'false');
  const logoChoice = document.getElementById('logo-choice-select')?.value || 'dawood';
  formData.append('logo_choice', logoChoice);
  const customLogoFile = document.getElementById('custom-logo-file')?.files?.[0];
  if (customLogoFile) formData.append('custom_logo', customLogoFile);

  try {
    const res = await fetch('/api/extract-manual', {
      method: 'POST',
      body: formData,
    });
    const data = await res.json();

    if (!data.success) {
      alert('Error extracting manual: ' + (data.error || 'Failed to parse manual.'));
      if (btnReview) {
        btnReview.removeAttribute('disabled');
        btnReview.innerHTML = originalBtnText;
      }
      return;
    }

    wizardSessionData = data;
    renderWizardReview(data);
    navigateToView('wizard');

  } catch (err) {
    alert('Extraction request failed: ' + err);
  } finally {
    if (btnReview) {
      btnReview.removeAttribute('disabled');
      btnReview.innerHTML = originalBtnText;
    }
  }
}

function renderWizardReview(data) {
  const manual = data.manual || {};
  const tasks = data.tasks || [];
  const analysisQuestions = data.analysis_questions || [];

  const courseBadge = document.getElementById('badge-detected-course');
  if (courseBadge) courseBadge.textContent = manual.course_name || 'Computer Science';
  const taskCountBadge = document.getElementById('badge-task-count');
  if (taskCountBadge) taskCountBadge.textContent = `${tasks.length} Task${tasks.length === 1 ? '' : 's'}`;
  const analysisCountBadge = document.getElementById('badge-analysis-count');
  if (analysisCountBadge) analysisCountBadge.textContent = `${analysisQuestions.length} Question${analysisQuestions.length === 1 ? '' : 's'}`;

  const titleEl = document.getElementById('overview-lab-title');
  if (titleEl) titleEl.textContent = manual.title || 'Laboratory Report';
  const objEl = document.getElementById('overview-lab-objectives');
  if (objEl) {
    const objText = (manual.objectives && manual.objectives.length > 0)
      ? manual.objectives.slice(0, 3).join(' • ')
      : 'Follow standard experimental and implementation procedure.';
    objEl.textContent = `Objectives: ${objText}`;
  }

  const tasksCountNum = document.getElementById('review-tasks-count-num');
  if (tasksCountNum) tasksCountNum.textContent = tasks.length;
  const qCountNum = document.getElementById('review-questions-count-num');
  if (qCountNum) qCountNum.textContent = analysisQuestions.length;

  // Render tasks
  const tasksList = document.getElementById('review-tasks-list');
  if (tasksList) {
    tasksList.innerHTML = '';
    tasks.forEach((t, idx) => {
      tasksList.appendChild(createTaskReviewElement(t, idx + 1));
    });
  }

  // Render questions
  const qSection = document.getElementById('review-analysis-section');
  const qList = document.getElementById('review-questions-list');
  if (qList) {
    qList.innerHTML = '';
    if (analysisQuestions.length > 0) {
      if (qSection) qSection.style.display = 'block';
      analysisQuestions.forEach((q, idx) => {
        const qText = typeof q === 'string' ? q : (q.question || '');
        qList.appendChild(createQuestionReviewElement(qText, idx + 1));
      });
    } else {
      if (qSection) qSection.style.display = 'none';
    }
  }
}

function createTaskReviewElement(task, num) {
  const card = document.createElement('div');
  card.className = 'review-task-card';
  card.dataset.taskId = task.task_id || num;

  const lang = (task.language || 'c').toLowerCase();
  card.innerHTML = `
    <div class="review-task-top-row">
      <span class="task-num-badge">Task ${num}</span>
      <input type="text" class="review-task-title-input" value="${escapeHtml(task.title || `Task ${num}`)}" placeholder="Task Title" />
      <select class="review-task-lang-select">
        <option value="c" ${lang === 'c' ? 'selected' : ''}>C (gcc)</option>
        <option value="python" ${lang === 'python' ? 'selected' : ''}>Python 3</option>
        <option value="sql" ${lang === 'sql' ? 'selected' : ''}>SQL</option>
        <option value="cpp" ${lang === 'cpp' ? 'selected' : ''}>C++</option>
        <option value="java" ${lang === 'java' ? 'selected' : ''}>Java</option>
      </select>
      <button type="button" class="btn btn-outline btn-xs" onclick="removeReviewTask(this)" title="Remove this task">✕</button>
    </div>
    <textarea class="review-task-desc-input" rows="2" placeholder="Task description and requirements...">${escapeHtml(task.description || '')}</textarea>
  `;
  return card;
}

function createQuestionReviewElement(qText, num) {
  const card = document.createElement('div');
  card.className = 'review-question-card';
  card.innerHTML = `
    <span class="question-num-badge">Q${num}</span>
    <input type="text" class="review-question-input" value="${escapeHtml(qText)}" placeholder="Analysis question text..." />
    <button type="button" class="btn btn-outline btn-xs" onclick="removeReviewQuestion(this)" title="Remove question">✕</button>
  `;
  return card;
}

function addNewReviewTask() {
  const tasksList = document.getElementById('review-tasks-list');
  if (!tasksList) return;
  const count = tasksList.querySelectorAll('.review-task-card').length + 1;
  const newTask = {
    task_id: count,
    title: `Task ${count}: Implementation`,
    description: '',
    language: 'c',
  };
  tasksList.appendChild(createTaskReviewElement(newTask, count));
  const countEl = document.getElementById('review-tasks-count-num');
  if (countEl) countEl.textContent = count;
}

function removeReviewTask(btn) {
  const card = btn.closest('.review-task-card');
  if (card) card.remove();
  const tasksList = document.getElementById('review-tasks-list');
  const count = tasksList ? tasksList.querySelectorAll('.review-task-card').length : 0;
  const countEl = document.getElementById('review-tasks-count-num');
  if (countEl) countEl.textContent = count;
}

function addNewReviewQuestion() {
  const qList = document.getElementById('review-questions-list');
  if (!qList) return;
  const count = qList.querySelectorAll('.review-question-card').length + 1;
  qList.appendChild(createQuestionReviewElement('', count));
  const qSection = document.getElementById('review-analysis-section');
  if (qSection) qSection.style.display = 'block';
  const countEl = document.getElementById('review-questions-count-num');
  if (countEl) countEl.textContent = count;
}

function removeReviewQuestion(btn) {
  const card = btn.closest('.review-question-card');
  if (card) card.remove();
  const qList = document.getElementById('review-questions-list');
  const count = qList ? qList.querySelectorAll('.review-question-card').length : 0;
  const countEl = document.getElementById('review-questions-count-num');
  if (countEl) countEl.textContent = count;
}

function backToUploadStep() {
  navigateToView('home');
}

async function generateFromConfirmedSession() {
  if (!wizardSessionData || !wizardSessionData.session_id) {
    alert('Session expired. Please re-upload your manual.');
    backToUploadStep();
    return;
  }

  // Collect tasks
  const taskCards = document.querySelectorAll('#review-tasks-list .review-task-card');
  const tasks = [];
  taskCards.forEach((c, idx) => {
    const titleInput = c.querySelector('.review-task-title-input');
    const langSelect = c.querySelector('.review-task-lang-select');
    const descInput = c.querySelector('.review-task-desc-input');
    tasks.push({
      task_id: idx + 1,
      title: titleInput ? titleInput.value.trim() : `Task ${idx + 1}`,
      language: langSelect ? langSelect.value : 'c',
      description: descInput ? descInput.value.trim() : '',
    });
  });

  if (tasks.length === 0) {
    alert('⚠️ Please add at least one lab task before starting generation.');
    return;
  }

  // Collect analysis questions
  const qCards = document.querySelectorAll('#review-questions-list .review-question-card');
  const analysisQuestions = [];
  qCards.forEach(c => {
    const input = c.querySelector('.review-question-input');
    if (input && input.value.trim()) {
      analysisQuestions.push(input.value.trim());
    }
  });

  const selectedProvider = document.getElementById('ai-provider').value;
  const enteredApiKey = document.getElementById('api-key')?.value.trim() || '';
  const customInst = document.getElementById('custom-instructions') ? document.getElementById('custom-instructions').value.trim() : '';

  const formats = [];
  if (document.getElementById('fmt-pdf')?.checked) formats.push('pdf');
  if (document.getElementById('fmt-docx')?.checked) formats.push('docx');

  // Transition UI to Progress bar
  navigateToView('progress');

  startTimer();
  updateStep(1, 15, 'Validating Requirements...', 'Requirements confirmed by student. Initializing orchestrator...');

  let isPipelineRunning = true;
  const stepTimers = [];
  stepTimers.push(setTimeout(() => { if (isPipelineRunning) updateStep(2, 30, 'Synthesizing Student Solutions...', 'Orchestrating code generation with undergraduate persona...'); }, 1200));
  stepTimers.push(setTimeout(() => { if (isPipelineRunning) updateStep(3, 50, 'Sandboxed Execution & Healing...', 'Executing code solutions locally with timeout protection...'); }, 3500));
  stepTimers.push(setTimeout(() => { if (isPipelineRunning) updateStep(4, 75, 'Terminal Capture & Quality Gate...', 'Capturing Linux terminal windows and running Quality Gate checks...'); }, 6000));

  try {
    const payload = {
      session_id: wizardSessionData.session_id,
      provider: selectedProvider,
      api_key: enteredApiKey,
      theme: document.getElementById('terminal-theme').value,
      instructions: customInst,
      formats: formats.join(','),
      tasks: tasks,
      analysis_questions: analysisQuestions,
    };

    const res = await fetch('/api/generate-from-session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    isPipelineRunning = false;
    stepTimers.forEach(t => clearTimeout(t));
    stopTimer();

    const result = await res.json();
    if (!result.success) {
      alert('Error during generation: ' + (result.error || 'Unknown generation failure'));
      document.getElementById('wizard-review-card').style.display = 'block';
      document.getElementById('progress-card').style.display = 'none';
      return;
    }

    renderResults(result);

  } catch (err) {
    isPipelineRunning = false;
    stepTimers.forEach(t => clearTimeout(t));
    stopTimer();
    alert('Pipeline network error: ' + err);
    document.getElementById('wizard-review-card').style.display = 'block';
    document.getElementById('progress-card').style.display = 'none';
  }
}



// ============================================================================
// FIRST-PARTY WEBMCP AGENT TOOLS (WebMCP Specification)
// ============================================================================

function registerWebMCPTools() {
  const modelContext = navigator.modelContext || document.modelContext;
  if (!modelContext || typeof modelContext.registerTool !== 'function') {
    console.info('[WebMCP] ModelContext not exposed in current browser.');
    return;
  }

  // 1. generate_lab
  modelContext.registerTool({
    name: 'generate_lab',
    description: 'Autonomous lab completer: generates student code, runs in sandbox, captures terminal screenshots, and builds formatted PDF/Word report.',
    inputSchema: {
      type: 'object',
      properties: {
        subject: {
          type: 'string',
          enum: ['auto', 'dbms', 'dsa', 'other'],
          description: 'Academic subject domain.'
        },
        custom_subject: {
          type: 'string',
          description: 'Custom subject name when subject is other.'
        },
        instructions: {
          type: 'string',
          description: 'Special persona instructions, e.g. "Add detailed comments".'
        },
        export_pdf: {
          type: 'boolean',
          description: 'Whether to generate high-resolution PDF report.'
        },
        export_docx: {
          type: 'boolean',
          description: 'Whether to generate sanitized Word (.docx) report.'
        },
        use_sample: {
          type: 'boolean',
          description: 'Whether to use built-in sample Data Science lab manual.'
        }
      },
      additionalProperties: false
    },
    readOnlyHint: false,
    untrustedContentHint: true,
    handler: async (args) => {
      const parsed = typeof args === 'string' ? JSON.parse(args) : args;
      if (parsed.use_sample) {
        await loadSampleManual();
      }
      if (parsed.instructions) {
        const instEl = document.getElementById('custom-instructions');
        if (instEl) instEl.value = parsed.instructions;
      }
      if (parsed.subject) {
        const subEl = document.getElementById('subject-select');
        if (subEl) subEl.value = parsed.subject;
      }
      if (parsed.custom_subject) {
        const otherEl = document.getElementById('other-subject-input');
        if (otherEl) otherEl.value = parsed.custom_subject;
      }
      if (typeof parsed.export_pdf === 'boolean') {
        const pdfFmt = document.getElementById('fmt-pdf');
        if (pdfFmt) pdfFmt.checked = parsed.export_pdf;
      }
      if (typeof parsed.export_docx === 'boolean') {
        const docxFmt = document.getElementById('fmt-docx');
        if (docxFmt) docxFmt.checked = parsed.export_docx;
      }
      await runLabPipeline();
      return {
        status: 'completed',
        lab: currentLabData ? {
          filename: currentLabData.filename,
          tasks_count: currentLabData.tasks ? currentLabData.tasks.length : 0,
          quality_gate: currentLabData.validation_report ? currentLabData.validation_report.is_valid : true
        } : null
      };
    }
  });

  // 2. execute_code
  modelContext.registerTool({
    name: 'execute_code',
    description: 'Execute student code (Python 3, C, or SQL) in the local sandbox and return execution stdout/stderr and metrics.',
    inputSchema: {
      type: 'object',
      properties: {
        language: {
          type: 'string',
          enum: ['python', 'c', 'sql'],
          description: 'Programming language.'
        },
        code: {
          type: 'string',
          description: 'Source code or query to execute.'
        },
        stdin: {
          type: 'string',
          description: 'Optional standard input.'
        }
      },
      required: ['language', 'code'],
      additionalProperties: false
    },
    readOnlyHint: false,
    handler: async (args) => {
      const parsed = typeof args === 'string' ? JSON.parse(args) : args;
      const res = await fetch('/api/execute-scratchpad', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          language: parsed.language,
          code: parsed.code,
          stdin: parsed.stdin || ''
        })
      });
      const data = await res.json();
      return {
        exit_code: data.exit_code,
        stdout: data.stdout || '',
        stderr: data.stderr || '',
        execution_time_ms: data.execution_time_ms,
        command: data.command
      };
    }
  });

  // 3. merge_documents
  modelContext.registerTool({
    name: 'merge_documents',
    description: 'Combine multiple PDF or Word documents into a unified output submission.',
    inputSchema: {
      type: 'object',
      properties: {
        use_sample_files: {
          type: 'boolean',
          description: 'Populate merger with sample lab files and execute merge.'
        },
        output_format: {
          type: 'string',
          enum: ['pdf', 'docx'],
          description: 'Output format.'
        },
        output_filename: {
          type: 'string',
          description: 'Output filename.'
        }
      },
      additionalProperties: false
    },
    readOnlyHint: false,
    handler: async (args) => {
      const parsed = typeof args === 'string' ? JSON.parse(args) : args;
      openNavDocTools();
      if (parsed.use_sample_files) {
        await loadSampleMergeFiles();
      }
      if (parsed.output_format) {
        selectExportFormat(parsed.output_format);
      }
      if (parsed.output_filename) {
        const fnInput = document.getElementById('merger-out-filename');
        if (fnInput) fnInput.value = parsed.output_filename;
      }
      await executeDocumentMerge();
      return {
        status: lastMergedResult ? 'merged' : 'error',
        result: lastMergedResult ? {
          filename: lastMergedResult.filename,
          page_count: lastMergedResult.page_count,
          size_bytes: lastMergedResult.size_bytes
        } : null
      };
    }
  });

  // 4. switch_theme
  modelContext.registerTool({
    name: 'switch_theme',
    description: 'Switch application UI theme (dark/light) or screenshot window theme palette.',
    inputSchema: {
      type: 'object',
      properties: {
        ui_theme: {
          type: 'string',
          enum: ['dark', 'light'],
          description: 'Application UI theme mode.'
        },
        screenshot_theme: {
          type: 'string',
          enum: ['modern-dark', 'slate-grey', 'cyber-black', 'paper-warm', 'cobalt-blue'],
          description: 'Terminal screenshot window theme palette.'
        }
      },
      additionalProperties: false
    },
    readOnlyHint: false,
    handler: async (args) => {
      const parsed = typeof args === 'string' ? JSON.parse(args) : args;
      if (parsed.ui_theme) {
        applyAppTheme(parsed.ui_theme, true);
      }
      if (parsed.screenshot_theme) {
        selectThemeFromSwatch(parsed.screenshot_theme);
      }
      return {
        current_ui_theme: document.documentElement.getAttribute('data-theme') || 'dark',
        current_screenshot_theme: document.getElementById('terminal-theme')?.value || 'modern-dark'
      };
    }
  });

  // 5. get_active_session
  modelContext.registerTool({
    name: 'get_active_session',
    description: 'Retrieve current active lab session metadata, task solutions, and document links.',
    inputSchema: {
      type: 'object',
      properties: {},
      additionalProperties: false
    },
    readOnlyHint: true,
    untrustedContentHint: true,
    handler: async () => {
      return {
        has_lab: !!currentLabData,
        lab_title: currentLabData?.manual?.title || null,
        filename: currentLabData?.filename || null,
        tasks_count: currentLabData?.tasks?.length || 0,
        pdf_download_url: currentLabData?.pdf_download_url || null,
        docx_download_url: currentLabData?.download_url || null
      };
    }
  });

  console.info('[WebMCP] Registered 5 first-party LabGenius agent tools successfully.');
}
