'use client';

import dynamic from 'next/dynamic';

const SessionTimeout = dynamic(
  () => import('@/components/session/session-timeout').then(mod => mod.SessionTimeout),
  { ssr: false }
);

export function SessionTimeoutProvider() {
  return <SessionTimeout />;
} 