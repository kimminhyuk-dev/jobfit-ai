interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warn' | 'danger' | 'muted' | 'primary';
  size?: 'sm' | 'md';
  className?: string;
}

const variantStyles: Record<string, string> = {
  default: 'bg-m-surface-alt text-m-muted border border-m-border',
  primary: 'bg-m-primary-soft text-m-primary',
  success: 'bg-m-success-soft text-m-success',
  warn: 'bg-m-warn-soft text-m-warn',
  danger: 'bg-m-danger-soft text-m-danger',
  muted: 'bg-m-surface-alt text-m-subtle',
};

const sizeStyles: Record<string, string> = {
  sm: 'text-[11px] px-2 py-0.5',
  md: 'text-xs px-2.5 py-1',
};

export default function Badge({ children, variant = 'default', size = 'sm', className = '' }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full font-medium ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
    >
      {children}
    </span>
  );
}
