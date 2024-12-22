'use client';

import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogCancel,
  AlertDialogAction,
} from "@/components/ui/alert-dialog"
import { Countdown } from '@/components/ui/countdown';

interface AlertMessageDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onContinue?: () => void;
  title: string;
  message: string;
  showContinue?: boolean;
  countdownSeconds?: number;
}

export function AlertMessageDialog({
  isOpen,
  onClose,
  onContinue,
  title,
  message,
  showContinue,
  countdownSeconds
}: AlertMessageDialogProps) {
  return (
    <AlertDialog open={isOpen}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{title}</AlertDialogTitle>
          <AlertDialogDescription>
            <span className="block">{message}</span>
            {countdownSeconds && (
              <span className="block mt-2 text-center">
                Time remaining: <Countdown seconds={countdownSeconds} />
              </span>
            )}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={onClose}>Logout</AlertDialogCancel>
          {showContinue && (
            <AlertDialogAction onClick={onContinue}>
              Continue Session
            </AlertDialogAction>
          )}
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
} 