import React from 'react';
import { Menu, Minus, Square, X } from 'lucide-react';

/**
 * Electron-friendly title bar. In Electron set the BrowserWindow to
 * `titleBarStyle: 'hidden'` + `frame: false`; the drag region is handled by
 * the `app-drag` / `app-no-drag` classes.
 */
export function TitleBar({ onMinimize, onMaximize, onClose, onMenu }) {
  return (
    <header className="app-drag grid grid-cols-[minmax(0,1fr)_auto] items-start gap-4 px-8 pt-7">
      <div className="flex min-w-0 items-start gap-6">
        <div className="min-w-0">
          <h1 className="truncate text-[26px] font-semibold leading-tight text-foreground">
            JeanMax
          </h1>
          <p className="mt-0.5 text-[13px] font-medium tracking-[0.14em] text-muted-foreground">
            V 1.0.0
          </p>
        </div>
      </div>
    </header>
  );
}
