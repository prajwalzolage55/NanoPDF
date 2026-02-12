/* static/js/main.js
   Minimal, safe UI logic for PDF Compressor
   - Works with <input id="fileInput" name="file" ...>
   - No automatic .click() (prevents double file dialog)
   - Validates file type & max size (10 MB)
   - Shows filename and size
   - Disables submit button and shows tiny processing indicator on submit
*/

/* -------- Config -------- */
const MAX_FILE_BYTES = 100 * 1024 * 1024; // 10 MB
const ALLOWED_EXT = ['pdf'];

/* -------- Helpers -------- */
function bytesToKB(bytes) {
  return (bytes / 1024).toFixed(2);
}
function bytesToMB(bytes) {
  return (bytes / (1024*1024)).toFixed(2);
}
function getFileExtension(name) {
  const idx = name.lastIndexOf('.');
  return idx === -1 ? '' : name.slice(idx + 1).toLowerCase();
}
function createAlert(message, type = 'danger', timeout = 6000) {
  const container = document.querySelector('.container.py-5') || document.body;
  const alert = document.createElement('div');
  alert.className = `alert alert-${type} alert-dismissible fade show`;
  alert.setAttribute('role', 'alert');
  alert.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
  `;
  container.insertBefore(alert, container.firstChild);
  if (timeout > 0) setTimeout(() => { try { alert.remove(); } catch (e) {} }, timeout);
  return alert;
}

/* -------- Elements -------- */
const fileInput = document.getElementById('fileInput') || document.querySelector('input[name="file"]');
if (!fileInput) {
  console.warn('main.js: file input (#fileInput or name="file") not found.');
}
const form = fileInput ? fileInput.form : document.querySelector('form');
const submitButton = form ? form.querySelector('button[type="submit"]') : null;

/* create file-info area under the file input if not present */
let fileInfo = document.querySelector('.file-info');
if (!fileInfo && fileInput) {
  fileInfo = document.createElement('div');
  fileInfo.className = 'file-info';
  fileInfo.style.marginTop = '0.6rem';
  fileInput.parentNode.insertBefore(fileInfo, fileInput.nextSibling);
}

/* processing indicator (small text) */
let processingSpan = document.createElement('span');
processingSpan.className = 'processing-note';
processingSpan.style.display = 'none';
processingSpan.style.marginLeft = '8px';
processingSpan.style.fontSize = '0.92rem';
processingSpan.style.color = 'rgba(255,255,255,0.85)';
processingSpan.textContent = 'Processing...';
if (fileInfo) fileInfo.appendChild(processingSpan);

/* -------- Core functions -------- */
function showFileInfo(name, sizeBytes) {
  if (!fileInfo) return;
  fileInfo.innerHTML = `
    <span class="badge">${name}</span>
    <span class="badge">${bytesToMB(sizeBytes)} MB</span>
  `;
  fileInfo.appendChild(processingSpan);
  processingSpan.style.display = 'none';
}

function clearFileInfo() {
  if (!fileInfo) return;
  fileInfo.innerHTML = '';
  processingSpan.style.display = 'none';
}

function setProcessingState(on = true) {
  if (submitButton) {
    submitButton.disabled = on;
    submitButton.setAttribute('aria-busy', on ? 'true' : 'false');
  }
  if (processingSpan) {
    processingSpan.style.display = on ? 'inline-block' : 'none';
  }
}

/* -------- Validation -------- */
function validateFileCandidate(file) {
  if (!file) return { ok: false, msg: 'No file selected.' };
  const ext = getFileExtension(file.name);
  if (!ALLOWED_EXT.includes(ext)) {
    return { ok: false, msg: 'Only PDF files are allowed. Please select a .pdf file.' };
  }
  if (file.size > MAX_FILE_BYTES) {
    return {
      ok: false,
      msg: `File too large: ${bytesToMB(file.size)} MB. Maximum allowed is ${bytesToMB(MAX_FILE_BYTES)} MB.`
    };
  }
  return { ok: true };
}

/* -------- Event handlers -------- */
if (fileInput) {
  fileInput.addEventListener('change', (e) => {
    const f = e.target.files && e.target.files[0];
    if (!f) {
      clearFileInfo();
      return;
    }
    const check = validateFileCandidate(f);
    if (!check.ok) {
      createAlert(check.msg, 'danger', 7000);
      fileInput.value = '';
      clearFileInfo();
      return;
    }
    showFileInfo(f.name, f.size);
  }, false);
}

if (form) {
  form.addEventListener('submit', (e) => {
    const f = fileInput && fileInput.files && fileInput.files[0];
    const check = validateFileCandidate(f);
    if (!check.ok) {
      e.preventDefault();
      createAlert(check.msg, 'danger', 7000);
      return;
    }
    // All good — enable processing UI and allow normal submit
    setProcessingState(true);
    // Note: don't preventDefault; let server handle the upload
  }, false);
}

/* Re-enable button if page becomes visible again (in case of navigation back) */
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible') {
    setProcessingState(false);
  }
});

/* Small fallback: clear processing state after a long time (safety) */
setTimeout(() => setProcessingState(false), 30 * 1000); // 30s safety fallback

/* End of main.js */
