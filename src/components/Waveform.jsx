import React, { useEffect, useRef } from 'react';

/**
 * Bottom audio waveform: symmetric bars, purple -> blue, always animating.
 * Later this can accept real analyser data via a `levels` prop.
 */
export function Waveform({ bars = 96 }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let raf = 0;
    let t = 0;
    let w = 0;
    let h = 0;

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const rect = canvas.getBoundingClientRect();
      w = rect.width;
      h = rect.height;
      canvas.width = Math.max(1, Math.floor(w * dpr));
      canvas.height = Math.max(1, Math.floor(h * dpr));
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);

    const seeds = Array.from({ length: bars }, (_, i) => ({
      f1: 0.9 + (i % 7) * 0.31,
      f2: 1.7 + (i % 5) * 0.47,
      ph: i * 0.61,
    }));

    const draw = () => {
      t += 0.035;
      ctx.clearRect(0, 0, w, h);
      const mid = h / 2;
      const gap = w / bars;
      const barW = Math.max(1.5, gap * 0.34);

      for (let i = 0; i < bars; i++) {
        const p = i / (bars - 1);
        const x = i * gap + gap / 2;
        const env = Math.pow(Math.sin(p * Math.PI), 2.2); // quiet at edges
        const s = seeds[i] ?? { f1: 1, f2: 2, ph: 0 };
        const osc =
          0.5 +
          0.5 *
            (Math.sin(t * s.f1 + s.ph) * 0.6 +
              Math.sin(t * s.f2 - s.ph * 0.7) * 0.4);
        const spike = Math.pow(Math.abs(Math.sin(p * 11 + t * 0.7)), 6) * 0.5;
        const amp = Math.max(0.02, env * (osc * 0.75 + spike)) * (h * 0.46);

        // purple (left) -> blue (right)
        const r = Math.round(168 + (56 - 168) * p);
        const g = Math.round(72 + (150 - 72) * p);
        const b = Math.round(245 + (255 - 245) * p);

        ctx.fillStyle = `rgba(${r},${g},${b},0.95)`;
        ctx.shadowBlur = 12;
        ctx.shadowColor = `rgba(${r},${g},${b},0.85)`;
        const radius = barW / 2;
        const y = mid - amp;
        const hh = amp * 2;
        ctx.beginPath();
        if (typeof ctx.roundRect === 'function') {
          ctx.roundRect(x - barW / 2, y, barW, hh, radius);
        } else {
          ctx.rect(x - barW / 2, y, barW, hh);
        }
        ctx.fill();
      }
      ctx.shadowBlur = 0;
      raf = requestAnimationFrame(draw);
    };
    raf = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
    };
  }, [bars]);

  return <canvas ref={canvasRef} className="h-full w-full" aria-hidden="true" />;
}
