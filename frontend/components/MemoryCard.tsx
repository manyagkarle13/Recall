'use client';

import React from 'react';
import { SourceBadge } from './SourceBadge';
import { ExternalLink, Trash2, Eye } from 'lucide-react';
import { getMediaUrl, MemoryItem } from '../lib/api';

interface MemoryCardProps {
  memory: MemoryItem;
  onDelete?: (id: string) => void;
  onClick?: (memory: MemoryItem) => void;
  showScore?: boolean;
}

export function MemoryCard({ memory, onDelete, onClick, showScore = false }: MemoryCardProps) {
  const score = memory.hybrid_score ?? memory.vector_score;
  const mediaUrl = getMediaUrl(memory.media_url || memory.metadata?.media_url);
  const isImage = memory.source_type === 'screenshot';
  const isFile = isImage || memory.source_type === 'pdf';

  return (
    <div
      onClick={() => onClick && onClick(memory)}
      className={`bg-white rounded-xl p-4 border border-slate-200 hover:border-purple-300 hover:shadow-md transition-all flex flex-col justify-between group ${
        onClick ? 'cursor-pointer' : ''
      }`}
    >
      <div>
        {/* Header: Badge & Date */}
        <div className="flex items-center justify-between gap-2 mb-2">
          <SourceBadge sourceType={memory.source_type} />

          <div className="flex items-center gap-2">
            {showScore && score !== undefined && score !== null && (
              <span className="text-[11px] font-bold text-purple-700 bg-purple-50 px-2 py-0.5 rounded-md border border-purple-200">
                {Math.round(score * 100)}% match
              </span>
            )}
            <span className="text-[11px] text-slate-400">
              {new Date(memory.created_at).toLocaleDateString(undefined, {
                month: 'short',
                day: 'numeric',
              })}
            </span>
          </div>
        </div>

        {/* Title */}
        <h3 className="font-bold text-sm text-slate-900 mb-1.5 line-clamp-1 group-hover:text-purple-700 transition-colors">
          {memory.title || 'Untitled Memory'}
        </h3>

        {isImage && mediaUrl ? (
          <div className="mb-3 overflow-hidden rounded-lg border border-slate-200 bg-slate-100 aspect-[16/9]">
            <img src={mediaUrl} alt={memory.title || 'Screenshot'} className="h-full w-full object-contain" />
          </div>
        ) : (
          <p className="text-xs text-slate-600 leading-relaxed line-clamp-3 mb-3 font-normal">
            {isFile ? 'Open the original file to view it.' : memory.raw_content}
          </p>
        )}
      </div>

      {/* Footer info & actions */}
      <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
        <div className="flex items-center gap-2 text-purple-600 group-hover:text-purple-700 font-medium">
          <Eye className="w-3.5 h-3.5" />
          <span>{isFile ? 'Open original file' : 'Click to view'}</span>
        </div>

        <div className="flex items-center gap-2">
          {memory.source_url && (
            <a
              href={memory.source_url}
              target="_blank"
              rel="noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="flex items-center gap-1 text-purple-600 hover:text-purple-800 transition-colors font-medium truncate max-w-[120px]"
            >
              <ExternalLink className="w-3 h-3" /> Link
            </a>
          )}

          {onDelete && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete(memory.id);
              }}
              className="text-slate-400 hover:text-red-600 p-1 rounded-md hover:bg-red-50 transition-colors"
              title="Delete memory"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
