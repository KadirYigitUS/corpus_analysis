/**
 * subtabs.js - Lightweight pill switcher supporting lazy onFirstShow and reactive cache invalidation.
 */
(function(window) {
  'use strict';

  const _registry = new Map();

  function resolveElement(target) {
    if (!target) return null;
    if (typeof target !== 'string') return target;
    return document.getElementById(target) || document.querySelector(target);
  }

  class SubtabController {
    constructor(containerId, options = {}) {
      this.container = resolveElement(containerId);
      if (this.container && _registry.has(this.container)) {
        return _registry.get(this.container);
      }
      this.options = options || {};
      this.callbacks = {};
      this.shownPanes = new Set();
      this.activePaneId = null;
      this.initEvents();
      this.bindAppState();
      if (this.container) {
        _registry.set(this.container, this);
      }
    }

    static init(tabRootSelector, paneMap = {}, options = {}) {
      const ctrl = new SubtabController(tabRootSelector, options);
      if (paneMap && typeof paneMap === 'object') {
        Object.entries(paneMap).forEach(([paneId, fn]) => {
          if (typeof fn === 'function') ctrl.onFirstShow(paneId, fn);
        });
      }
      return ctrl;
    }

    static invalidateAll(tabRootSelector) {
      if (!tabRootSelector) {
        _registry.forEach((ctrl) => ctrl.invalidate());
        return;
      }
      const el = resolveElement(tabRootSelector);
      if (!el) return;
      if (_registry.has(el)) {
        _registry.get(el).invalidate();
        return;
      }
      _registry.forEach((ctrl, containerEl) => {
        if (el.contains(containerEl) || containerEl.contains(el)) {
          ctrl.invalidate();
        }
      });
    }

    initEvents() {
      if (!this.container) return;
      const buttons = this.container.querySelectorAll('.viz-subtab-btn');
      buttons.forEach(btn => {
        if (btn.classList.contains('active')) {
          this.activePaneId = btn.getAttribute('data-pane');
        }
        btn.addEventListener('click', () => {
          const targetPaneId = btn.getAttribute('data-pane');
          this.activate(targetPaneId);
        });
      });
    }

    bindAppState() {
      if (!window.appState || this.options.autoInvalidate === false) return;
      const onGlobalChange = () => this.invalidate();
      window.appState.on('scopeChanged', onGlobalChange);
      window.appState.on('viewParamsChanged', onGlobalChange);
    }

    invalidate() {
      if (!this.container) return;
      const parent = this.container.parentElement || document;
      parent.querySelectorAll('.viz-pane [data-loaded], .viz-pane[data-loaded]').forEach(el => {
        delete el.dataset.loaded;
        if (el.querySelector('.chart-card')) {
          el.innerHTML = '';
        }
      });
      this.shownPanes.clear();

      if (this.activePaneId && typeof this.callbacks[this.activePaneId] === 'function') {
        const activePane = document.getElementById(this.activePaneId);
        if (activePane && activePane.classList.contains('active')) {
          this.shownPanes.add(this.activePaneId);
          this.callbacks[this.activePaneId]();
        }
      }
    }

    onFirstShow(paneId, callback) {
      this.callbacks[paneId] = callback;
      const paneEl = document.getElementById(paneId);
      if (this.shownPanes.has(paneId) || (paneEl && paneEl.classList.contains('active'))) {
        this.shownPanes.add(paneId);
        this.activePaneId = paneId;
        callback();
      }
    }

    activate(paneId) {
      if (!this.container) return;
      const parent = this.container.parentElement;
      if (!parent) return;
      this.activePaneId = paneId;

      this.container.querySelectorAll('.viz-subtab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-pane') === paneId);
      });

      parent.querySelectorAll('.viz-pane').forEach(pane => {
        pane.classList.toggle('active', pane.id === paneId);
      });

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

