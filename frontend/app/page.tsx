'use client';

import React, { useState } from 'react';
import { Navbar } from '../components/Navbar';
import { MemoryCard } from '../components/MemoryCard';
import { AnswerCard } from '../components/AnswerCard';
import { AddMemoryModal } from '../components/AddMemoryModal';
import { MemoryDetailModal } from '../components/MemoryDetailModal';
import { Search, Loader2, Compass, FileText } from 'lucide-react';
import { getMediaUrl, searchMemories, askRecall, AskResponse, MemoryItem, Citation } from '../lib/api';

export default function HomePage() {
  const [query, setQuery] = useState('');
  const [sourceType, setSourceType] = useState('all');
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [searchResults, setSearchResults] = useState<MemoryItem[]>([]);
  const [answerData, setAnswerData] = useState<AskResponse | null>(null);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [selectedMemory, setSelectedMemory] = useState<MemoryItem | null>(null);

  const handleExecute = async (inputQuery?: string) => {
    const activeQuery = inputQuery || query;
    if (!activeQuery.trim()) return;

    setLoading(true);
    setError(null);
    setAnswerData(null);

    try {
      // Fire both search AND ask in parallel
      const [searchRes, askRes] = await Promise.allSettled([
        searchMemories(activeQuery, {
          top_k: 12,
          alpha: 0.6,
          threshold: 0.45,
          source_type: sourceType === 'all' ? undefined : sourceType,
        }),
        askRecall(activeQuery, {
          top_k: 5,
          threshold: 0.45,
          alpha: 0.6,
          mode: 'hybrid',
        }),
      ]);

      if (searchRes.status === 'fulfilled') {
        setSearchResults(searchRes.value.results);
      } else {
        setError(searchRes.reason?.message || 'Search failed.');
      }

      if (askRes.status === 'fulfilled') {
        setAnswerData(askRes.value);
      }
      // If ask fails (e.g. Groq down), silently skip — search results still show

      setHasSearched(true);
    } catch (err: any) {
      setError(err.message || 'An error occurred during query execution.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleExecute();
    }
  };

  const handleMemoryClick = (memory: MemoryItem) => {
    const mediaUrl = getMediaUrl(memory.media_url || memory.metadata?.media_url);
    if (mediaUrl && (memory.source_type === 'screenshot' || memory.source_type === 'pdf')) {
      window.open(mediaUrl, '_blank', 'noopener,noreferrer');
      return;
    }
    setSelectedMemory(memory);
  };

  const handleCitationClick = (citation: Citation) => {
    // Convert citation to a MemoryItem-like object to open in detail modal
    setSelectedMemory({
      id: citation.id,
      title: citation.title,
      source_type: citation.source_type,
      raw_content: citation.raw_content || '',
      source_url: citation.source_url,
      media_url: citation.media_url || citation.metadata?.media_url,
      metadata: citation.metadata,
      created_at: citation.created_at || citation.metadata?.created_at || new Date().toISOString(),
      chunk_index: 0,
      has_embedding: true,
      hybrid_score: citation.score,
    });
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-900 flex flex-col">
      <Navbar onOpenAddModal={() => setIsAddModalOpen(true)} />

      <main className="flex-1 max-w-4xl w-full mx-auto px-4 py-10 flex flex-col">
        {/* Hero Section */}
        <div className="text-center mb-8">
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900 mb-2">
            Search your memory
          </h1>
          <p className="text-slate-600 text-sm max-w-lg mx-auto font-normal">
            Find saved documents, notes, webpages, and screenshots.
          </p>
        </div>

        {/* Search Bar Container */}
        <div className="bg-white rounded-2xl p-2 border border-slate-200 shadow-sm mb-6">
          <div className="flex items-center gap-2 px-3 py-1.5">
            <Search className="w-5 h-5 text-slate-400 shrink-0" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question or search your memories..."
              className="w-full bg-transparent border-none text-slate-900 placeholder:text-slate-400 text-sm sm:text-base focus:outline-none py-1"
            />
            {query && (
              <button
                onClick={() => setQuery('')}
                className="text-xs text-slate-400 hover:text-slate-600 px-1"
              >
                Clear
              </button>
            )}
            <button
              onClick={() => handleExecute()}
              disabled={loading || !query.trim()}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold bg-gradient-to-r from-purple-600 to-indigo-600 text-white hover:from-purple-700 hover:to-indigo-700 shadow-sm shadow-purple-500/25 transition-all disabled:opacity-50 shrink-0 cursor-pointer"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Search className="w-4 h-4" />
              )}
              <span>{loading ? 'Searching...' : 'Search'}</span>
            </button>
          </div>

          <div className="flex items-center justify-between pt-2 px-3 border-t border-slate-100 text-xs">
            <div className="flex items-center gap-2">
              <label htmlFor="source-filter" className="text-slate-500 font-medium">Search in:</label>
              <select
                id="source-filter"
                value={sourceType}
                onChange={(e) => setSourceType(e.target.value)}
                className="bg-transparent text-slate-700 font-semibold focus:outline-none"
              >
                <option value="all">Everything</option>
                <option value="pdf">PDFs</option>
                <option value="screenshot">Screenshots</option>
                <option value="webpage">Webpages</option>
                <option value="text">Notes</option>
              </select>
            </div>
          </div>
        </div>

        {/* Suggestion Chips */}
        {searchResults.length === 0 && !loading && !error && !hasSearched && (
          <div className="mb-8">
            <div className="flex items-center gap-1.5 text-xs text-slate-500 mb-2 font-medium">
              <Compass className="w-3.5 h-3.5 text-purple-600" />
              <span>Suggested questions:</span>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="text-xs text-slate-500">Search by title, text, or a word visible in an image.</span>
            </div>
          </div>
        )}

        {searchResults.length === 0 && !loading && !error && hasSearched && (
          <div className="rounded-xl border border-slate-200 bg-white p-8 text-center">
            <FileText className="mx-auto mb-2 h-8 w-8 text-slate-300" />
            <p className="text-sm font-semibold text-slate-700">No relevant memory found</p>
            <p className="mt-1 text-xs text-slate-500">Try describing the saved item another way or choose Everything.</p>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs">
            {error}
          </div>
        )}

        {/* ✅ Groq Synthesized Answer Card — shown above results */}
        {answerData && (
          <div className="mb-6">
            <AnswerCard
              data={answerData}
              onSelectCitation={handleCitationClick}
            />
          </div>
        )}

        {/* Results Area */}
        {searchResults.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                Relevant Results ({searchResults.length})
              </h3>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {searchResults.map((item) => (
                <MemoryCard
                  key={item.id}
                  memory={item}
                  onClick={handleMemoryClick}
                  showScore={true}
                />
              ))}
            </div>
          </div>
        )}
      </main>

      {/* Detail Viewer Modal */}
      <MemoryDetailModal
        memory={selectedMemory}
        onClose={() => setSelectedMemory(null)}
      />

      {/* Add Memory Modal */}
      <AddMemoryModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onSuccess={() => setIsAddModalOpen(false)}
      />
    </div>
  );
}
