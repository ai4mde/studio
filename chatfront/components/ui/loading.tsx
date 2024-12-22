import React from 'react';
import { cn } from '@/lib/utils';
import { matrixStyles } from '@/components/ui/matrix-styles';

const Loading: React.FC = () => {
  return (
    <div className={cn(
      "flex items-center gap-2",
      matrixStyles.text.glow,
      matrixStyles.effects.pulse
    )}>
      Loading...
    </div>
  );
};

export default Loading; 