/**
 * viz_api.js - Async JSON fetch wrapper with abort controller and error toasts.
 */
(function(window) {
  'use strict';

  async function fetchJSON(url, options = {}) {
    const defaultHeaders = { 'Content-Type': 'application/json' };
    const config = Object.assign({ headers: defaultHeaders }, options);

    try {
      const resp = await fetch(url, config);
      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}: ${resp.statusText}`);
      }
      return await resp.json();
    } catch (err) {
      console.error(`[VizAPI] Request failed for ${url}:`, err);
      showErrorToast(err.message || 'API request failed');
      throw err;
    }
  }

  function showErrorToast(msg) {
    let toast = document.getElementById('viz-api-toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'viz-api-toast';
      toast.style.cssText = 'position:fixed;bottom:20px;right:20px;background:#ef4444;color:#fff;padding:8px 14px;border-radius:4px;font-size:12px;z-index:9999;box-shadow:0 4px 6px rgba(0,0,0,0.2);display:none;';
      document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.style.display = 'block';
    setTimeout(() => { toast.style.display = 'none'; }, 4000);
  }

  window.VizAPI = {
    getJSON: (url) => fetchJSON(url, { method: 'GET' }),
    postJSON: (url, body) => fetchJSON(url, { method: 'POST', body: JSON.stringify(body) })
  };
})(window);
