import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';
import { motion, HTMLMotionProps } from 'framer-motion';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center whitespace-nowrap rounded-lg text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default:
          'bg-primary-600 text-white hover:bg-primary-700 focus-visible:ring-primary-500',
        destructive:
          'bg-danger-600 text-white hover:bg-danger-700 focus-visible:ring-danger-500',
        outline:
          'border border-gray-300 bg-white hover:bg-gray-50 hover:text-gray-900',
        secondary:
          'bg-gray-200 text-gray-900 hover:bg-gray-300 focus-visible:ring-gray-500',
        ghost:
          'hover:bg-gray-100 hover:text-gray-900',
        link:
          'text-primary-600 underline-offset-4 hover:underline',
        success:
          'bg-success-600 text-white hover:bg-success-700 focus-visible:ring-success-500',
        warning:
          'bg-warning-600 text-white hover:bg-warning-700 focus-visible:ring-warning-500',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 rounded-md px-3',
        lg: 'h-11 rounded-lg px-8',
        xl: 'h-12 rounded-lg px-10 text-base',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  isLoading?: boolean;
  animation?: 'none' | 'scale' | 'shine';
}

/**
 * Animated Button component with micro-interactions
 * Supports scale on hover, loading states, and shine effect
 */
const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, isLoading, animation = 'none', children, disabled, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button';
    const [isHovered, setIsHovered] = React.useState(false);

    const MotionComp = motion(Comp);

    const getMotionProps = (): HTMLMotionProps<'button'> => {
      if (animation === 'scale') {
        return {
          whileHover: { scale: disabled || isLoading ? 1 : 1.02 },
          whileTap: { scale: disabled || isLoading ? 1 : 0.98 },
          transition: { duration: 0.15 },
        };
      }
      if (animation === 'shine') {
        return {
          whileHover: { 
            boxShadow: disabled || isLoading ? 'none' : '0 0 20px rgba(14, 165, 233, 0.3)' 
          },
        };
      }
      return {};
    };

    return (
      <MotionComp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={disabled || isLoading}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        {...getMotionProps()}
        {...(props as any)}
      >
        {isLoading ? (
          <motion.span
            className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          />
        ) : null}
        {children}
      </MotionComp>
    );
  }
);
Button.displayName = 'Button';

export { Button, buttonVariants };
