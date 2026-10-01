'use client';

import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Sparkles, Copy, Check, ShieldCheck, ShieldAlert, Cpu } from 'lucide-react';
import { AskResponse, Citation } from '../lib/api';

interface AnswerCardProps {
  data: AskResponse;
  onSelectCitation?: (citation: Citation) => void;
}

export function AnswerCard({ data, onSelectCitation }: AnswerCardProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(data.answer);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Clean raw LLM text into standardized Markdown and inline citation links
  const processMarkdownText = (text: string): string => {
    if (!text) return '';
    let formatted = text;

    // Convert bullet symbols like `^ ` or `• ` at the start of lines to `* `
    formatted = formatted.replace(/^[ \t]*[\^•][ \t]+/gm, '* ');

    // Convert [1], [2] to Markdown citation links [#citation-1]
    formatted = formatted.replace(/\[(\d+)\]/g, '[$1](#citation-$1)');

    return formatted;
  };

  const formattedAnswerText = processMarkdownText(data.answer);

  return (
    <div className="bg-white rounded-2xl p-6 border border-purple-200 shadow-sm relative overflow-hidden transition-all">
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-purple-500 via-indigo-500 to-purple-600" />

      {/* Header bar */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-purple-50 border border-purple-200 flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-purple-600" />
          </div>
          <span className="font-semibold text-sm text-slate-900">Synthesized Answer</span>
          <span className="flex items-center gap-1 text-[11px] font-medium text-purple-700 bg-purple-50 px-2 py-0.5 rounded-full border border-purple-200">
            <Cpu className="w-3 h-3 text-purple-600" />
            {data.model.replace('groq/', '')}
          </span>
        </div>

        <div className="flex items-center gap-3">
          {data.has_relevant_memories ? (
            <span className="flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
              <ShieldCheck className="w-3.5 h-3.5" />
              Grounded ({Math.round(data.top_score * 100)}% match)
            </span>
          ) : (
            <span className="flex items-center gap-1 text-[11px] font-semibold text-amber-700 bg-amber-50 px-2.5 py-0.5 rounded-full border border-amber-200">
              <ShieldAlert className="w-3.5 h-3.5" />
              No Direct Match
            </span>
          )}

          <button
            onClick={handleCopy}
            className="p-1.5 rounded-lg text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition-colors"
            title="Copy answer"
          >
            {copied ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Synthesized Text (Rendered Markdown) */}
      <div className="text-slate-800 text-sm leading-relaxed mb-5">
        <ReactMarkdown
          components={{
            p: ({ children }) => <p className="mb-3 leading-relaxed text-slate-800 text-sm">{children}</p>,
            strong: ({ children }) => <strong className="font-semibold text-slate-900">{children}</strong>,
            em: ({ children }) => <em className="italic text-slate-800">{children}</em>,
            ul: ({ children }) => <ul className="list-disc pl-5 my-2.5 space-y-1.5 text-slate-800 text-sm">{children}</ul>,
            ol: ({ children }) => <ol className="list-decimal pl-5 my-2.5 space-y-1.5 text-slate-800 text-sm">{children}</ol>,
            li: ({ children }) => <li className="leading-relaxed">{children}</li>,
            h1: ({ children }) => <h1 className="text-base font-bold text-slate-900 mt-4 mb-2">{children}</h1>,
            h2: ({ children }) => <h2 className="text-sm font-bold text-slate-900 mt-3 mb-1.5">{children}</h2>,
            h3: ({ children }) => <h3 className="text-sm font-semibold text-slate-900 mt-2 mb-1">{children}</h3>,
            code: ({ children }) => (
              <code className="bg-purple-50 text-purple-800 font-mono text-[12px] px-1.5 py-0.5 rounded border border-purple-200/60">
                {children}
              </code>
            ),
            blockquote: ({ children }) => (
              <blockquote className="border-l-4 border-purple-300 pl-3 my-2 text-slate-600 italic">
                {children}
              </blockquote>
            ),
            a: ({ href, children }) => {
              if (href?.startsWith('#citation-')) {
                const citationNum = parseInt(href.replace('#citation-', ''), 10);
                const citation = data.citations?.[citationNum - 1];
                return (
                  <button
                    type="button"
                    onClick={() => citation && onSelectCitation?.(citation)}
                    className="inline-flex items-center gap-1 font-bold text-[11px] text-purple-700 bg-purple-100/90 hover:bg-purple-200 border border-purple-300 rounded px-1.5 py-0.5 mx-0.5 transition-all cursor-pointer shadow-xs hover:scale-105 active:scale-95"
                    title={citation ? `Click to view source: ${citation.title}` : `Citation [${citationNum}]`}
                  >
                    [{children}]
                  </button>
                );
              }
              return (
                <a href={href} target="_blank" rel="noopener noreferrer" className="text-purple-600 underline font-medium hover:text-purple-800">
                  {children}
                </a>
              );
            },
          }}
        >
          {formattedAnswerText}
        </ReactMarkdown>
      </div>

      {/* Citations Footer */}
      {data.citations && data.citations.length > 0 && (
        <div className="pt-4 border-t border-slate-100">
          <div className="text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2.5">
            Source Citations ({data.citations.length}) — Click to inspect document / image:
          </div>
          <div className="flex flex-wrap gap-2">
            {data.citations.map((c, idx) => (
              <button
                key={c.id || idx}
                onClick={() => onSelectCitation && onSelectCitation(c)}
                className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-50 hover:bg-purple-50 border border-slate-200 hover:border-purple-300 text-xs text-slate-700 transition-colors group cursor-pointer text-left"
              >
                <span className="font-semibold text-purple-700">[{idx + 1}]</span>
                <span className="font-medium group-hover:text-purple-900 truncate max-w-[220px]">
                  {c.title}
                </span>
                <span className="text-[10px] text-slate-500 bg-white px-1.5 py-0.5 rounded border border-slate-200">
                  {Math.round(c.score * 100)}%
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

