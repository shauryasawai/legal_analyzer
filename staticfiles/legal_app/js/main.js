// Shared utilities for LexAI
const LexAI = {
  getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) return meta.getAttribute('content');
    const cookie = document.cookie.split(';')
      .find(c => c.trim().startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1].trim() : '';
  },

  formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  },

  fileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    return { pdf: '📕', docx: '📘', doc: '📘', txt: '📝' }[ext] || '📄';
  },
};
