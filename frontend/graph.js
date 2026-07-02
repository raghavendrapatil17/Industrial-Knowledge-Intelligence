/* Self-contained force-directed graph on <canvas>. No external libraries (offline-safe). */
(function () {
  const TYPE_COLORS = {
    equipment: "#ff6b35", personnel: "#4cc9f0", regulatory: "#f7508f",
    location: "#7bd88f", material: "#f4c04a", document: "#93a1b3",
  };

  class ForceGraph {
    constructor(canvas, tooltipEl) {
      this.canvas = canvas;
      this.ctx = canvas.getContext("2d");
      this.tooltip = tooltipEl;
      this.nodes = [];
      this.edges = [];
      this.hover = null;
      this.highlight = new Set();
      this.dpr = window.devicePixelRatio || 1;
      this.raf = null;
      this._bind();
      this.resize();
      window.addEventListener("resize", () => this.resize());
    }

    resize() {
      const r = this.canvas.getBoundingClientRect();
      this.W = r.width; this.H = r.height;
      this.canvas.width = r.width * this.dpr;
      this.canvas.height = r.height * this.dpr;
      this.ctx.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
    }

    setData(graph, highlightIds = []) {
      const cx = this.W / 2, cy = this.H / 2;
      const prev = new Map(this.nodes.map((n) => [n.id, n]));
      this.nodes = graph.nodes.map((n, i) => {
        const p = prev.get(n.id);
        const a = (i / Math.max(graph.nodes.length, 1)) * Math.PI * 2;
        return {
          ...n,
          x: p ? p.x : cx + Math.cos(a) * 140 + (Math.random() - 0.5) * 40,
          y: p ? p.y : cy + Math.sin(a) * 140 + (Math.random() - 0.5) * 40,
          vx: 0, vy: 0,
          r: n.kind === "document" ? 7 : 6 + Math.min((n.degree || 1), 8),
        };
      });
      const idx = new Map(this.nodes.map((n) => [n.id, n]));
      this.edges = graph.edges
        .map((e) => ({ s: idx.get(e.source), t: idx.get(e.target), rel: e.rel }))
        .filter((e) => e.s && e.t);
      this.highlight = new Set(highlightIds);
      this.alpha = 1;
      this._run();
    }

    _run() {
      cancelAnimationFrame(this.raf);
      let ticks = 0;
      const step = () => {
        this._physics();
        this._draw();
        ticks++;
        if (ticks < 600 && this.alpha > 0.02) this.raf = requestAnimationFrame(step);
        else this._draw();
      };
      step();
    }

    _physics() {
      const N = this.nodes;
      const cx = this.W / 2, cy = this.H / 2;
      const k = 0.9;
      // repulsion
      for (let i = 0; i < N.length; i++) {
        for (let j = i + 1; j < N.length; j++) {
          const a = N[i], b = N[j];
          let dx = a.x - b.x, dy = a.y - b.y;
          let d2 = dx * dx + dy * dy || 0.01;
          let d = Math.sqrt(d2);
          const rep = (1800 * k) / d2;
          const fx = (dx / d) * rep, fy = (dy / d) * rep;
          a.vx += fx; a.vy += fy; b.vx -= fx; b.vy -= fy;
        }
      }
      // springs
      for (const e of this.edges) {
        let dx = e.t.x - e.s.x, dy = e.t.y - e.s.y;
        let d = Math.sqrt(dx * dx + dy * dy) || 0.01;
        const target = 70;
        const f = ((d - target) / d) * 0.04 * k;
        const fx = dx * f, fy = dy * f;
        e.s.vx += fx; e.s.vy += fy; e.t.vx -= fx; e.t.vy -= fy;
      }
      // centering + integrate
      for (const n of N) {
        n.vx += (cx - n.x) * 0.006;
        n.vy += (cy - n.y) * 0.006;
        n.vx *= 0.82; n.vy *= 0.82;
        if (n !== this.dragging) { n.x += n.vx * this.alpha; n.y += n.vy * this.alpha; }
        n.x = Math.max(n.r + 4, Math.min(this.W - n.r - 4, n.x));
        n.y = Math.max(n.r + 4, Math.min(this.H - n.r - 4, n.y));
      }
      this.alpha *= 0.985;
    }

    _draw() {
      const ctx = this.ctx;
      ctx.clearRect(0, 0, this.W, this.H);
      const hasHi = this.highlight.size > 0;
      // edges
      for (const e of this.edges) {
        const on = !hasHi || (this.highlight.has(e.s.id) && this.highlight.has(e.t.id));
        ctx.strokeStyle = e.rel === "REFERENCES" ? "rgba(255,107,53,"+(on?0.5:0.06)+")"
          : e.rel === "CO_OCCURS" ? "rgba(120,140,170,"+(on?0.18:0.04)+")"
          : "rgba(140,160,190,"+(on?0.32:0.05)+")";
        ctx.lineWidth = e.rel === "REFERENCES" ? 1.6 : 1;
        ctx.beginPath(); ctx.moveTo(e.s.x, e.s.y); ctx.lineTo(e.t.x, e.t.y); ctx.stroke();
      }
      // nodes
      for (const n of this.nodes) {
        const on = !hasHi || this.highlight.has(n.id);
        const col = n.color || TYPE_COLORS[n.type] || "#ccc";
        ctx.globalAlpha = on ? 1 : 0.25;
        if (n.kind === "document") {
          ctx.fillStyle = col;
          this._roundRect(ctx, n.x - n.r, n.y - n.r, n.r * 2, n.r * 2, 3); ctx.fill();
        } else {
          ctx.beginPath(); ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
          ctx.fillStyle = col; ctx.fill();
        }
        if (n === this.hover) { ctx.lineWidth = 2.5; ctx.strokeStyle = "#fff"; ctx.stroke(); }
        // labels for entities / hovered
        if ((on && n.kind !== "document" && n.r >= 8) || n === this.hover) {
          ctx.globalAlpha = on ? 0.95 : 0.3;
          ctx.fillStyle = "#e6edf3";
          ctx.font = "11px Segoe UI, sans-serif";
          ctx.fillText(n.label.length > 22 ? n.label.slice(0, 21) + "…" : n.label, n.x + n.r + 3, n.y + 3);
        }
        ctx.globalAlpha = 1;
      }
    }

    _roundRect(ctx, x, y, w, h, r) {
      ctx.beginPath();
      ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r);
      ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r);
      ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
    }

    _nodeAt(mx, my) {
      for (let i = this.nodes.length - 1; i >= 0; i--) {
        const n = this.nodes[i];
        if ((mx - n.x) ** 2 + (my - n.y) ** 2 <= (n.r + 3) ** 2) return n;
      }
      return null;
    }

    _bind() {
      const c = this.canvas;
      const pos = (ev) => {
        const r = c.getBoundingClientRect();
        return { x: ev.clientX - r.left, y: ev.clientY - r.top };
      };
      c.addEventListener("mousemove", (ev) => {
        const p = pos(ev);
        if (this.dragging) { this.dragging.x = p.x; this.dragging.y = p.y; this.alpha = Math.max(this.alpha, 0.3); this._run(); return; }
        const n = this._nodeAt(p.x, p.y);
        this.hover = n; c.style.cursor = n ? "pointer" : "default";
        if (n) {
          this.tooltip.hidden = false;
          this.tooltip.innerHTML = `<b>${n.label}</b><br>${n.kind === "document" ? n.doc_type : n.type}`;
          this.tooltip.style.left = Math.min(p.x + 12, this.W - 200) + "px";
          this.tooltip.style.top = (p.y + 12) + "px";
        } else { this.tooltip.hidden = true; }
        this._draw();
      });
      c.addEventListener("mousedown", (ev) => { const p = pos(ev); this.dragging = this._nodeAt(p.x, p.y); });
      window.addEventListener("mouseup", () => { this.dragging = null; });
      c.addEventListener("mouseleave", () => { this.tooltip.hidden = true; this.hover = null; this._draw(); });
      c.addEventListener("click", (ev) => {
        const p = pos(ev); const n = this._nodeAt(p.x, p.y);
        if (!n) return;
        if (n.kind === "document" && this.onDocClick) this.onDocClick(n.id);
        else if (n.kind !== "document" && this.onEntityClick) this.onEntityClick(n.id);
      });
    }
  }

  window.ForceGraph = ForceGraph;
  window.TYPE_COLORS = TYPE_COLORS;
})();
