'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { BrainCircuit, Search, Database, Plus, Sparkles } from 'lucide-react';
import { LogOut } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { logout } from '../lib/api';

interface NavbarProps {
  onOpenAddModal?: () => void;
}

export function Navbar({ onOpenAddModal }: NavbarProps) {
  const pathname = usePathname();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.replace('/login');
  };

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200 bg-white/90 backdrop-blur-md">
      <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        {/* Logo & Brand */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-purple-600 to-indigo-600 flex items-center justify-center shadow-md shadow-purple-500/20 group-hover:scale-105 transition-transform">
            <BrainCircuit className="w-5 h-5 text-white" />
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-lg text-slate-900 tracking-tight">Recall</span>
              <span className="text-[10px] uppercase font-bold tracking-widest px-1.5 py-0.5 bg-purple-100 text-purple-700 rounded-md border border-purple-200">
                AI Memory
              </span>
            </div>
            <span className="text-[11px] text-slate-500 -mt-0.5">Semantic Hybrid Retrieval</span>
          </div>
        </Link>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl border border-slate-200">
          <Link
            href="/"
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
              pathname === '/'
                ? 'bg-white text-purple-700 shadow-sm font-semibold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Search className="w-3.5 h-3.5" />
            <span>Ask & Search</span>
          </Link>
          <Link
            href="/memories"
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
              pathname === '/memories'
                ? 'bg-white text-purple-700 shadow-sm font-semibold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Database className="w-3.5 h-3.5" />
            <span>Memories</span>
          </Link>
        </nav>

        {/* Action Button */}
        <div className="flex items-center gap-2">
          {onOpenAddModal && (
            <button
              onClick={onOpenAddModal}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-purple-600 to-indigo-600 text-white hover:from-purple-700 hover:to-indigo-700 shadow-sm shadow-purple-500/20 transition-all hover:scale-[1.02] active:scale-[0.98]"
            >
              <Plus className="w-4 h-4" />
              <span>Add Memory</span>
            </button>
          )}
          <button onClick={handleLogout} title="Log out" className="rounded-xl p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-900">
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
