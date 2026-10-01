'use client';

import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

export function AuthGate({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [ready, setReady] = useState(pathname === '/login');

  useEffect(() => {
    if (pathname === '/login') {
      setReady(true);
      return;
    }

    if (!localStorage.getItem('recall_token')) {
      router.replace('/login');
      return;
    }
    setReady(true);
  }, [pathname, router]);

  if (!ready) {
    return <div className="min-h-screen bg-[#f8fafc]" />;
  }

  return children;
}