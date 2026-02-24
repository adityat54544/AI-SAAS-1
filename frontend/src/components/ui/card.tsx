import * as React from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';
import { cn } from '@/lib/utils';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hover?: boolean;
  animation?: 'none' | 'scale' | 'lift';
}

/**
 * Animated Card component with hover effects
 */
const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, hover = false, animation = 'none', children, ...props }, ref) => {
    const MotionDiv = motion.div;

    const getMotionProps = (): HTMLMotionProps<'div'> => {
      if (animation === 'scale') {
        return {
          whileHover: { scale: 1.01 },
          whileTap: { scale: 0.99 },
          transition: { duration: 0.15 },
        };
      }
      if (animation === 'lift') {
        return {
          whileHover: { y: -4, boxShadow: '0 10px 30px -10px rgba(0, 0, 0, 0.15)' },
          transition: { duration: 0.2 },
        };
      }
      return {};
    };

    return (
      <MotionDiv
        ref={ref}
        className={cn(
          'rounded-xl border border-gray-200 bg-white shadow-sm',
          hover && 'cursor-pointer transition-shadow hover:shadow-md',
          className
        )}
        {...getMotionProps()}
        {...(props as any)}
      >
        {children}
      </MotionDiv>
    );
  }
);
Card.displayName = 'Card';

const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('flex flex-col space-y-1.5 p-6', className)}
    {...props}
  />
));
CardHeader.displayName = 'CardHeader';

const CardTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn('text-lg font-semibold leading-none tracking-tight', className)}
    {...props}
  />
));
CardTitle.displayName = 'CardTitle';

const CardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn('text-sm text-gray-500', className)}
    {...props}
  />
));
CardDescription.displayName = 'CardDescription';

const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn('p-6 pt-0', className)} {...props} />
));
CardContent.displayName = 'CardContent';

const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('flex items-center p-6 pt-0', className)}
    {...props}
  />
));
CardFooter.displayName = 'CardFooter';

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent };
