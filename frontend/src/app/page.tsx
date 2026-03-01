"use client";

import { useEffect } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  Upload,
  Brain,
  Edit3,
  Download,
  Zap,
  Clock,
  Layers,
  Users,
  FileText,
  CheckCircle2,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/ThemeToggle";

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.55, ease: [0.22, 1, 0.36, 1] },
  }),
};

const steps = [
  {
    icon: Upload,
    title: "Upload Your Idea",
    desc: "Paste a description or upload RFPs, PDFs, or Excel files",
    color: "from-blue-500/20 to-blue-600/5",
    iconColor: "text-blue-400",
  },
  {
    icon: Brain,
    title: "AI Analyzes",
    desc: "Our AI breaks down features, estimates hours, and recommends tech stacks",
    color: "from-violet-500/20 to-violet-600/5",
    iconColor: "text-violet-400",
  },
  {
    icon: Edit3,
    title: "Review & Edit",
    desc: "Fine-tune estimates, priorities, and resource allocations",
    color: "from-cyan-500/20 to-cyan-600/5",
    iconColor: "text-cyan-400",
  },
  {
    icon: Download,
    title: "Download Proposal",
    desc: "Export a client-ready PDF proposal in one click",
    color: "from-emerald-500/20 to-emerald-600/5",
    iconColor: "text-emerald-400",
  },
];

const features = [
  {
    icon: Layers,
    title: "Feature Extraction",
    desc: "Automatically identifies modules, features, and sub-tasks from unstructured input",
    glow: "group-hover:text-blue-400",
  },
  {
    icon: Clock,
    title: "Hour Estimation",
    desc: "AI-powered effort estimation across frontend, backend, integration & testing",
    glow: "group-hover:text-violet-400",
  },
  {
    icon: Zap,
    title: "Tech Stack Recommendation",
    desc: "Smart technology suggestions based on project requirements and constraints",
    glow: "group-hover:text-amber-400",
  },
  {
    icon: Users,
    title: "Resource Allocation",
    desc: "Optimal team composition with role-based hour distribution",
    glow: "group-hover:text-cyan-400",
  },
  {
    icon: Edit3,
    title: "Editable Tables",
    desc: "Inline editing with auto-calculated totals and priority management",
    glow: "group-hover:text-pink-400",
  },
  {
    icon: FileText,
    title: "One-Click Proposal",
    desc: "Generate professional PDF proposals ready for client presentation",
    glow: "group-hover:text-emerald-400",
  },
];

const stats = [
  {
    value: "500+",
    label: "Proposals Generated",
    color: "from-blue-400 to-violet-400",
  },
  {
    value: "4.2 min",
    label: "Average Time",
    color: "from-violet-400 to-pink-400",
  },
  { value: "92%", label: "Approval Rate", color: "from-cyan-400 to-blue-400" },
  {
    value: "150+",
    label: "Teams Using",
    color: "from-emerald-400 to-cyan-400",
  },
];

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    if (typeof window === "undefined") return;
    const token = window.localStorage.getItem("authToken");
    if (token) {
      router.replace("/dashboard");
    }
  }, [router]);

  return (
    <div className="min-h-screen overflow-x-hidden bg-background">
      {/* Navbar */}
      <nav className="sticky top-0 z-40 bg-background/70 backdrop-blur-xl border-b border-border/40">
        <div className="container mx-auto flex items-center justify-between h-14 px-4">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="w-9 h-9 rounded-xl gradient-bg flex items-center justify-center shadow-md shadow-primary/30 group-hover:shadow-primary/50 transition-shadow">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <span className="font-display text-lg font-bold tracking-tight">
              Neural Architects
            </span>
          </Link>
          <div className="hidden md:flex items-center gap-6 text-sm font-medium text-muted-foreground">
            <a
              href="#how-it-works"
              className="hover:text-foreground transition-colors relative after:absolute after:bottom-[-2px] after:left-0 after:w-0 after:h-[1px] after:bg-primary hover:after:w-full after:transition-all"
            >
              How It Works
            </a>
            <a
              href="#features"
              className="hover:text-foreground transition-colors relative after:absolute after:bottom-[-2px] after:left-0 after:w-0 after:h-[1px] after:bg-primary hover:after:w-full after:transition-all"
            >
              Features
            </a>
            <a
              href="#stats"
              className="hover:text-foreground transition-colors relative after:absolute after:bottom-[-2px] after:left-0 after:w-0 after:h-[1px] after:bg-primary hover:after:w-full after:transition-all"
            >
              Stats
            </a>
          </div>
          <div className="flex items-center gap-2">
            <ThemeToggle
              inline
              className="h-8 w-8 border-border/40 hover:bg-primary/5"
            />
            <Link href="/login">
              <Button
                variant="ghost"
                size="sm"
                className="text-muted-foreground hover:text-foreground"
              >
                Log In
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden pt-16 pb-20 dot-grid">
        {/* Aurora orbs — soft glow, no harsh darkening */}
        <div
          className="absolute top-[-10%] right-[-5%] w-[580px] h-[580px] rounded-full pointer-events-none"
          style={{
            background:
              "radial-gradient(circle, hsl(217 95% 70% / 0.08), transparent 55%)",
            filter: "blur(70px)",
            animation: "aurora-float 14s ease-in-out infinite alternate",
          }}
        />
        <div
          className="absolute bottom-[-5%] left-[-5%] w-[480px] h-[480px] rounded-full pointer-events-none"
          style={{
            background:
              "radial-gradient(circle, hsl(263 85% 70% / 0.07), transparent 55%)",
            filter: "blur(70px)",
            animation:
              "aurora-float 10s ease-in-out infinite alternate-reverse",
          }}
        />
        <div
          className="absolute top-[35%] left-[25%] w-[320px] h-[320px] rounded-full pointer-events-none"
          style={{
            background:
              "radial-gradient(circle, hsl(160 84% 50% / 0.04), transparent 60%)",
            filter: "blur(60px)",
            animation: "aurora-float 16s ease-in-out infinite alternate",
          }}
        />

        <div className="container mx-auto px-4 relative z-10">
          <motion.div
            className="max-w-4xl mx-auto text-center"
            initial="hidden"
            animate="visible"
          >
            {/* Badge */}
            <motion.div
              variants={fadeUp}
              custom={0}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-primary/20 bg-primary/8 text-primary text-xs font-medium mb-5 backdrop-blur-sm"
            >
              <Sparkles className="w-3 h-3" />
              AI-Powered Presales Intelligence
              <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
            </motion.div>

            {/* Headline */}
            <motion.h1
              variants={fadeUp}
              custom={1}
              className="text-4xl md:text-5xl lg:text-6xl font-display font-bold tracking-tight leading-[1.08] mb-4"
            >
              From Idea to Proposal <br className="hidden md:block" />
              in <span className="gradient-text">Under 5 Minutes</span>
            </motion.h1>

            <motion.p
              variants={fadeUp}
              custom={2}
              className="text-base md:text-lg text-muted-foreground max-w-2xl mx-auto mb-6 leading-relaxed"
            >
              The Architect&apos;s Co-pilot that ingests unstructured client
              inputs and autonomously drafts technical proposals with feature
              breakdowns, hour estimates, and resource plans.
            </motion.p>

            {/* CTA buttons */}
            <motion.div
              variants={fadeUp}
              custom={3}
              className="flex flex-col sm:flex-row items-center justify-center gap-3"
            >
              <Link href="/login">
                <Button
                  size="lg"
                  className="btn-glow text-white text-sm px-6 h-10 rounded-xl"
                >
                  Get Started <ArrowRight className="w-4 h-4 ml-1.5" />
                </Button>
              </Link>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="relative py-12">
        <div className="absolute inset-0 bg-grid-pattern opacity-30" />
        <div className="container mx-auto px-4 relative z-10">
          <motion.div
            className="text-center mb-10"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
          >
            <p className="text-xs font-semibold uppercase tracking-widest text-primary mb-2">
              Simple process
            </p>
            <h2 className="text-2xl md:text-3xl font-display font-bold mb-2">
              How It Works
            </h2>
            <p className="text-muted-foreground text-sm max-w-xl mx-auto">
              Four simple steps from raw idea to polished proposal
            </p>
          </motion.div>

          <div className="grid md:grid-cols-4 gap-4 max-w-5xl mx-auto relative">
            <div className="hidden md:block absolute top-10 left-[12.5%] right-[12.5%] h-px bg-gradient-to-r from-transparent via-border to-transparent" />

            {steps.map((step, i) => (
              <motion.div
                key={step.title}
                className={`relative p-4 text-center rounded-xl border border-border/40 bg-gradient-to-b ${step.color} backdrop-blur-sm transition-all duration-300 hover:-translate-y-1 hover:border-primary/30 group`}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.12, duration: 0.5 }}
                whileHover={{ scale: 1.02 }}
              >
                <div
                  className={`w-10 h-10 rounded-lg gradient-bg flex items-center justify-center mx-auto mb-3 shadow-md shadow-primary/25 group-hover:shadow-primary/40 group-hover:scale-110 transition-all duration-300`}
                >
                  <step.icon className="w-5 h-5 text-white" />
                </div>
                <div className="step-badge">{i + 1}</div>
                <h3 className="font-display font-semibold text-sm mb-1">
                  {step.title}
                </h3>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {step.desc}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-14 relative overflow-hidden">
        <div
          className="absolute top-1/2 right-0 -translate-y-1/2 w-[400px] h-[400px] rounded-full pointer-events-none"
          style={{
            background:
              "radial-gradient(circle, hsl(263 85% 65% / 0.08), transparent 70%)",
            filter: "blur(60px)",
          }}
        />
        <div className="container mx-auto px-4 relative z-10">
          <motion.div
            className="text-center mb-10"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <p className="text-xs font-semibold uppercase tracking-widest text-accent mb-2">
              What&apos;s included
            </p>
            <h2 className="text-2xl md:text-3xl font-display font-bold mb-2">
              Powerful Features
            </h2>
            <p className="text-muted-foreground text-sm max-w-xl mx-auto">
              Everything you need to create accurate, professional proposals
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-4 max-w-5xl mx-auto">
            {features.map((f, i) => (
              <motion.div
                key={f.title}
                className="glass-card-hover p-4 rounded-xl group cursor-default"
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08, duration: 0.5 }}
                whileHover={{ y: -4 }}
              >
                <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center mb-3 group-hover:bg-primary/20 group-hover:scale-110 transition-all duration-300">
                  <f.icon
                    className={`w-5 h-5 text-primary transition-colors duration-300 ${f.glow}`}
                  />
                </div>
                <h3 className="font-display font-semibold text-sm mb-1 group-hover:text-primary transition-colors">
                  {f.title}
                </h3>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {f.desc}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-14 relative overflow-hidden">
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background:
              "radial-gradient(ellipse 80% 50% at 50% 100%, hsl(217 95% 65% / 0.07), transparent)",
          }}
        />
        <div className="container mx-auto px-4 relative z-10">
          <motion.div
            className="max-w-3xl mx-auto text-center"
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <div className="relative p-6 md:p-8 rounded-2xl border border-primary/20 bg-card/60 backdrop-blur-xl overflow-hidden">
              <div className="absolute top-0 left-1/2 -translate-x-1/2 w-3/4 h-px bg-gradient-to-r from-transparent via-primary/50 to-transparent" />
              <div className="absolute -top-8 -left-8 w-32 h-32 rounded-full bg-primary/10 blur-2xl" />
              <div className="absolute -bottom-8 -right-8 w-32 h-32 rounded-full bg-accent/10 blur-2xl" />

              <div className="relative z-10">
                <div className="w-12 h-12 rounded-xl gradient-bg flex items-center justify-center mx-auto mb-4 shadow-lg shadow-primary/30 animate-float-slow">
                  <CheckCircle2 className="w-6 h-6 text-white" />
                </div>
                <h2 className="text-2xl md:text-3xl font-display font-bold mb-3">
                  Ready to Supercharge Your Presales?
                </h2>
                <p className="text-muted-foreground mb-6 max-w-lg mx-auto text-sm leading-relaxed">
                  Stop spending hours on RFP responses. Let Neural Architects
                  handle the heavy lifting.
                </p>
                <Link href="/login">
                  <Button
                    size="lg"
                    className="btn-glow text-white px-8 h-10 text-sm rounded-xl"
                  >
                    Get Started Free <ArrowRight className="w-4 h-4 ml-1.5" />
                  </Button>
                </Link>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border/40 py-6">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg gradient-bg flex items-center justify-center shadow-sm shadow-primary/25">
                <Brain className="w-4 h-4 text-white" />
              </div>
              <span className="font-display font-bold tracking-tight">
                Neural Architects
              </span>
            </div>
            <p className="text-sm text-muted-foreground">
              © 2026 Neural Architects. The Proposal Automation Engine.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
