/**
 * chart_scales.js - Ticks, math ranges, and palette color ramps for zero-dependency charts.
 */
(function(window) {
  'use strict';

  const AUTHOR_COLORS = {
    'SM': '#7c3aed',
    'ZB': '#16a34a',
    'OK': '#2563eb',
    'DEFAULT': '#64748b'
  };

  const CATEGORICAL_10 = [
    '#2563eb', '#16a34a', '#d97706', '#dc2626', '#7c3aed',
    '#0891b2', '#db2777', '#4b5563', '#ea580c', '#059669'
  ];

  function niceNum(range, round) {
    const exp = Math.floor(Math.log10(range));
    const frac = range / Math.pow(10, exp);
    let nice;
    if (round) {
      if (frac < 1.5) nice = 1;
      else if (frac < 3) nice = 2;
      else if (frac < 7) nice = 5;
      else nice = 10;
    } else {
      if (frac <= 1) nice = 1;
      else if (frac <= 2) nice = 2;
      else if (frac <= 5) nice = 5;
      else nice = 10;
    }
    return nice * Math.pow(10, exp);
  }

  function calculateTicks(minVal, maxVal, maxTicks = 5) {
    if (minVal === maxVal) return [minVal];
    const range = niceNum(maxVal - minVal, false);
    const tickSpacing = niceNum(range / (maxTicks - 1), true);
    const niceMin = Math.floor(minVal / tickSpacing) * tickSpacing;
    const niceMax = Math.ceil(maxVal / tickSpacing) * tickSpacing;
    const ticks = [];
    for (let t = niceMin; t <= niceMax + 0.5 * tickSpacing; t += tickSpacing) {
      ticks.push(Number(t.toFixed(4)));
    }
    return ticks;
  }

  function sampleYlGnBu(t) {
    const clamped = Math.max(0, Math.min(1, t));
    const r = Math.round(255 - clamped * 230);
    const g = Math.round(255 - clamped * 125);
    const b = Math.round(217 + clamped * 30);
    return `rgb(${r}, ${g}, ${b})`;
  }

  function sampleDivergingVlag(t) {
    const clamped = Math.max(-1, Math.min(1, t));
    if (clamped < 0) {
      const f = -clamped;
      return `rgb(${Math.round(240 - f * 80)}, ${Math.round(240 - f * 140)}, ${Math.round(255)})`;
    }
    const f = clamped;
    return `rgb(${Math.round(255)}, ${Math.round(240 - f * 140)}, ${Math.round(240 - f * 80)})`;
  }

  window.ChartScales = {
    AUTHOR_COLORS,
    CATEGORICAL_10,
    calculateTicks,
    sampleYlGnBu,
    sampleDivergingVlag,
    getAuthorColor: (focal) => AUTHOR_COLORS[focal] || AUTHOR_COLORS.DEFAULT
  };
})(window);
