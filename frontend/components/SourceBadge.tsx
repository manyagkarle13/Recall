'use client';

import React from 'react';
import { FileText, Globe, Image as ImageIcon, FileCode } from 'lucide-react';

interface SourceBadgeProps {
  sourceType: string;
  className?: string;
}

export function SourceBadge({ sourceType, className = '' }: SourceBadgeProps) {
  switch (sourceType.toLowerCase()) {
    case 'webpage':
      return (
        <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200 ${className}`}>
          <Globe className="w-3 h-3" />
          Web
        </span>
      );
    case 'screenshot':
      return (
        <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-50 text-purple-700 border border-purple-200 ${className}`}>
          <ImageIcon className="w-3 h-3" />
          Screenshot
        </span>
      );
    case 'pdf':
      return (
        <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 ${className}`}>
          <FileCode className="w-3 h-3" />
          PDF
        </span>
      );
    case 'text':
    default:
      return (
        <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200 ${className}`}>
          <FileText className="w-3 h-3" />
          Note
        </span>
      );
  }
}
