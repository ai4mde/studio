import * as React from 'react';
import { useEffect, useState } from 'react';
import { Alert, AlertDescription } from '../ui/alert';
import { Button } from '../ui/button';

interface SessionTimeoutWarningProps {
  timeoutMinutes: number;
  onTimeout: () => void;
}

export function SessionTimeoutWarning({ timeoutMinutes, onTimeout }: SessionTimeoutWarningProps) {
  const [remainingTime, setRemainingTime] = useState(timeoutMinutes * 60);
  const [showWarning, setShowWarning] = useState(false);

  const resetTimer = () => {
    setRemainingTime(timeoutMinutes * 60);
    setShowWarning(false);
  };

  useEffect(() => {
    let timer: NodeJS.Timeout;
    
    // Show warning 60 seconds before timeout
    const warningTime = 60; // 60 seconds warning
    
    const updateTimer = () => {
      setRemainingTime(prev => {
        const newTime = prev - 1;
        if (newTime <= 0) {
          onTimeout();
          return 0;
        }
        if (newTime <= warningTime) {
          setShowWarning(true);
        }
        return newTime;
      });
    };

    timer = setInterval(updateTimer, 1000);
    
    return () => clearInterval(timer);
  }, [timeoutMinutes, onTimeout]);

  if (!showWarning) return null;

  const seconds = remainingTime % 60;

  return (
    <Alert className="fixed bottom-4 right-4 max-w-md bg-yellow-50 border-yellow-200 dark:bg-yellow-900/10 dark:border-yellow-900/20">
      <AlertDescription className="flex flex-col gap-3">
        <p>Your session will expire in {seconds} seconds.</p>
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={resetTimer}>
            Continue Session
          </Button>
          <Button variant="destructive" onClick={onTimeout}>
            Log Off
          </Button>
        </div>
      </AlertDescription>
    </Alert>
  );
} 