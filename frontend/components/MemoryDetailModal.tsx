'use client';

import React, { useState } from 'react';
import { X, Copy, Check, ExternalLink, Calendar, FileText, Download } from 'lucide-react';
import { SourceBadge } from './SourceBadge';
import { getMediaUrl, MemoryItem } from '../lib/api';

interface MemoryDetailModalProps {
  memory: MemoryItem | null;
  onClose: () => void;
}

export function MemoryDetailModal({ memory, onClose }: MemoryDetailModalProps) {
  const [copied, setCopied] = useState(false);
  const [imgError, setImgError] = useState(false);

  if (!memory) return null;

  const score = memory.hybrid_score ?? memory.vector_score;

  // Build the media URL for images
  const rawMediaUrl = memory.media_url || memory.metadata?.media_url;
  const fullMediaUrl = getMediaUrl(rawMediaUrl);

  // Build the PDF URL  
  const rawPdfUrl = memory.metadata?.media_url;
  const fullPdfUrl = memory.source_type === 'pdf' ? getMediaUrl(rawPdfUrl) : null;

  const isImage = memory.source_type === 'screenshot';
  const isPdf = memory.source_type === 'pdf';

  const handleCopy = () => {
    navigator.clipboard.writeText(memory.raw_content || '');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) onClose();
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-slate-900/60 backdrop-blur-sm"
      onClick={handleBackdropClick}
    >
      <div className="bg-white w-full max-w-3xl max-h-[92vh] rounded-2xl border border-slate-200 shadow-2xl flex flex-col overflow-hidden">

        {/* Header */}
        <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between gap-4 flex-shrink-0">
          <div className="flex items-center gap-2 flex-wrap min-w-0">
            <SourceBadge sourceType={memory.source_type} />
            {score !== undefined && score !== null && (
              <span className="text-[11px] font-bold text-purple-700 bg-purple-100 px-2 py-0.5 rounded-full border border-purple-200">
                {Math.round(score * 100)}% match
              </span>
            )}
            <span className="text-xs text-slate-400 flex items-center gap-1 font-normal">
              <Calendar className="w-3 h-3" />
              {memory.created_at && !isNaN(Date.parse(memory.created_at))
                ? new Date(memory.created_at).toLocaleDateString(undefined, {
                    year: 'numeric', month: 'short', day: 'numeric',
                  })
                : 'Saved Memory'}
            </span>
          </div>
          <button
            onClick={onClose}
            className="flex-shrink-0 text-slate-400 hover:text-slate-700 p-1.5 rounded-xl hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Title */}
        <div className="px-5 pt-3 pb-2 flex-shrink-0">
          <h2 className="text-base font-bold text-slate-900 truncate">
            {memory.title || 'Untitled Memory'}
          </h2>
        </div>

        {/* Scrollable body */}
        <div className="flex-1 overflow-y-auto px-5 pb-5 space-y-4">

          {/* === IMAGE VIEW: Full image for screenshots === */}
          {isImage && fullMediaUrl && !imgError && (
            <div className="relative rounded-xl overflow-hidden border border-slate-200 bg-slate-100 flex items-center justify-center min-h-[200px]">
              <img
                src={fullMediaUrl}
                alt={memory.title || 'Screenshot'}
                className="max-w-full max-h-[60vh] object-contain"
                onError={() => setImgError(true)}
              />
              <a
                href={fullMediaUrl}
                target="_blank"
                rel="noreferrer"
                className="absolute top-3 right-3 flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/90 hover:bg-white text-xs font-semibold text-slate-700 shadow-sm border border-slate-200 hover:border-purple-300 transition-all"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                Open Full Size
              </a>
            </div>
          )}

          {/* Image error fallback */}
          {isImage && (imgError || !fullMediaUrl) && (
            <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 flex flex-col items-center justify-center py-8 gap-2 text-slate-400">
              <FileText className="w-8 h-8 text-purple-400" />
              <p className="text-xs font-medium text-slate-600">Screenshot Memory & OCR Extracted Text</p>
            </div>
          )}

          {/* === PDF VIEW: Open PDF button + text content === */}
          {isPdf && (
            <div className="space-y-3">
              {fullPdfUrl ? (
                <a
                  href={fullPdfUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center justify-center gap-2 w-full py-3 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 text-white text-sm font-semibold hover:from-purple-700 hover:to-indigo-700 transition-all shadow-sm shadow-purple-500/20"
                >
                  <ExternalLink className="w-4 h-4" />
                  Open PDF in Browser
                </a>
              ) : (
                <div className="flex items-center justify-center gap-2 w-full py-3 rounded-xl bg-slate-100 text-slate-400 text-sm font-medium border border-dashed border-slate-300">
                  <FileText className="w-4 h-4" />
                  Re-upload PDF to enable direct opening
                </div>
              )}
            </div>
          )}

          {/* === CONTENT: Text content (Hidden for image/screenshot memories) === */}
          {!isImage && memory.raw_content && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-600 flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-purple-500" />
                  {isPdf ? 'Extracted Text' : 'Memory Content'}
                </span>
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-1 text-xs font-semibold text-purple-700 bg-purple-50 hover:bg-purple-100 border border-purple-200 px-2.5 py-1 rounded-lg transition-colors"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copied ? 'Copied' : 'Copy'}</span>
                </button>
              </div>
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-xs text-slate-800 leading-relaxed max-h-64 overflow-y-auto select-text whitespace-pre-wrap">
                {memory.raw_content}
              </div>
            </div>
          )}

          {/* Source URL */}
          {memory.source_url && (
            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-400 font-semibold uppercase text-[10px]">Source</span>
              <a
                href={memory.source_url}
                target="_blank"
                rel="noreferrer"
                className="text-purple-600 hover:underline truncate font-medium"
              >
                {memory.source_url}
              </a>
            </div>
          )}

          {/* Quick stats */}
          <div className="flex items-center gap-4 text-[11px] text-slate-400 pt-1 border-t border-slate-100">
            {memory.raw_content && (
              <span>{memory.raw_content.length.toLocaleString()} chars</span>
            )}
            {memory.metadata?.num_pages && (
              <span>{memory.metadata.num_pages} pages</span>
            )}
            {memory.metadata?.image_dimensions && (
              <span>{memory.metadata.image_dimensions}</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
