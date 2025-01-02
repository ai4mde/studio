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
import { LogOut } from 'lucide-react';
import { cn } from '@/lib/utils';

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
        className={cn(
          "flex items-center gap-2",
          "text-foreground hover:text-primary",
          "transition-colors duration-200",
          className
        )}
      >
        <LogOut className="h-4 w-4" />
        {children || 'Logout'}
      </button>

      <Dialog open={showDialog} onOpenChange={handleOpenChange}>
        <DialogContent 
          className="sm:max-w-md bg-background border-border" 
          onPointerDownOutside={(e) => e.preventDefault()}
        >
          <DialogHeader>
            <DialogTitle className="text-foreground">Logged Out</DialogTitle>
            <DialogDescription className="space-y-2 text-muted-foreground">
              <p>{`${getTimeBasedGreeting()} ${username}, You are logged out of the system now!`}</p>
              <p>To continue please login again.</p>
              <p>Have a nice day.</p>
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button 
              onClick={handleClose}
              className="bg-primary text-primary-foreground hover:bg-primary/90"
            >
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
} 