'use client';

import { useEffect, useState } from 'react';

interface CountdownProps {
  seconds: number;
}

export function Countdown({ seconds }: CountdownProps) {
  const [time, setTime] = useState(seconds);

  useEffect(() => {
    setTime(seconds);
    
    const timer = setInterval(() => {
      setTime((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);

    return () => clearInterval(timer);
  }, [seconds]);

  return (
    <span className="font-mono font-bold">
      {time} seconds
    </span>
  );
}