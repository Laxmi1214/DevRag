import { Link } from 'react-router-dom';

export default function Home() {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-8">
      <div className="max-w-3xl">
        <p className="text-sm font-semibold uppercase tracking-wide text-brand">DevRag</p>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight text-ink">
          AI-powered documentation retrieval for modern developers.
        </h1>
        <p className="mt-4 text-base leading-7 text-slate-600">
          A multi-source AI documentation assistant that extracts knowledge from PDFs, images, and documentation websites using OCR, semantic retrieval, and Retrieval-Augmented Generation.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            to="/upload"
            className="rounded-md bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
          >
            Upload docs
          </Link>
          <Link
            to="/chat"
            className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100"
          >
            Open chat
          </Link>
        </div>
      </div>
    </section>
  );
}
