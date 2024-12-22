'use client';

import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useState } from 'react';
import { getTimeBasedGreeting } from '@/lib/utils/greeting';
import { useRouter } from 'next/navigation';
import { useSession } from "next-auth/react";

interface LogoutButtonProps {
  onLogout: () => Promise<void>;
  className?: string;
  children?: React.ReactNode;
}

export default function LogoutButton({ onLogout, className, children }: LogoutButtonProps) {
  const [showDialog, setShowDialog] = useState(false);
  const router = useRouter();
  const { data: session } = useSession();
  const username = session?.user?.name || session?.user?.username || 'User';

  const handleLogoutClick = async () => {
    try {
      await onLogout();
      setShowDialog(true);
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  const handleClose = () => {
    setShowDialog(false);
    router.push('/login');
  };

  const handleOpenChange = (open: boolean) => {
    if (!open) {
      handleClose();
    }
  };

  return (
    <>
      <button
        onClick={handleLogoutClick}
        className={className}
      >
        {children || 'Logout'}
      </button>

      <Dialog open={showDialog} onOpenChange={handleOpenChange}>
        <DialogContent className="sm:max-w-md" onPointerDownOutside={(e) => e.preventDefault()}>
          <DialogHeader>
            <DialogTitle>Logged Out</DialogTitle>
            <DialogDescription className="space-y-2">
              <p>{`${getTimeBasedGreeting()} ${username}, You are logged out of the system now!`}</p>
              <p>To continue please login again.</p>
              <p>Have a nice day.</p>
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button onClick={handleClose}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
} 