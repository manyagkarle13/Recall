'use client';

import { FormEvent, useState } from 'react';
import { useRouter } from 'next/navigation';
import { BrainCircuit, Loader2, LockKeyhole, UserRound } from 'lucide-react';
import { login, register } from '../../lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [isRegistering, setIsRegistering] = useState(false);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (isRegistering) {
        await register(username.trim(), email.trim(), password);
      } else {
        await login(username.trim(), password);
      }
      router.replace('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to continue.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#f8fafc] flex items-center justify-center px-4 py-10">
      <section className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-xl">
        <div className="mb-8 flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-tr from-purple-600 to-indigo-600 shadow-md">
            <BrainCircuit className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-extrabold text-slate-900">Recall</h1>
            <p className="text-xs text-slate-500">Your private memory space</p>
          </div>
        </div>

        <h2 className="text-2xl font-bold text-slate-900">{isRegistering ? 'Create your account' : 'Welcome back'}</h2>
        <p className="mt-1 text-sm text-slate-500">{isRegistering ? 'Start saving memories by meaning.' : 'Sign in to access your saved memories.'}</p>

        {error && <div className="mt-5 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <label className="block text-sm font-semibold text-slate-700">
            Username
            <div className="relative mt-1.5">
              <UserRound className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
              <input required value={username} onChange={(event) => setUsername(event.target.value)} className="w-full rounded-xl border border-slate-300 bg-slate-50 py-2.5 pl-9 pr-3 text-sm text-slate-900 outline-none focus:border-purple-500 focus:bg-white" />
            </div>
          </label>

          {isRegistering && (
            <label className="block text-sm font-semibold text-slate-700">
              Email (optional)
              <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} className="mt-1.5 w-full rounded-xl border border-slate-300 bg-slate-50 px-3 py-2.5 text-sm text-slate-900 outline-none focus:border-purple-500 focus:bg-white" />
            </label>
          )}

          <label className="block text-sm font-semibold text-slate-700">
            Password
            <div className="relative mt-1.5">
              <LockKeyhole className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
              <input required type="password" minLength={8} value={password} onChange={(event) => setPassword(event.target.value)} className="w-full rounded-xl border border-slate-300 bg-slate-50 py-2.5 pl-9 pr-3 text-sm text-slate-900 outline-none focus:border-purple-500 focus:bg-white" />
            </div>
          </label>

          <button disabled={loading} className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 py-3 text-sm font-semibold text-white shadow-md disabled:opacity-60">
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
            {isRegistering ? 'Create account' : 'Log in'}
          </button>
        </form>

        <button onClick={() => { setIsRegistering(!isRegistering); setError(''); }} className="mt-5 w-full text-sm font-semibold text-purple-700 hover:text-purple-900">
          {isRegistering ? 'Already have an account? Log in' : 'New to Recall? Create an account'}
        </button>
      </section>
    </main>
  );
}