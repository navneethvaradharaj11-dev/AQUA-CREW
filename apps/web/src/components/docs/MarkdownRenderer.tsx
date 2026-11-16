"use client";

import React, { useState } from "react";
import { Check, Copy, Terminal } from "lucide-react";

interface MarkdownRendererProps {
  content: string;
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  // Parse markdown into structured blocks
  const blocks: React.ReactNode[] = [];
  const lines = content.split("\n");
  let i = 0;

  const renderInline = (text: string): React.ReactNode => {
    // Replace inline code, bold, links, badges
    const parts: React.ReactNode[] = [];
    let remaining = text;
    let key = 0;

    // Pattern for inline markdown tokens: `code`, **bold**, *italic*, [link](url)
    const regex = /(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*|\[[^\]]+\]\([^)]+\))/g;
    let match;
    let lastIndex = 0;

    while ((match = regex.exec(remaining)) !== null) {
      if (match.index > lastIndex) {
        parts.push(remaining.substring(lastIndex, match.index));
      }
      const token = match[0];
      if (token.startsWith("`") && token.endsWith("`")) {
        parts.push(
          <code
            key={key++}
            className="rounded bg-slate-800/80 px-1.5 py-0.5 font-mono text-[12px] text-cyan-300 border border-slate-700/60"
          >
            {token.slice(1, -1)}
          </code>
        );
      } else if (token.startsWith("**") && token.endsWith("**")) {
        parts.push(
          <strong key={key++} className="font-bold text-white">
            {token.slice(2, -2)}
          </strong>
        );
      } else if (token.startsWith("*") && token.endsWith("*")) {
        parts.push(
          <em key={key++} className="italic text-slate-300">
            {token.slice(1, -1)}
          </em>
        );
      } else if (token.startsWith("[")) {
        const linkMatch = token.match(/\[([^\]]+)\]\(([^)]+)\)/);
        if (linkMatch) {
          parts.push(
            <a
              key={key++}
              href={linkMatch[2]}
              target={linkMatch[2].startsWith("http") ? "_blank" : undefined}
              rel="noopener noreferrer"
              className="text-cyan-400 underline decoration-cyan-500/50 hover:text-cyan-300 transition-colors"
            >
              {linkMatch[1]}
            </a>
          );
        } else {
          parts.push(token);
        }
      }
      lastIndex = match.index + token.length;
    }

    if (lastIndex < remaining.length) {
      parts.push(remaining.substring(lastIndex));
    }

    return parts.length > 0 ? parts : text;
  };

  while (i < lines.length) {
    const line = lines[i];

    // Fenced Code Block
    if (line.trim().startsWith("```")) {
      const lang = line.trim().slice(3).trim();
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      i++; // skip closing ```
      const codeString = codeLines.join("\n");
      blocks.push(
        <CodeBlock key={`code-${i}`} code={codeString} language={lang || "text"} />
      );
      continue;
    }

    // Markdown Table
    if (line.trim().startsWith("|") && line.trim().endsWith("|")) {
      const tableLines: string[] = [];
      while (i < lines.length && lines[i].trim().startsWith("|") && lines[i].trim().endsWith("|")) {
        tableLines.push(lines[i]);
        i++;
      }

      if (tableLines.length >= 2) {
        const headerRow = tableLines[0]
          .split("|")
          .slice(1, -1)
          .map((c) => c.trim());
        const dataRows = tableLines
          .slice(2)
          .map((r) =>
            r
              .split("|")
              .slice(1, -1)
              .map((c) => c.trim())
          );

        blocks.push(
          <div key={`table-${i}`} className="my-6 overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/60 shadow-lg">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950/80">
                  {headerRow.map((h, colIdx) => (
                    <th key={colIdx} className="px-4 py-3 font-mono font-bold text-cyan-300 uppercase tracking-wider">
                      {renderInline(h)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-sans">
                {dataRows.map((row, rowIdx) => (
                  <tr key={rowIdx} className="hover:bg-slate-800/30 transition-colors">
                    {row.map((cell, cellIdx) => (
                      <td key={cellIdx} className="px-4 py-2.5 text-slate-300">
                        {renderInline(cell)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
        continue;
      }
    }

    // Headings
    if (line.startsWith("# ")) {
      blocks.push(
        <h1
          key={`h1-${i}`}
          id={line.slice(2).toLowerCase().replace(/[^a-z0-9]+/g, "-")}
          className="text-2xl sm:text-3xl font-extrabold text-white mt-8 mb-4 border-b border-slate-800 pb-3 flex items-center gap-2"
        >
          {line.slice(2)}
        </h1>
      );
      i++;
      continue;
    }

    if (line.startsWith("## ")) {
      blocks.push(
        <h2
          key={`h2-${i}`}
          id={line.slice(3).toLowerCase().replace(/[^a-z0-9]+/g, "-")}
          className="text-xl sm:text-2xl font-bold text-white mt-8 mb-3 text-cyan-100 flex items-center gap-2"
        >
          {line.slice(3)}
        </h2>
      );
      i++;
      continue;
    }

    if (line.startsWith("### ")) {
      blocks.push(
        <h3
          key={`h3-${i}`}
          id={line.slice(4).toLowerCase().replace(/[^a-z0-9]+/g, "-")}
          className="text-lg font-semibold text-cyan-400 mt-6 mb-2"
        >
          {line.slice(4)}
        </h3>
      );
      i++;
      continue;
    }

    if (line.startsWith("#### ")) {
      blocks.push(
        <h4 key={`h4-${i}`} className="text-base font-semibold text-slate-200 mt-4 mb-2">
          {line.slice(5)}
        </h4>
      );
      i++;
      continue;
    }

    // Horizontal Rule
    if (line.trim() === "---" || line.trim() === "***") {
      blocks.push(<hr key={`hr-${i}`} className="my-8 border-slate-800" />);
      i++;
      continue;
    }

    // Blockquote
    if (line.startsWith("> ")) {
      const quoteLines: string[] = [];
      while (i < lines.length && lines[i].startsWith("> ")) {
        quoteLines.push(lines[i].slice(2));
        i++;
      }
      blocks.push(
        <blockquote
          key={`quote-${i}`}
          className="my-4 border-l-4 border-cyan-500 bg-cyan-950/20 px-4 py-2 text-sm text-cyan-200/90 rounded-r-lg"
        >
          {quoteLines.map((ql, qIdx) => (
            <p key={qIdx}>{renderInline(ql)}</p>
          ))}
        </blockquote>
      );
      continue;
    }

    // List Items
    if (line.trim().startsWith("- ") || line.trim().startsWith("* ")) {
      const listItems: string[] = [];
      while (i < lines.length && (lines[i].trim().startsWith("- ") || lines[i].trim().startsWith("* "))) {
        listItems.push(lines[i].trim().slice(2));
        i++;
      }
      blocks.push(
        <ul key={`ul-${i}`} className="my-3 space-y-1.5 list-disc list-inside text-sm text-slate-300">
          {listItems.map((li, liIdx) => (
            <li key={liIdx} className="leading-relaxed">
              {renderInline(li)}
            </li>
          ))}
        </ul>
      );
      continue;
    }

    // Numbered List
    if (/^\d+\.\s/.test(line.trim())) {
      const listItems: string[] = [];
      while (i < lines.length && /^\d+\.\s/.test(lines[i].trim())) {
        listItems.push(lines[i].trim().replace(/^\d+\.\s/, ""));
        i++;
      }
      blocks.push(
        <ol key={`ol-${i}`} className="my-3 space-y-1.5 list-decimal list-inside text-sm text-slate-300">
          {listItems.map((li, liIdx) => (
            <li key={liIdx} className="leading-relaxed">
              {renderInline(li)}
            </li>
          ))}
        </ol>
      );
      continue;
    }

    // Empty lines
    if (!line.trim()) {
      i++;
      continue;
    }

    // Regular Paragraph
    blocks.push(
      <p key={`p-${i}`} className="my-3 text-sm leading-relaxed text-slate-300">
        {renderInline(line)}
      </p>
    );
    i++;
  }

  return <div className="space-y-1 text-slate-200">{blocks}</div>;
}

function CodeBlock({ code, language }: { code: string; language: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="my-5 rounded-xl border border-slate-800 bg-slate-950 overflow-hidden shadow-xl">
      <div className="flex items-center justify-between border-b border-slate-800/80 bg-slate-900/80 px-4 py-2 text-xs">
        <div className="flex items-center gap-2 font-mono text-cyan-400">
          <Terminal className="h-3.5 w-3.5" />
          <span>{language.toUpperCase()}</span>
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 rounded px-2 py-1 text-[11px] font-mono text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
          title="Copy code to clipboard"
        >
          {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
          <span>{copied ? "Copied" : "Copy"}</span>
        </button>
      </div>
      <pre className="p-4 text-xs font-mono text-slate-200 overflow-x-auto leading-relaxed scrollbar-thin scrollbar-thumb-slate-800">
        <code>{code}</code>
      </pre>
    </div>
  );
}

