'use client';

import React, { useState, useEffect } from 'react';
import { Navbar } from '../../components/Navbar';
import { MemoryCard } from '../../components/MemoryCard';
import { AddMemoryModal } from '../../components/AddMemoryModal';
import { MemoryDetailModal } from '../../components/MemoryDetailModal';
import { getMediaUrl, getMemories, deleteMemory, MemoryItem } from '../../lib/api';
import { Database, Filter, Loader2, Plus } from 'lucide-react';

const FILTER_TABS = [
  { id: 'all', label: 'All Items' },
  { id: 'text', label: 'Notes' },
  { id: 'webpage', label: 'Webpages' },
  { id: 'screenshot', label: 'Screenshots' },
  { id: 'pdf', label: 'PDFs' },
];

export default function MemoriesPage() {
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [activeTab, setActiveTab] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState<number>(1);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [selectedMemory, setSelectedMemory] = useState<MemoryItem | null>(null);

  const fetchMemoriesList = async (pageNum = 1, filterType = activeTab, search = searchQuery) => {
    setLoading(true);
    setError(null);
    try {
      const res = await getMemories({
        page: pageNum,
        source_type: filterType === 'all' ? undefined : filterType,
        q: search.trim() || undefined,
      });
      setMemories(res.results);
      setTotalCount(res.count);
      setPage(pageNum);
    } catch (err: any) {
      setError(err.message || 'Failed to load memories');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMemoriesList(1, activeTab, searchQuery);
  }, [activeTab]);

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this memory?')) return;
    try {
      await deleteMemory(id);
      fetchMemoriesList(page, activeTab, searchQuery);
    } catch (err: any) {
      alert(err.message || 'Failed to delete');
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

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchMemoriesList(1, activeTab, searchQuery);
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-900 flex flex-col">
      <Navbar onOpenAddModal={() => setIsAddModalOpen(true)} />

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 py-8">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900 flex items-center gap-2">
              <Database className="w-6 h-6 text-purple-600" />
              <span>Saved Memories</span>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-purple-100 text-purple-700 border border-purple-200">
                {totalCount} items
              </span>
            </h1>
            <p className="text-xs text-slate-500 mt-1 font-normal">
              Click on any document or screenshot card below to open the full reader and preview image.
            </p>
          </div>

          <button
            onClick={() => setIsAddModalOpen(true)}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-purple-600 to-indigo-600 text-white hover:from-purple-700 hover:to-indigo-700 shadow-sm shadow-purple-500/20 transition-all cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Add Memory</span>
          </button>
        </div>

        {/* Filter tabs & Search */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 mb-6">
          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl border border-slate-200 overflow-x-auto">
            {FILTER_TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'bg-white text-purple-700 shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <form onSubmit={handleSearchSubmit} className="relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Filter memory titles..."
              className="w-full sm:w-64 px-3.5 py-1.5 bg-white border border-slate-200 rounded-xl text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20"
            />
          </form>
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex flex-col items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-purple-600 animate-spin mb-3" />
            <p className="text-xs text-slate-500 font-medium">Loading memories...</p>
          </div>
        ) : memories.length === 0 ? (
          <div className="text-center py-20 bg-white rounded-2xl border border-slate-200 p-8 shadow-sm">
            <Database className="w-10 h-10 text-slate-400 mx-auto mb-3" />
            <h3 className="text-sm font-bold text-slate-800 mb-1">No memories found</h3>
            <p className="text-xs text-slate-500 mb-4 font-normal">
              {activeTab !== 'all'
                ? `No items found for filter '${activeTab}'.`
                : 'Your memory catalog is currently empty. Add your first note or document!'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {memories.map((m) => (
              <MemoryCard
                key={m.id}
                memory={m}
                onClick={handleMemoryClick}
                onDelete={handleDelete}
              />
            ))}
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
        onSuccess={() => {
          setIsAddModalOpen(false);
          fetchMemoriesList(page, activeTab, searchQuery);
        }}
      />
    </div>
  );
}
