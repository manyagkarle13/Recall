'use client';

import React, { useState } from 'react';
import { X, Upload, FileText, Globe, AlertCircle, Loader2, Image as ImageIcon } from 'lucide-react';
import { createMemory } from '../lib/api';

interface AddMemoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function AddMemoryModal({ isOpen, onClose, onSuccess }: AddMemoryModalProps) {
  const [tab, setTab] = useState<'text' | 'file'>('text');
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (tab === 'text') {
        if (!content.trim()) {
          throw new Error('Please enter some memory content.');
        }
        await createMemory({
          title: title.trim() || undefined,
          raw_content: content.trim(),
          source_type: sourceUrl ? 'webpage' : 'text',
          source_url: sourceUrl.trim() || undefined,
        });
      } else {
        if (!file) {
          throw new Error('Please select a file to upload.');
        }
        await createMemory({
          title: title.trim() || undefined,
          source_url: sourceUrl.trim() || undefined,
          file: file,
        });
      }

      onSuccess();
      onClose();
      // Reset form
      setTitle('');
      setContent('');
      setSourceUrl('');
      setFile(null);
    } catch (err: any) {
      setError(err.message || 'Failed to save memory');
    } finally {
      setLoading(false);
    }
  };

  const isImageFile = file && /\.(png|jpe?g|webp|bmp)$/i.test(file.name);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white w-full max-w-lg rounded-2xl p-6 border border-slate-200 shadow-2xl relative">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-bold text-slate-900">Save New Memory</h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-700 p-1.5 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab switch */}
        <div className="flex gap-2 p-1 bg-slate-100 rounded-xl mb-5">
          <button
            type="button"
            onClick={() => setTab('text')}
            className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-semibold transition-all ${
              tab === 'text'
                ? 'bg-white text-purple-700 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <FileText className="w-4 h-4" />
            Paste Text Note
          </button>
          <button
            type="button"
            onClick={() => setTab('file')}
            className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-semibold transition-all ${
              tab === 'file'
                ? 'bg-white text-purple-700 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Upload className="w-4 h-4" />
            Upload Document / Image
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-red-500" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Title (Optional)
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Major Project Architecture"
              className="w-full px-3.5 py-2 bg-slate-50 border border-slate-300 rounded-xl text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:bg-white focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Source URL (Optional)
            </label>
            <div className="relative">
              <input
                type="url"
                value={sourceUrl}
                onChange={(e) => setSourceUrl(e.target.value)}
                placeholder="https://..."
                className="w-full pl-9 pr-3.5 py-2 bg-slate-50 border border-slate-300 rounded-xl text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:bg-white focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20"
              />
              <Globe className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            </div>
          </div>

          {tab === 'text' ? (
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Content *
              </label>
              <textarea
                rows={5}
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Write or paste your note here... (Documents over 500 tokens will be chunked automatically)"
                required
                className="w-full px-3.5 py-2 bg-slate-50 border border-slate-300 rounded-xl text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:bg-white focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20"
              />
            </div>
          ) : (
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Upload File or Image *
              </label>
              <div className="border-2 border-dashed border-slate-300 hover:border-purple-500 rounded-xl p-6 text-center cursor-pointer transition-colors bg-slate-50 hover:bg-purple-50/40">
                <input
                  type="file"
                  id="file-upload"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="hidden"
                  accept=".txt,.md,.pdf,.png,.jpg,.jpeg,.webp"
                />
                <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center">
                  {isImageFile ? (
                    <ImageIcon className="w-8 h-8 text-purple-600 mb-2" />
                  ) : (
                    <Upload className="w-8 h-8 text-purple-600 mb-2" />
                  )}
                  <p className="text-sm font-semibold text-slate-800">
                    {file ? file.name : 'Click to select or drag and drop'}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    Supports .txt, .md, .pdf documents & .png, .jpg, .jpeg images (OCR auto-extracted)
                  </p>
                  {isImageFile && (
                    <span className="mt-2 text-[11px] font-semibold text-purple-700 bg-purple-100 px-2 py-0.5 rounded-full">
                      Image detected — text will be extracted via OCR
                    </span>
                  )}
                </label>
              </div>
            </div>
          )}

          <div className="flex justify-end gap-3 pt-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-2 px-5 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-purple-600 to-indigo-600 text-white hover:from-purple-700 hover:to-indigo-700 shadow-sm shadow-purple-500/20 transition-all disabled:opacity-50 cursor-pointer"
            >
              {loading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              {loading ? 'Embedding & Saving...' : 'Save Memory'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
