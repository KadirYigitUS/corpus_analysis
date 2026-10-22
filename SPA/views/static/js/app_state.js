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

  buildQueryParams(extra = {}) {
    const params = new URLSearchParams();
    const sc = this.state.scope || {};
    const vp = this.state.view_params || {};

    if (sc.scope) {
      params.set('category', sc.scope);
      params.set('scope', sc.scope);
    }
    if (sc.author_filter) params.set('author_filter', sc.author_filter);
    if (sc.pair_code) params.set('pair_code', sc.pair_code);
    if (sc.text_code) params.set('text_code', sc.text_code);

    if (vp.field) params.set('field', vp.field);
    if (vp.filter_function_words !== undefined) {
      params.set('filter_function_words', String(Boolean(vp.filter_function_words)));
    }
    if (vp.mode) params.set('mode', vp.mode);
    if (vp.punct) params.set('punct', vp.punct);

    Object.entries(extra || {}).forEach(([k, v]) => {
      if (v !== undefined && v !== null) params.set(k, String(v));
    });
    return params;
  }

  buildRequestPayload(extra = {}) {
    return Object.assign(
      {
        scope: Object.assign({}, this.state.scope),
        view_params: Object.assign({}, this.state.view_params)
      },
      extra || {}
    );
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
