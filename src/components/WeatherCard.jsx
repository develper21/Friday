import React from 'react';
import { Droplets, MapPin, Wind } from 'lucide-react';

const fallback = {
  temperatureC: 28,
  condition: 'Partly Cloudy',
  location: 'Ahmedabad, IN',
  humidityPercent: 60,
  windKph: 12,
};

export function WeatherCard({ data = fallback }) {
  return (
    <section className="glass-card w-[288px] p-7">
      <svg viewBox="0 0 64 48" className="h-11 w-14" aria-hidden="true">
        <circle cx="22" cy="17" r="10" fill="#FFC53D" />
        <circle cx="22" cy="17" r="14" fill="#FFC53D" opacity="0.25" />
        <path
          d="M20 44a11 11 0 0 1 .9-21.9A14 14 0 0 1 47 26.5a9 9 0 0 1-1.5 17.5H20.Z"
          fill="#E6EDF7"
        />
        <path
          d="M20 44a11 11 0 0 1 .9-21.9c1.6 0 3.1.3 4.5.9A12 12 0 0 0 18 34c0 3.8 1.7 7.3 4.4 10H20.Z"
          fill="#C7D3E4"
        />
      </svg>

      <h2 className="mt-6 text-2xl font-semibold text-foreground">Weather</h2>

      <div className="mt-4 flex items-start">
        <span className="text-[64px] font-semibold leading-none tracking-tight text-foreground">
          {data.temperatureC}
        </span>
        <span className="mt-1 text-[34px] leading-none text-foreground">°</span>
        <span className="mt-3 ml-1 text-[30px] leading-none font-medium text-accent-blue">
          c
        </span>
      </div>

      <p className="mt-4 text-lg font-medium text-foreground">{data.condition}</p>
      <p className="mt-2 flex items-center gap-2 text-sm text-muted-foreground">
        <MapPin className="h-4 w-4 shrink-0" />
        <span className="truncate">{data.location}</span>
      </p>

      <div className="glass-divider mt-6" />

      <div className="mt-5 flex items-center justify-between text-[15px]">
        <span className="flex items-center gap-3 text-foreground">
          <Droplets className="h-[18px] w-[18px] shrink-0 text-muted-foreground" />
          Humidity
        </span>
        <span className="text-muted-foreground">{data.humidityPercent}%</span>
      </div>

      <div className="glass-divider mt-5" />

      <div className="mt-5 flex items-center justify-between text-[15px]">
        <span className="flex items-center gap-3 text-foreground">
          <Wind className="h-[18px] w-[18px] shrink-0 text-muted-foreground" />
          Wind
        </span>
        <span className="text-muted-foreground">{data.windKph} km/h</span>
      </div>
    </section>
  );
}
