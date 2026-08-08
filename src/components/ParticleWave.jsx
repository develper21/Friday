import React, { useEffect, useRef, useState } from 'react';

/**
 * Center particle-wave: a high-detail wave plate (orange -> blue) with a live
 * canvas particle shimmer on top, so the wave is always visibly running.
 * Now reacts to audio levels from Jean Max voice assistant.
 * Note: The original wave.png asset needs to be added to src/assets/ for the full effect.
 * Currently using canvas-only animation as fallback.
 */
export function ParticleWave({ audioLevel = 0, isSpeaking = false }) {
  const canvasRef = useRef(null);
  const [currentAudioLevel, setCurrentAudioLevel] = useState(0);

  // Smooth audio level transitions
  useEffect(() => {
    const targetLevel = isSpeaking ? audioLevel : 0;
    const interval = setInterval(() => {
      setCurrentAudioLevel(prev => {
        const diff = targetLevel - prev;
        return prev + diff * 0.1;
      });
    }, 50);
    return () => clearInterval(interval);
  }, [audioLevel, isSpeaking]);

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

    const stops = [
      { p: 0.0, c: [255, 150, 60] },
      { p: 0.35, c: [255, 110, 40] },
      { p: 0.55, c: [225, 215, 250] },
      { p: 0.78, c: [90, 170, 255] },
      { p: 1.0, c: [40, 110, 245] },
    ];
    const colorAt = (p) => {
      for (let i = 0; i < stops.length - 1; i++) {
        const a = stops[i];
        const b = stops[i + 1];
        if (p >= a.p && p <= b.p) {
          const k = (p - a.p) / (b.p - a.p);
          return [
            Math.round(a.c[0] + (b.c[0] - a.c[0]) * k),
            Math.round(a.c[1] + (b.c[1] - a.c[1]) * k),
            Math.round(a.c[2] + (b.c[2] - a.c[2]) * k),
          ];
        }
      }
      return [255, 255, 255];
    };

    // S-curve matching the wave plate
    const curveY = (x, time) => {
      const p = x / w;
      const swell = Math.sin(p * Math.PI);
      return (
        h * 0.52 -
        Math.sin(p * Math.PI * 1.9 - 0.6 + time * 0.3) * h * 0.26 * swell -
        Math.sin(p * Math.PI * 3.4 + time * 0.45) * h * 0.04 * swell
      );
    };

    const draw = () => {
      t += 0.008;
      ctx.clearRect(0, 0, w, h);
      ctx.globalCompositeOperation = 'lighter';

      const bands = 46;
      const cols = Math.max(180, Math.floor(w / 2));
      
      // Audio reactivity: boost amplitude and speed based on audio level
      const audioBoost = 1 + currentAudioLevel * 2; // Amplify wave when speaking
      const speedBoost = 1 + currentAudioLevel * 0.5; // Speed up slightly when speaking

      for (let b = 0; b < bands; b++) {
        const bandN = b / (bands - 1) - 0.5;
        for (let i = 0; i < cols; i++) {
          const p = i / cols;
          const x = p * w + Math.sin(b * 1.7 + t * 1.2 * speedBoost + i * 0.02) * 4;
          const spread = h * 0.28 * Math.sin(p * Math.PI) * audioBoost;
          const y =
            curveY(x, t * speedBoost) +
            bandN * spread * (0.6 + 0.4 * Math.sin(p * 6 + t * 1.6 * speedBoost + b));
          const edgeFade = Math.pow(Math.sin(p * Math.PI), 0.9);
          const bandFade = 1 - Math.abs(bandN) * 1.6;
          // Increase particle intensity when audio is present
          const baseAlpha = 0.15 + 0.7 * Math.random();
          const audioAlpha = currentAudioLevel > 0.1 ? baseAlpha * (1 + currentAudioLevel) : baseAlpha;
          const a = Math.max(0, edgeFade * bandFade) * audioAlpha;
          if (a <= 0.05) continue;
          const [r, g, bl] = colorAt(p);
          ctx.fillStyle = `rgba(${r},${g},${bl},${a * 0.55})`;
          ctx.fillRect(x, y, a > 0.6 ? 1.8 : 1.1, a > 0.6 ? 1.8 : 1.1);
        }
      }

      ctx.globalCompositeOperation = 'source-over';
      raf = requestAnimationFrame(draw);
    };
    raf = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
    };
  }, []);

  return (
    <div className="relative h-full w-full" aria-hidden="true">
      <canvas ref={canvasRef} className="absolute inset-0 h-full w-full" />
    </div>
  );
}
