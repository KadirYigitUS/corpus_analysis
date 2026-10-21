/**
 * Global App State Machine and Event Bus for Corpus Analysis SPA.
 */
class AppStateManager {
  constructor() {
    this.state = {
      lang: 'tr',
      scope: {
        scope: 'all',
        author_filter: null,
        text_code: null,
        pair_code: 'IR-IA_BR-SM'
      },
      view_params: {
        field: 'tok',
        filter_function_words: false,
        mode: 'drop',
        punct: 'drop'
      },
      activeTab: 'tab_01',
      telemetry: {
        rss_mb: 0,
        cache_info: {}
      }
    };
    this.listeners = {};
    this.i18nCatalog = {};
  }

  on(event, callback) {
    if (!this.listeners[event]) this.listeners[event] = [];
    this.listeners[event].push(callback);
  }

  emit(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(fn => fn(data));
    }
  }

  setState(partial) {
    Object.assign(this.state, partial);
    this.emit('stateChanged', this.state);
  }

  setScope(scopeUpdate) {
    Object.assign(this.state.scope, scopeUpdate);
    this.emit('scopeChanged', this.state.scope);
  }

  setViewParams(paramsUpdate) {
    Object.assign(this.state.view_params, paramsUpdate);
    this.emit('viewParamsChanged', this.state.view_params);
  }

  async loadI18n(lang) {
    try {
      const resp = await fetch(`/static/i18n/${lang}.json`);
      if (resp.ok) {
        this.i18nCatalog = await resp.json();
        this.state.lang = lang;
        this.emit('langChanged', { lang, catalog: this.i18nCatalog });
      }
    } catch (err) {
      console.error('Failed to load i18n catalog:', err);
    }
  }

  t(keyPath) {
    const keys = keyPath.split('.');
    let cur = this.i18nCatalog;
    for (const k of keys) {
      if (!cur || cur[k] === undefined) return keyPath;
      cur = cur[k];
    }
    return cur;
  }

  async refreshTelemetry() {
    try {
      const resp = await fetch('/api/v1/corpus/telemetry');
      if (resp.ok) {
        const data = await resp.json();
        this.state.telemetry = data;
        this.emit('telemetryUpdated', data);
      }
    } catch (err) {
      console.warn('Telemetry polling error:', err);
    }
  }
}

window.appState = new AppStateManager();
