'use client';

import { motion, AnimatePresence, Variants } from 'framer-motion';
import { usePathname } from 'next/navigation';
import { ReactNode } from 'react';
import { useReducedMotion } from 'framer-motion';

interface AnimatedLayoutProps {
  children: ReactNode;
}

/**
 * Global animated layout using AnimatePresence keyed by route pathname
 * Provides smooth page transitions with reduced-motion accessibility
 */
export function AnimatedLayout({ children }: AnimatedLayoutProps) {
  const pathname = usePathname();
  const shouldReduceMotion = useReducedMotion();

  // Reduced motion variants for accessibility
  const pageVariants: Variants = shouldReduceMotion
    ? {
        hidden: { opacity: 0 },
        enter: { opacity: 1 },
        exit: { opacity: 0 },
      }
    : {
        hidden: { opacity: 0, y: 8 },
        enter: { opacity: 1, y: 0 },
        exit: { opacity: 0, y: -8 },
      };

  const pageTransition = shouldReduceMotion
    ? { duration: 0.1 }
    : { duration: 0.2 };

  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.div
        key={pathname}
        initial="hidden"
        animate="enter"
        exit="exit"
        variants={pageVariants}
        transition={pageTransition}
        className="min-h-screen"
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}

/**
 * Staggered children container for list animations
 */
interface StaggerContainerProps {
  children: ReactNode;
  className?: string;
}

export function StaggerContainer({ children, className }: StaggerContainerProps) {
  const shouldReduceMotion = useReducedMotion();

  const containerVariants: Variants = shouldReduceMotion
    ? {
        hidden: { opacity: 0 },
        show: {
          opacity: 1,
          transition: {
            staggerChildren: 0,
          },
        },
      }
    : {
        hidden: { opacity: 0 },
        show: {
          opacity: 1,
          transition: {
            staggerChildren: 0.05,
            delayChildren: 0.1,
          },
        },
      };

  return (
    <motion.div
      className={className}
      variants={containerVariants}
      initial="hidden"
      animate="show"
    >
      {children}
    </motion.div>
  );
}

/**
 * Animated item for use inside StaggerContainer
 */
interface StaggerItemProps {
  children: ReactNode;
  className?: string;
}

export function StaggerItem({ children, className }: StaggerItemProps) {
  const shouldReduceMotion = useReducedMotion();

  const itemVariants: Variants = shouldReduceMotion
    ? {
        hidden: { opacity: 0 },
        show: { opacity: 1 },
      }
    : {
        hidden: { opacity: 0, y: 16 },
        show: { opacity: 1, y: 0 },
      };

  return (
    <motion.div className={className} variants={itemVariants}>
      {children}
    </motion.div>
  );
}
