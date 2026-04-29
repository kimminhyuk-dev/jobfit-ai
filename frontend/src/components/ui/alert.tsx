import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';

import { cn } from '../../lib/utils';

const alertVariants = cva('rounded-lg border px-3 py-2 text-[13px]', {
  variants: {
    variant: {
      default: 'border-m-border bg-m-surface text-m-text',
      danger: 'border-m-danger/20 bg-m-danger-soft text-m-danger',
      success: 'border-m-success/20 bg-m-success-soft text-m-success',
    },
  },
  defaultVariants: {
    variant: 'default',
  },
});

export interface AlertProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof alertVariants> {}

const Alert = React.forwardRef<HTMLDivElement, AlertProps>(
  ({ className, variant, ...props }, ref) => (
    <div
      ref={ref}
      role="alert"
      className={cn(alertVariants({ variant, className }))}
      {...props}
    />
  ),
);
Alert.displayName = 'Alert';

export { Alert };
