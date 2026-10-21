/**
 * Tab 2 Chart & Token Annotation Helper (ported from length_view.py).
 */
class Tab02ChartAndTokens {
  constructor(canvasId, titleId, tipId) {
    this.canvasId = canvasId;
    this.titleId = titleId;
    this.tipId = tipId;
    this.series = [];
    this.chapterSummary = [];
    this.onPointClick = null;
  }

  drawChart(series, chapterSummary, scopeLabel) {
    this.series = series || [];
    this.chapterSummary = chapterSummary || [];
    const canvas = document.getElementById(this.canvasId);
    const titleEl = document.getElementById(this.titleId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.width;
    const H = canvas.height;
    const PAD = { top: 24, right: 18, bottom: 34, left: 46 };
    const PW = W - PAD.left - PAD.right;
    const PH = H - PAD.top - PAD.bottom;

    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, W, H);

    if (!this.series.length) {
      if (titleEl) titleEl.textContent = 'No alignment data available';
      return;
    }

    const aiMin = this.series[0].ai;
    const aiMax = this.series[this.series.length - 1].ai;
    const aiSpan = Math.max(1, aiMax - aiMin);
    let absMax = 1;
    for (let i = 0; i < this.series.length; i++) {
      const a = Math.abs(this.series[i].sd);
      if (a > absMax) absMax = a;
    }

    const toX = (ai) => PAD.left + ((ai - aiMin) / aiSpan) * PW;
    const toY = (sd) => PAD.top + PH / 2 - (sd / absMax) * (PH / 2 - 4);

    // Horizontal dashed integer grid lines
    ctx.strokeStyle = '#e9ecef';
    ctx.lineWidth = 1;
    for (let v = -absMax; v <= absMax; v++) {
      if (v === 0) continue;
      ctx.setLineDash([3, 3]);
      ctx.beginPath();
      ctx.moveTo(PAD.left, toY(v));
      ctx.lineTo(PAD.left + PW, toY(v));
      ctx.stroke();
    }
    ctx.setLineDash([]);

    // Whole-book chapter boundary markers
    if (this.chapterSummary.length > 1 && scopeLabel && scopeLabel.includes('Whole Book')) {
      ctx.strokeStyle = 'rgba(100,116,139,0.28)';
      ctx.fillStyle = '#64748b';
      ctx.font = '9.5px system-ui';
      ctx.textAlign = 'left';
      this.chapterSummary.forEach((c, idx) => {
        if (idx > 0 && c.ai_min >= aiMin && c.ai_min <= aiMax) {
          const cx = toX(c.ai_min);
          ctx.beginPath();
          ctx.moveTo(cx, PAD.top);
          ctx.lineTo(cx, PAD.top + PH);
          ctx.stroke();
          ctx.fillText(`Ch.${c.ch}`, cx + 2, PAD.top + 10);
        }
      });
    }

    // Zero baseline
    ctx.strokeStyle = '#adb5bd';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(PAD.left, toY(0));
    ctx.lineTo(PAD.left + PW, toY(0));
    ctx.stroke();

    // Per-row shaded bars (blue for TUR > ENG, red for ENG > TUR)
    const barW = this.series.length > 1500 ? 1.5 : 2.5;
    for (let i = 0; i < this.series.length; i++) {
      const r = this.series[i];
      if (r.sd === 0) continue;
      const x = toX(r.ai);
      const y0 = toY(0);
      const y1 = toY(r.sd);
      ctx.fillStyle = r.sd > 0 ? 'rgba(13,110,253,0.24)' : 'rgba(220,53,69,0.24)';
      ctx.fillRect(x - barW / 2, Math.min(y0, y1), barW, Math.max(1, Math.abs(y1 - y0)));
    }

    // Main polyline (decimated cleanly when >2000 rows so extremes remain crisp)
    ctx.strokeStyle = '#2F5496';
    ctx.lineWidth = this.series.length > 2000 ? 1.0 : 1.5;
    ctx.beginPath();
    const step = Math.max(1, Math.floor(this.series.length / 1200));
    for (let i = 0; i < this.series.length; i += step) {
      const r = this.series[i];
      if (i === 0) ctx.moveTo(toX(r.ai), toY(r.sd));
      else ctx.lineTo(toX(r.ai), toY(r.sd));
    }
    ctx.stroke();

    // X-axis tick labels
    ctx.fillStyle = '#495057';
    ctx.font = '10px system-ui';
    ctx.textAlign = 'center';
    const xStep = aiSpan <= 100 ? 10 : aiSpan <= 500 ? 50 : aiSpan <= 2000 ? 200 : 500;
    const firstTick = Math.ceil(aiMin / xStep) * xStep;
    for (let x = firstTick; x <= aiMax; x += xStep) {
      ctx.fillText(String(x), toX(x), H - PAD.bottom + 13);
    }

    // Y-axis integer tick labels
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    for (let v = -absMax; v <= absMax; v++) {
      ctx.fillStyle = v === 0 ? '#212529' : '#868e96';
      ctx.fillText(String(v), PAD.left - 5, toY(v));
    }

    // Axis titles
    ctx.save();
    ctx.translate(12, PAD.top + PH / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.textAlign = 'center';
    ctx.fillStyle = '#495057';
    ctx.fillText('sent_diff (TR−EN)', 0, 0);
    ctx.restore();
    ctx.textAlign = 'center';
    ctx.fillStyle = '#495057';
    ctx.fillText('Alignment Index (AI)', PAD.left + PW / 2, H - 4);

    if (titleEl) {
      titleEl.textContent = `Cümle Sayısı Farkı — ${scopeLabel} (sent_diff = TUR − ENG, AI ${aiMin}–${aiMax}, N=${this.series.length})`;
    }
  }

  static renderCellHtml(sents, rawText) {
    if (!sents || !sents.length) {
      return (rawText || '—').replace(/</g, '&lt;');
    }
    const sep = ' <span class="sent-sep">|</span> ';
    const rendered = sents.map((sent) => {
      if (!sent || !sent.length) return '';
      return sent.map((a) => {
        const ner = a.n && a.n !== 'O' ? `ner-${a.n}` : '';
        const cls = ['tok', ner].filter(Boolean).join(' ');
        const t = String(a.t || '').replace(/</g, '&lt;').replace(/"/g, '&quot;');
        const p = String(a.p || '').replace(/"/g, '&quot;');
        const n = String(a.n || 'O').replace(/"/g, '&quot;');
        const l = String(a.l || '').replace(/"/g, '&quot;');
        const m = String(a.m || '').replace(/"/g, '&quot;');
        const d = String(a.d || '').replace(/"/g, '&quot;');
        return `<span class="${cls}" data-pos="${p}" data-ner="${n}" data-lemma="${l}" data-morph="${m}" data-dep="${d}">${t}</span>`;
      }).join(' ');
    }).filter((s) => s.length > 0);
    return rendered.length <= 1 ? (rendered[0] || '') : rendered.join(sep);
  }

  attachTooltip(containerId) {
    const container = document.getElementById(containerId);
    const tip = document.getElementById(this.tipId);
    if (!container || !tip) return;
    container.addEventListener('mouseover', (e) => {
      const span = e.target.closest('.tok');
      if (!span) return;
      const ds = span.dataset;
      const lines = [`<b>${span.textContent}</b>`];
      if (ds.pos) lines.push(`POS: ${ds.pos}`);
      if (ds.ner && ds.ner !== 'O') lines.push(`<span class="tip-ner">NER: ${ds.ner}</span>`);
      if (ds.dep) lines.push(`<span class="tip-dep">dep: ${ds.dep}</span>`);
      if (ds.lemma) lines.push(`<span class="tip-lemma">lemma: ${ds.lemma}</span>`);
      if (ds.morph) lines.push(`<span class="tip-morph">${ds.morph}</span>`);
      tip.innerHTML = lines.join('<br>');
      tip.style.display = 'block';
    });
    container.addEventListener('mousemove', (e) => {
      tip.style.left = `${e.clientX + 14}px`;
      tip.style.top = `${e.clientY + 14}px`;
    });
    container.addEventListener('mouseout', (e) => {
      if (!e.relatedTarget || !e.relatedTarget.closest('.tok')) {
        tip.style.display = 'none';
      }
    });
  }
}

window.Tab02ChartAndTokens = Tab02ChartAndTokens;
