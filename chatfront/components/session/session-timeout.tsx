'use client';

import { useEffect, useState, useCallback } from 'react';
import { useSession, signOut } from 'next-auth/react';
import { AlertMessageDialog } from '../chat/alert-dialog';

const SESSION_TIMEOUT_DURATION = Number(process.env.NEXT_PUBLIC_SESSION_TIMEOUT_DURATION ?? 30);
const SESSION_WARNING_THRESHOLD = Number(process.env.NEXT_PUBLIC_SESSION_WARNING_THRESHOLD ?? 20);

export function SessionTimeout() {
  const { status } = useSession();
  const [showWarning, setShowWarning] = useState(false);
  const [timeLeft, setTimeLeft] = useState(SESSION_TIMEOUT_DURATION);

  const resetTimer = useCallback(() => {
    setTimeLeft(SESSION_TIMEOUT_DURATION);
    setShowWarning(false);
  }, []);

  useEffect(() => {
    if (status !== 'authenticated') return;

    const timer = setInterval(() => {
      setTimeLeft((current) => {
        const newTime = current - 1;
        
        if (newTime === SESSION_WARNING_THRESHOLD) {
          setShowWarning(true);
        }
        
        if (newTime <= 0) {
          clearInterval(timer);
          signOut({ redirect: true, callbackUrl: '/login' });
        }

        return newTime;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [status, timeLeft]);

  useEffect(() => {
    if (showWarning) return;

    const handleActivity = () => {
      resetTimer();
    };

    window.addEventListener('mousemove', handleActivity);
    window.addEventListener('keydown', handleActivity);
    window.addEventListener('click', handleActivity);

    return () => {
      window.removeEventListener('mousemove', handleActivity);
      window.removeEventListener('keydown', handleActivity);
      window.removeEventListener('click', handleActivity);
    };
  }, [resetTimer, showWarning]);

  return (
    <AlertMessageDialog
      isOpen={showWarning}
      onClose={() => signOut({ redirect: true, callbackUrl: '/login' })}
      onContinue={resetTimer}
      title="Session Expiring Soon"
      message="Your session will expire soon. Click 'Continue Session' to stay logged in."
      showContinue={true}
      countdownSeconds={timeLeft}
    />
  );
} 