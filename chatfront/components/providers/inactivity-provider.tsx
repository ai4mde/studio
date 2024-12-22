'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import { useSession, signOut } from 'next-auth/react';
import { useRouter } from 'next/navigation';

const INACTIVITY_TIMEOUT = Number(process.env.NEXT_PUBLIC_SESSION_TIMEOUT_DURATION ?? 1800); // 30 minutes
const WARNING_THRESHOLD = Number(process.env.NEXT_PUBLIC_SESSION_WARNING_THRESHOLD ?? 120);   // 2 minutes

interface InactivityContextType {
  showWarning: boolean;
  timeRemaining: number;
  resetTimer: () => void;
}

const InactivityContext = createContext<InactivityContextType>({
  showWarning: false,
  timeRemaining: INACTIVITY_TIMEOUT,
  resetTimer: () => {}
});

export function InactivityProvider({ children }: { children: React.ReactNode }) {
  const { data: session } = useSession();
  const router = useRouter();
  const [lastActivity, setLastActivity] = useState(Date.now());
  const [showWarning, setShowWarning] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState(INACTIVITY_TIMEOUT);

  const resetTimer = () => {
    setLastActivity(Date.now());
    setShowWarning(false);
  };

  useEffect(() => {
    if (!session) return;

    const handleActivity = () => resetTimer();

    // Add event listeners for user activity
    window.addEventListener('mousemove', handleActivity);
    window.addEventListener('keydown', handleActivity);
    window.addEventListener('click', handleActivity);
    window.addEventListener('scroll', handleActivity);

    const checkInactivity = setInterval(() => {
      const timeSinceLastActivity = (Date.now() - lastActivity) / 1000;
      const remainingTime = INACTIVITY_TIMEOUT - timeSinceLastActivity;
      
      setTimeRemaining(Math.max(0, Math.floor(remainingTime)));

      if (remainingTime <= WARNING_THRESHOLD) {
        setShowWarning(true);
      }

      if (remainingTime <= 0) {
        signOut({ redirect: true, callbackUrl: '/login' });
      }
    }, 1000);

    return () => {
      window.removeEventListener('mousemove', handleActivity);
      window.removeEventListener('keydown', handleActivity);
      window.removeEventListener('click', handleActivity);
      window.removeEventListener('scroll', handleActivity);
      clearInterval(checkInactivity);
    };
  }, [session, lastActivity, router]);

  return (
    <InactivityContext.Provider value={{ showWarning, timeRemaining, resetTimer }}>
      {children}
    </InactivityContext.Provider>
  );
}

export const useInactivity = () => useContext(InactivityContext); 