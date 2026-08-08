import React, { useEffect, useState } from 'react';
import { Clock, Calendar } from 'lucide-react';

export function TimeDateCard() {
  const [time, setTime] = useState('');
  const [date, setDate] = useState('');
  const [day, setDay] = useState('');

  useEffect(() => {
    const updateDateTime = () => {
      const now = new Date();
      
      // Format time (HH:MM:SS)
      const hours = now.getHours().toString().padStart(2, '0');
      const minutes = now.getMinutes().toString().padStart(2, '0');
      const seconds = now.getSeconds().toString().padStart(2, '0');
      setTime(`${hours}:${minutes}:${seconds}`);
      
      // Format date (DD MMMM YYYY)
      const dayOfMonth = now.getDate();
      const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
                          'July', 'August', 'September', 'October', 'November', 'December'];
      const month = monthNames[now.getMonth()];
      const year = now.getFullYear();
      setDate(`${dayOfMonth} ${month} ${year}`);
      
      // Format day
      const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
      setDay(dayNames[now.getDay()]);
    };

    updateDateTime();
    const interval = setInterval(updateDateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <section className="glass-card w-[288px] p-7">
      <div className="flex items-center gap-3">
        <Clock className="h-6 w-6 text-accent-blue" />
        <h2 className="text-2xl font-semibold text-foreground">Time</h2>
      </div>

      <div className="mt-6">
        <div className="text-[56px] font-semibold leading-none tracking-tight text-foreground">
          {time}
        </div>
      </div>

      <div className="glass-divider mt-6" />

      <div className="mt-5 flex items-center gap-3 text-lg font-medium text-foreground">
        <Calendar className="h-5 w-5 shrink-0 text-muted-foreground" />
        <span>{day}</span>
      </div>

      <div className="glass-divider mt-5" />

      <div className="mt-5 text-[17px] text-muted-foreground">
        {date}
      </div>
    </section>
  );
}
