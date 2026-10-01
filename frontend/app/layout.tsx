import type { Metadata } from 'next';
import './globals.css';
import { AuthGate } from '../components/AuthGate';

export const metadata: Metadata = {
  title: 'Recall — Personal AI Memory System',
  description: 'Grounded semantic retrieval and question-answering with fine-tuned embeddings & Groq LLaMA 3.1',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#090d16] text-slate-100 antialiased selection:bg-indigo-500 selection:text-white">
        <AuthGate>{children}</AuthGate>
      </body>
    </html>
  );
}
