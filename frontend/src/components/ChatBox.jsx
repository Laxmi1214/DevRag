import { useState } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api';

export default function ChatBox() {
  const [question, setQuestion] = useState('');
  const [limit, setLimit] = useState(5);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  const handleSubmit = async (event) => {
    event.preventDefault();
    const trimmedQuestion = question.trim();

    if (!trimmedQuestion) {
      setError('Enter a question to retrieve relevant chunks.');
      return;
    }

    setIsGenerating(true);
    setError('');
    setResult(null);

    try {
      const response = await fetch(`${API_BASE_URL}/rag/answer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: trimmedQuestion,
          limit,
        }),
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Answer generation failed.');
      }

      setResult(data);
    } catch (retrievalError) {
      setError(retrievalError.message);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <section className="space-y-6">
      <form onSubmit={handleSubmit} className="rounded-lg border border-slate-200 bg-white p-5">
        <div className="flex flex-col gap-4">
          <div>
            <h1 className="text-xl font-semibold">Ask DevRag</h1>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Ask a question to generate a grounded answer from your indexed documentation.
            </p>
          </div>
          <textarea
            value={question}
            onChange={(event) => {
              setQuestion(event.target.value);
              setError('');
            }}
            placeholder="What does the documentation say about installation?"
            rows={4}
            className="min-h-28 resize-y rounded-md border border-slate-300 px-3 py-2 text-sm leading-6 outline-none focus:border-brand focus:ring-2 focus:ring-blue-100"
          />
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            
            <button
              type="submit"
              disabled={isGenerating}
              className="rounded-md bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-400"
            >
              {isGenerating ? 'Generating...' : 'Generate Answer'}
            </button>
          </div>
        </div>
      </form>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-4">
          <div className="rounded-lg border border-slate-200 bg-white p-5">
            <p className="text-sm font-semibold text-slate-500">Question</p>
            <p className="mt-1 text-base font-semibold text-slate-900">{result.question}</p>
            <div className="mt-5 rounded-md bg-slate-950 p-4 text-sm leading-6 text-slate-100">
              <pre className="whitespace-pre-wrap font-sans">{result.answer}</pre>
            </div>
           
            {result.active_source && (
              <p className="mt-3 text-xs text-slate-500">
                Active source: {result.active_source.source_name} ({result.active_source.source_type})
              </p>
            )}
          </div>

        </div>
      )}
    </section>
  );
}
