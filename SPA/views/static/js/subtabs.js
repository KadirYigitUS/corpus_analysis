/**
 * subtabs.js - Lightweight pill switcher supporting lazy onFirstShow callbacks.
 */
(function(window) {
  'use strict';

  class SubtabController {
    constructor(containerId, options = {}) {
      this.container = typeof containerId === 'string' ? document.getElementById(containerId) : containerId;
      this.options = options;
      this.callbacks = {};
      this.shownPanes = new Set();
      this.initEvents();
    }

    initEvents() {
      if (!this.container) return;
      const buttons = this.container.querySelectorAll('.viz-subtab-btn');
      buttons.forEach(btn => {
        btn.addEventListener('click', () => {
          const targetPaneId = btn.getAttribute('data-pane');
          this.activate(targetPaneId);
        });
      });
    }

    onFirstShow(paneId, callback) {
      this.callbacks[paneId] = callback;
      if (this.shownPanes.has(paneId)) {
        callback();
      }
    }

    activate(paneId) {
      if (!this.container) return;
      const parent = this.container.parentElement;
      if (!parent) return;

      // Update buttons
      this.container.querySelectorAll('.viz-subtab-btn').forEach(btn => {
        if (btn.getAttribute('data-pane') === paneId) {
          btn.classList.add('active');
        } else {
          btn.classList.remove('active');
        }
      });

      // Update panes
      parent.querySelectorAll('.viz-pane').forEach(pane => {
        if (pane.id === paneId) {
          pane.classList.add('active');
        } else {
          pane.classList.remove('active');
        }
      });

      // Trigger callback on first view
      if (!this.shownPanes.has(paneId)) {
        this.shownPanes.add(paneId);
        if (typeof this.callbacks[paneId] === 'function') {
          this.callbacks[paneId]();
        }
      }
    }
  }

  window.SubtabController = SubtabController;
})(window);
