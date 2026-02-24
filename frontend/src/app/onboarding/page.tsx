'use client';

export const dynamic = 'force-dynamic';

import { motion } from 'framer-motion';
import { useAuth } from '@/lib/auth-context';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { ThemeToggle } from '@/components/theme-toggle';
import { 
  Github, 
  Shield, 
  Zap, 
  GitBranch, 
  BarChart3, 
  ArrowRight,
  CheckCircle2,
  Sparkles,
  Rocket,
  Code2
} from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';

const features = [
  {
    icon: Shield,
    title: 'Security Analysis',
    description: 'Identify vulnerabilities and security issues in your codebase with AI-powered scanning.',
  },
  {
    icon: Zap,
    title: 'Performance Insights',
    description: 'Get detailed performance metrics and optimization recommendations.',
  },
  {
    icon: GitBranch,
    title: 'CI/CD Automation',
    description: 'Automatically generate and optimize your CI/CD workflows.',
  },
  {
    icon: BarChart3,
    title: 'Code Quality',
    description: 'Measure and improve your code quality with comprehensive analytics.',
  },
];

const steps = [
  {
    number: '01',
    title: 'Connect Your Repository',
    description: 'Sign in with GitHub and connect your repositories to start analyzing.',
  },
  {
    number: '02',
    title: 'Run Analysis',
    description: 'Our AI analyzes your code for security, performance, and quality issues.',
  },
  {
    number: '03',
    title: 'Apply Recommendations',
    description: 'Review AI suggestions and apply fixes with a single click.',
  },
];

export default function OnboardingPage() {
  const { isAuthenticated, signIn } = useAuth();
  const [currentStep, setCurrentStep] = useState(0);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      {/* Header */}
      <header className="relative z-10">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="p-2 bg-primary-600 rounded-lg">
                <Sparkles className="h-6 w-6 text-white" />
              </div>
              <span className="text-xl font-bold">AutoDevOps AI</span>
            </div>
            <div className="flex items-center gap-4">
              <ThemeToggle />
              {isAuthenticated ? (
                <Link href="/dashboard">
                  <Button>
                    Go to Dashboard
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </Link>
              ) : (
                <Button onClick={() => signIn()}>
                  <Github className="mr-2 h-4 w-4" />
                  Sign In
                </Button>
              )}
            </div>
          </div>
        </motion.div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden">
        {/* Background decorations */}
        <div className="absolute inset-0 pointer-events-none">
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 0.1, scale: 1 }}
            transition={{ duration: 1 }}
            className="absolute top-1/4 -left-32 w-96 h-96 bg-primary-500 rounded-full blur-3xl"
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 0.1, scale: 1 }}
            transition={{ duration: 1, delay: 0.2 }}
            className="absolute bottom-1/4 -right-32 w-96 h-96 bg-purple-500 rounded-full blur-3xl"
          />
        </div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
          >
            <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 text-sm font-medium mb-6">
              <Sparkles className="h-4 w-4" />
              AI-Powered Development
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-5xl md:text-7xl font-bold tracking-tight mb-6"
          >
            Supercharge Your
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-purple-600">
              {' '}Development
            </span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto mb-10"
          >
            Analyze your repositories, identify issues, and get AI-powered recommendations to improve your code quality, security, and performance.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            {!isAuthenticated ? (
              <Button size="xl" onClick={() => signIn()} className="gap-2">
                <Github className="h-5 w-5" />
                Get Started Free
                <ArrowRight className="h-5 w-5" />
              </Button>
            ) : (
              <Link href="/dashboard">
                <Button size="xl" className="gap-2">
                  <Rocket className="h-5 w-5" />
                  Launch Dashboard
                  <ArrowRight className="h-5 w-5" />
                </Button>
              </Link>
            )}
            <Button size="xl" variant="outline" className="gap-2">
              <Code2 className="h-5 w-5" />
              View Documentation
            </Button>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 bg-white/50 dark:bg-gray-800/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Everything You Need
            </h2>
            <p className="text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
              Powerful features to help you build better software, faster.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
              >
                <Card hover animation="lift" className="h-full">
                  <CardContent className="p-6">
                    <div className="p-3 bg-primary-100 dark:bg-primary-900/30 rounded-lg w-fit mb-4">
                      <feature.icon className="h-6 w-6 text-primary-600 dark:text-primary-400" />
                    </div>
                    <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                    <p className="text-gray-600 dark:text-gray-300">{feature.description}</p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              How It Works
            </h2>
            <p className="text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
              Get started in minutes with our simple three-step process.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {steps.map((step, index) => (
              <motion.div
                key={step.number}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="relative"
              >
                <div className="text-8xl font-bold text-gray-200 dark:text-gray-700 absolute -top-4 -left-2">
                  {step.number}
                </div>
                <div className="relative pt-12 pl-4">
                  <h3 className="text-xl font-semibold mb-2">{step.title}</h3>
                  <p className="text-gray-600 dark:text-gray-300">{step.description}</p>
                </div>
                {index < steps.length - 1 && (
                  <ArrowRight className="hidden md:block absolute top-1/2 -right-4 transform -translate-y-1/2 text-gray-300 dark:text-gray-600 h-8 w-8" />
                )}
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-gradient-to-r from-primary-600 to-purple-600">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center"
        >
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
            Ready to Transform Your Development?
          </h2>
          <p className="text-xl text-white/80 mb-10">
            Join thousands of developers who are already using AutoDevOps AI to build better software.
          </p>
          {!isAuthenticated && (
            <Button 
              size="xl" 
              variant="secondary" 
              onClick={() => signIn()}
              className="gap-2"
            >
              <Github className="h-5 w-5" />
              Get Started Now
              <ArrowRight className="h-5 w-5" />
            </Button>
          )}
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="p-1.5 bg-primary-600 rounded">
                <Sparkles className="h-4 w-4 text-white" />
              </div>
              <span className="font-medium">AutoDevOps AI</span>
            </div>
            <p className="text-sm text-gray-500">
              © 2024 AutoDevOps AI. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
