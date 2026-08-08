import React from 'react';
import { Radio, Smartphone } from 'lucide-react';

const fallback = {
  deviceName: "MJ's Mobile",
  model: 'iPhone 14',
  connected: true,
};

export function MobileCard({ data = fallback, onLiveLocation }) {
  return (
    <section className="glass-card w-[288px] p-7">
      <Smartphone className="h-11 w-11 text-accent-purple" strokeWidth={1.5} />

      <h2 className="mt-6 text-2xl font-semibold text-foreground">Mobile</h2>

      <p className="mt-4 text-lg font-medium text-foreground">{data.deviceName}</p>
      <p className="mt-1 text-[15px] text-muted-foreground">{data.model}</p>

      <p className="mt-3 flex items-center gap-2 text-[15px]">
        <span
          className={
            data.connected
              ? 'h-2 w-2 shrink-0 rounded-full bg-accent-green shadow-[0_0_8px_var(--accent-green)]'
              : 'h-2 w-2 shrink-0 rounded-full bg-muted-foreground'
          }
        />
        <span className={data.connected ? 'text-accent-green' : 'text-muted-foreground'}>
          {data.connected ? 'Connected' : 'Disconnected'}
        </span>
      </p>

      <div className="glass-divider mt-6" />

      <button
        type="button"
        onClick={onLiveLocation}
        className="glass-button mt-6 flex w-full items-center justify-center gap-3 px-4 py-4 text-[15px] text-accent-purple"
      >
        <Radio className="h-[18px] w-[18px] shrink-0" />
        Live Location
      </button>
    </section>
  );
}
