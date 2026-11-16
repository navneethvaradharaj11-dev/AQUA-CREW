import React from "react";
import fs from "fs";
import path from "path";
import Link from "next/link";
import { notFound } from "next/navigation";
import {
  BookOpen,
  ArrowLeft,
  Download,
  ChevronRight,
  Shield,
  Layers,
  Cpu,
  FileCode,
  Activity,
  FileText,
  Terminal,
} from "lucide-react";
import { MarkdownRenderer } from "@/components/docs/MarkdownRenderer";

interface DocsPageProps {
  params: {
    slug?: string[];
  };
}

interface DocNavItem {
  id: string;
  filename: string;
  title: string;
  description: string;
  category: "architecture" | "api" | "security" | "operations";
}

const DOC_ITEMS: DocNavItem[] = [
  // Architecture & Engineering
  {
    id: "architecture",
    filename: "ARCHITECTURE.md",
    title: "System Architecture Overview",
    description: "Core vision, strict software-first strategy & module topology.",
    category: "architecture",
  },
  {
    id: "system-architecture",
    filename: "AQUA_CREW_SYSTEM_ARCHITECTURE.md",
    title: "Comprehensive System Architecture",
    description: "Monorepo topology, inter-service messaging & domain models.",
    category: "architecture",
  },
  {
    id: "ai-architecture",
    filename: "ADVANCED_AI_ARCHITECTURE.md",
    title: "AI & Signal Intelligence Architecture",
    description: "Acoustic FFT, wavelet decomposition & anomaly inference.",
    category: "architecture",
  },
  {
    id: "hydraulic-digital-twin",
    filename: "AQUA_CREW_HYDRAULIC_DIGITAL_TWIN.md",
    title: "Hydraulic Digital Twin & EPANET",
    description: "Todini gradient solver, pipe network modeling & hydraulic twin.",
    category: "architecture",
  },
  {
    id: "iot-architecture",
    filename: "AQUA_CREW_IOT_ARCHITECTURE.md",
    title: "IoT & Hardware Integration Ecosystem",
    description: "MQTT protocols, sensor calibration, edge gateways & safety locks.",
    category: "architecture",
  },

  // APIs & Specifications
  {
    id: "api-spec",
    filename: "API_SPECIFICATION.md",
    title: "REST & WebSockets API Specification",
    description: "Full endpoint specifications, authentication schemas & payloads.",
    category: "api",
  },
  {
    id: "ai-api-spec",
    filename: "AI_API_SPECIFICATION.md",
    title: "AI Waveform & Detection API Specification",
    description: "Synthetic signal generation, inference queries & ROC metrics.",
    category: "api",
  },
  {
    id: "websocket-spec",
    filename: "WEBSOCKET_SPECIFICATION.md",
    title: "Real-Time Telemetry Streaming Protocol",
    description: "Asynchronous pub/sub, rover state sync & alert broadcast.",
    category: "api",
  },

  // Security & Reliability
  {
    id: "security-review",
    filename: "AQUA_CREW_SECURITY_REVIEW.md",
    title: "Security & Threat Mitigation Review",
    description: "RBAC policies, JWT verification, rate limiting & attack defense.",
    category: "security",
  },
  {
    id: "safety-governance",
    filename: "AQUA_CREW_SAFETY_AND_GOVERNANCE.md",
    title: "Hardware Safety & Governance Lockout",
    description: "HARDWARE_ACTUATION_ENABLED = false enforcement policies.",
    category: "security",
  },
  {
    id: "ai-security",
    filename: "AI_AUTHORIZATION_SECURITY.md",
    title: "AI Governance & Prompt Interlocks",
    description: "Anti-jailbreak sanitizers, telemetry integrity & audit trails.",
    category: "security",
  },

  // Operations & Guides
  {
    id: "user-guide",
    filename: "AQUA_CREW_USER_GUIDE.md",
    title: "Operator Command Center User Guide",
    description: "Comprehensive operational handbook for municipal engineers.",
    category: "operations",
  },
  {
    id: "operations-guide",
    filename: "AQUA_CREW_OPERATIONS_GUIDE.md",
    title: "Dispatch & Incident Workflow Guide",
    description: "Incident triage, rover mission dispatch & repair work orders.",
    category: "operations",
  },
  {
    id: "deployment-guide",
    filename: "AQUA_CREW_DEPLOYMENT_GUIDE.md",
    title: "Production Deployment & Infrastructure",
    description: "Docker compose, environment variables & hosting best practices.",
    category: "operations",
  },
  {
    id: "release-notes",
    filename: "AQUA_CREW_RELEASE_NOTES.md",
    title: "Product Release Notes & Milestones",
    description: "Release changelog, verified engineering milestones & roadmap.",
    category: "operations",
  },
];

function resolveDocumentFile(slugParts?: string[]): { filename: string; currentDoc: DocNavItem } {
  if (!slugParts || slugParts.length === 0) {
    return { filename: "ARCHITECTURE.md", currentDoc: DOC_ITEMS[0] };
  }

  const rawSlug = slugParts.join("/");
  // Check exact filename match (e.g. "ARCHITECTURE.md")
  const exactMatch = DOC_ITEMS.find(
    (d) => d.filename.toLowerCase() === rawSlug.toLowerCase() || d.id.toLowerCase() === rawSlug.toLowerCase()
  );

  if (exactMatch) {
    return { filename: exactMatch.filename, currentDoc: exactMatch };
  }

  // Check with .md appended
  const withMd = DOC_ITEMS.find(
    (d) => d.filename.toLowerCase() === `${rawSlug.toLowerCase()}.md`
  );
  if (withMd) {
    return { filename: withMd.filename, currentDoc: withMd };
  }

  // Fallback: check if the file literally exists in docs
  const cleanFilename = rawSlug.endsWith(".md") ? rawSlug : `${rawSlug}.md`;
  return {
    filename: cleanFilename,
    currentDoc: {
      id: rawSlug,
      filename: cleanFilename,
      title: cleanFilename.replace(/\.md$/i, "").replace(/_/g, " "),
      description: "Technical Dossier & Engineering Document",
      category: "architecture",
    },
  };
}

function loadMarkdownContent(filename: string): string | null {
  const possiblePaths = [
    path.join(process.cwd(), "public/docs", filename),
    path.join(process.cwd(), "../../docs", filename),
    path.join(process.cwd(), "../docs", filename),
    path.join(process.cwd(), "docs", filename),
    path.resolve(__dirname, "../../../../../../docs", filename),
  ];

  for (const p of possiblePaths) {
    try {
      if (fs.existsSync(p)) {
        return fs.readFileSync(p, "utf-8");
      }
    } catch {
      // continue search
    }
  }

  return null;
}

export default function DocsPage({ params }: DocsPageProps) {
  const { filename, currentDoc } = resolveDocumentFile(params.slug);
  const content = loadMarkdownContent(filename);

  if (!content) {
    notFound();
  }

  const categories = [
    { key: "architecture", title: "Architecture & Systems", icon: <Layers className="h-4 w-4 text-cyan-400" /> },
    { key: "api", title: "APIs & Protocols", icon: <FileCode className="h-4 w-4 text-purple-400" /> },
    { key: "security", title: "Security & Safety", icon: <Shield className="h-4 w-4 text-emerald-400" /> },
    { key: "operations", title: "Operations & Manuals", icon: <Activity className="h-4 w-4 text-amber-400" /> },
  ] as const;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* Top Navbar */}
      <header className="sticky top-0 z-40 border-b border-slate-800 bg-slate-950/90 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors text-xs font-mono"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Back to Home</span>
            </Link>
            <span className="text-slate-700">|</span>
            <div className="flex items-center gap-2">
              <BookOpen className="h-5 w-5 text-cyan-400" />
              <span className="font-bold tracking-tight text-white font-mono text-sm">
                AQUA CREW <span className="text-cyan-400 font-normal">/ DOCS</span>
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <a
              href={`/api/docs/raw/${filename}`}
              download={filename}
              className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900/80 text-xs font-mono text-slate-300 hover:text-white hover:border-slate-700 transition-colors shadow-sm"
              title="Download Raw Markdown file"
            >
              <Download className="h-3.5 w-3.5 text-cyan-400" />
              <span>Raw .md</span>
            </a>
            <Link
              href="/app"
              className="px-3.5 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs font-mono transition-colors shadow-lg shadow-cyan-950/40"
            >
              Open Command Center &rarr;
            </Link>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 flex flex-col md:flex-row gap-8 w-full">
        {/* Left Sticky Sidebar */}
        <aside className="w-full md:w-72 shrink-0 space-y-6">
          <div className="rounded-xl border border-slate-800/80 bg-slate-900/40 p-4 space-y-6">
            {categories.map((cat) => {
              const items = DOC_ITEMS.filter((d) => d.category === cat.key);
              if (items.length === 0) return null;

              return (
                <div key={cat.key} className="space-y-2">
                  <div className="flex items-center gap-2 text-xs font-mono font-bold text-slate-400 uppercase tracking-wider px-2">
                    {cat.icon}
                    <span>{cat.title}</span>
                  </div>
                  <nav className="space-y-0.5">
                    {items.map((item) => {
                      const isActive = item.filename.toLowerCase() === filename.toLowerCase();

                      return (
                        <Link
                          key={item.id}
                          href={`/docs/${item.filename}`}
                          className={`group flex items-start justify-between rounded-lg px-2.5 py-2 text-xs transition-all ${
                            isActive
                              ? "bg-cyan-950/60 text-cyan-300 font-bold border border-cyan-800/80 shadow-sm"
                              : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
                          }`}
                        >
                          <div className="truncate pr-1">
                            <div className="truncate">{item.title}</div>
                            <div className="text-[10px] text-slate-500 truncate font-mono mt-0.5 font-normal">
                              {item.filename}
                            </div>
                          </div>
                          {isActive && <ChevronRight className="h-3.5 w-3.5 shrink-0 text-cyan-400 mt-0.5" />}
                        </Link>
                      );
                    })}
                  </nav>
                </div>
              );
            })}
          </div>
        </aside>

        {/* Right Content Area */}
        <main className="flex-1 min-w-0">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/30 p-6 sm:p-10 shadow-2xl backdrop-blur-sm">
            {/* Header info badge */}
            <div className="mb-6 pb-6 border-b border-slate-800/80 flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="flex items-center gap-2 text-xs font-mono text-cyan-400 mb-1">
                  <FileText className="h-3.5 w-3.5" />
                  <span>AQUA CREW ENGINEERING DOSSIER</span>
                  <span>/</span>
                  <span className="text-slate-400">{filename}</span>
                </div>
                <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                  {currentDoc.title}
                </h1>
                <p className="text-xs text-slate-400 mt-1">{currentDoc.description}</p>
              </div>

              <a
                href={`/api/docs/raw/${filename}`}
                download={filename}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-950 text-xs font-mono text-slate-300 hover:text-white hover:border-slate-700 transition-colors"
              >
                <Download className="h-3.5 w-3.5 text-cyan-400" />
                <span>Download Markdown</span>
              </a>
            </div>

            {/* Markdown Body */}
            <MarkdownRenderer content={content} />
          </div>
        </main>
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-6 text-center text-xs text-slate-600 font-mono">
        AQUA CREW &bull; Autonomous Water Infrastructure Intelligence &bull; Production Release v1.0.0
      </footer>
    </div>
  );
}

