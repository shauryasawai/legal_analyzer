// Upload page logic
(function () {
  const dropZone   = document.getElementById('dropZone');
  const fileInput  = document.getElementById('fileInput');
  const filePreview = document.getElementById('filePreview');
  const fileIcon   = document.getElementById('fileIcon');
  const fileName   = document.getElementById('fileName');
  const fileSize   = document.getElementById('fileSize');
  const clearBtn   = document.getElementById('clearFile');
  const analyzeBtn = document.getElementById('analyzeBtn');
  const processing = document.getElementById('processingState');
  const procTitle  = document.getElementById('processingTitle');
  const progressFill = document.getElementById('progressFill');
  const errorState = document.getElementById('errorState');
  const errorMsg   = document.getElementById('errorMsg');
  const retryBtn   = document.getElementById('retryBtn');

  let selectedFile = null;

  // ── Drag & drop ──────────────────────────────────────────────
  ['dragenter', 'dragover'].forEach(evt => {
    dropZone.addEventListener(evt, e => {
      e.preventDefault();
      dropZone.classList.add('drag-over');
    });
  });
  ['dragleave', 'drop'].forEach(evt => {
    dropZone.addEventListener(evt, () => dropZone.classList.remove('drag-over'));
  });
  dropZone.addEventListener('drop', e => {
    e.preventDefault();
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  });
  dropZone.addEventListener('click', () => fileInput.click());
  fileInput.addEventListener('change', () => {
    if (fileInput.files[0]) handleFile(fileInput.files[0]);
  });

  // ── File selection ────────────────────────────────────────────
  function handleFile(file) {
    const allowed = ['.pdf', '.docx', '.doc', '.txt'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!allowed.includes(ext)) {
      showError('Unsupported file type. Please upload PDF, DOCX, or TXT.');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      showError('File too large. Maximum size is 10 MB.');
      return;
    }
    selectedFile = file;
    fileIcon.textContent = LexAI.fileIcon(file.name);
    fileName.textContent = file.name;
    fileSize.textContent = LexAI.formatFileSize(file.size);

    dropZone.classList.add('hidden');
    filePreview.classList.remove('hidden');
    errorState.classList.add('hidden');
  }

  clearBtn.addEventListener('click', () => {
    selectedFile = null;
    fileInput.value = '';
    filePreview.classList.add('hidden');
    dropZone.classList.remove('hidden');
  });

  retryBtn.addEventListener('click', () => {
    errorState.classList.add('hidden');
    filePreview.classList.remove('hidden');
  });

  // ── Analyze ───────────────────────────────────────────────────
  analyzeBtn.addEventListener('click', uploadAndAnalyze);

  function showError(msg) {
    errorMsg.textContent = msg;
    processing.classList.add('hidden');
    filePreview.classList.add('hidden');
    dropZone.classList.add('hidden');
    errorState.classList.remove('hidden');
  }

  function setProgress(pct) {
    progressFill.style.width = pct + '%';
  }

  const stages = [
    [10, 'Uploading document…'],
    [30, 'Extracting text with LangChain…'],
    [55, 'Building vector embeddings…'],
    [75, 'Analyzing clauses with Claude AI…'],
    [90, 'Scoring risks and simplifying…'],
  ];
  let stageIndex = 0;
  let stageTimer = null;

  function startProgressSimulation() {
    stageIndex = 0;
    setProgress(5);
    stageTimer = setInterval(() => {
      if (stageIndex < stages.length) {
        const [pct, label] = stages[stageIndex++];
        setProgress(pct);
        procTitle.textContent = label;
      } else {
        clearInterval(stageTimer);
      }
    }, 2000);
  }

  async function uploadAndAnalyze() {
    if (!selectedFile) return;

    filePreview.classList.add('hidden');
    processing.classList.remove('hidden');
    startProgressSimulation();

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const resp = await fetch('/upload/', {
        method: 'POST',
        headers: { 'X-CSRFToken': LexAI.getCsrfToken() },
        body: formData,
      });
      const data = await resp.json();

      clearInterval(stageTimer);

      if (data.success) {
        setProgress(100);
        procTitle.textContent = 'Analysis complete! Redirecting…';
        setTimeout(() => { window.location.href = data.redirect; }, 800);
      } else {
        showError(data.error || 'Analysis failed. Please try again.');
      }
    } catch (err) {
      clearInterval(stageTimer);
      showError('Network error. Please check your connection and try again.');
    }
  }
})();
