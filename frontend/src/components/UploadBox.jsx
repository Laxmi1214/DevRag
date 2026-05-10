import { useState } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api';

const uploadSections = {
  pdf: {
    title: 'Upload PDF documentation',
    description: 'Drop a PDF here or choose one from your machine.',
    accept: 'application/pdf,.pdf',
    endpoint: '/upload/pdf',
    buttonLabel: 'Select PDF',
    loadingLabel: 'Extracting...',
    allowed: ['application/pdf'],
    extensions: ['.pdf'],
    invalidMessage: 'Please upload a PDF file.',
  },
  image: {
    title: 'Upload image for OCR',
    description: 'Upload screenshots, scanned notes, or technical diagrams to extract searchable text using OCR.',
    accept: 'image/png,image/jpeg,.png,.jpg,.jpeg',
    endpoint: '/upload/image',
    buttonLabel: 'Select Image',
    loadingLabel: 'Running OCR...',
    allowed: ['image/png', 'image/jpeg', 'image/jpg'],
    extensions: ['.png', '.jpg', '.jpeg'],
    invalidMessage: 'Please upload a PNG or JPG image.',
  },
};

const initialState = {
  fileName: '',
  isDragging: false,
  isUploading: false,
  error: '',
  result: null,
};

export default function UploadBox() {
  const [uploads, setUploads] = useState({
    pdf: initialState,
    image: initialState,
  });
  const [urlUpload, setUrlUpload] = useState({
    url: '',
    isSubmitting: false,
    error: '',
    result: null,
  });

  const updateUpload = (type, nextState) => {
    setUploads((current) => ({
      ...current,
      [type]: {
        ...current[type],
        ...nextState,
      },
    }));
  };

  const uploadFile = async (type, file) => {
    if (!file) return;

    const config = uploadSections[type];
    const lowerName = file.name.toLowerCase();
    const hasAllowedExtension = config.extensions.some((extension) => lowerName.endsWith(extension));
    const hasAllowedType = config.allowed.includes(file.type);

    if (!hasAllowedType && !hasAllowedExtension) {
      updateUpload(type, { error: config.invalidMessage, result: null });
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    updateUpload(type, {
      fileName: file.name,
      error: '',
      result: null,
      isUploading: true,
    });

    try {
      const response = await fetch(`${API_BASE_URL}${config.endpoint}`, {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Upload failed.');
      }

      updateUpload(type, { result: data });
    } catch (uploadError) {
      updateUpload(type, { error: uploadError.message });
    } finally {
      updateUpload(type, { isUploading: false });
    }
  };

  const handleDrop = (type, event) => {
    event.preventDefault();
    updateUpload(type, { isDragging: false });
    uploadFile(type, event.dataTransfer.files?.[0]);
  };

  const submitUrl = async (event) => {
    event.preventDefault();
    const trimmedUrl = urlUpload.url.trim();

    if (!trimmedUrl) {
      setUrlUpload((current) => ({ ...current, error: 'Please enter a documentation URL.' }));
      return;
    }

    setUrlUpload((current) => ({
      ...current,
      isSubmitting: true,
      error: '',
      result: null,
    }));

    try {
      const response = await fetch(`${API_BASE_URL}/upload/url`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: trimmedUrl }),
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'URL ingestion failed.');
      }

      setUrlUpload((current) => ({ ...current, result: data }));
    } catch (submitError) {
      setUrlUpload((current) => ({ ...current, error: submitError.message }));
    } finally {
      setUrlUpload((current) => ({ ...current, isSubmitting: false }));
    }
  };

  return (
    <section className="space-y-6">
      <UrlPanel state={urlUpload} onChange={setUrlUpload} onSubmit={submitUrl} />
      <UploadPanel
        type="pdf"
        state={uploads.pdf}
        onDrop={handleDrop}
        onUpload={uploadFile}
        onUpdate={updateUpload}
      />
      <UploadPanel
        type="image"
        state={uploads.image}
        onDrop={handleDrop}
        onUpload={uploadFile}
        onUpdate={updateUpload}
      />
    </section>
  );
}

function UrlPanel({ state, onChange, onSubmit }) {
  return (
    <div className="space-y-4">
      <form onSubmit={onSubmit} className="rounded-lg border border-slate-200 bg-white p-6">
        <div className="max-w-3xl">
          <h1 className="text-2xl font-semibold tracking-tight">Connect Technical Documentation</h1>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            Crawl and index technical documentation websites to enable grounded AI retrieval and semantic search.
          </p>
          <div className="mt-5 flex flex-col gap-3 sm:flex-row">
            <input
              type="url"
              value={state.url}
              placeholder="Paste documentation URL (eg: https://docs.example.com/)"
              className="min-w-0 flex-1 rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-brand focus:ring-2 focus:ring-blue-100"
              disabled={state.isSubmitting}
              onChange={(event) =>
                onChange((current) => ({
                  ...current,
                  url: event.target.value,
                  error: '',
                }))
              }
            />
            <button
              type="submit"
              disabled={state.isSubmitting}
              className="rounded-md bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-400"
            >
              {state.isSubmitting ? 'Crawling...' : 'Ingest URL'}
            </button>
          </div>
        </div>
      </form>

      {state.error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
          {state.error}
        </div>
      )}

      {state.result && <PreviewCard result={state.result} />}
    </div>
  );
}

function UploadPanel({ type, state, onDrop, onUpload, onUpdate }) {
  const config = uploadSections[type];

  return (
    <div className="space-y-4">
      <div
        onDragOver={(event) => {
          event.preventDefault();
          onUpdate(type, { isDragging: true });
        }}
        onDragLeave={() => onUpdate(type, { isDragging: false })}
        onDrop={(event) => onDrop(type, event)}
        className={[
          'rounded-lg border border-dashed bg-white p-8 text-center transition',
          state.isDragging ? 'border-brand bg-blue-50' : 'border-slate-300',
        ].join(' ')}
      >
        <div className="mx-auto max-w-lg">
          <h1 className="text-2xl font-semibold tracking-tight">{config.title}</h1>
          <p className="mt-3 text-sm leading-6 text-slate-600">{config.description}</p>
          <label className="mt-6 inline-flex cursor-pointer rounded-md bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700">
            {state.isUploading ? config.loadingLabel : config.buttonLabel}
            <input
              type="file"
              accept={config.accept}
              className="sr-only"
              disabled={state.isUploading}
              onChange={(event) => onUpload(type, event.target.files?.[0])}
            />
          </label>
          {state.fileName && <p className="mt-4 text-sm font-medium text-slate-700">{state.fileName}</p>}
        </div>
      </div>

      {state.error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
          {state.error}
        </div>
      )}

      {state.result && <PreviewCard result={state.result} />}
    </div>
  );
}

function PreviewCard({ result }) {
  return (
    <div className="rounded-lg border border-emerald-200 bg-white p-5">
      <p className="text-sm font-semibold text-emerald-700">{result.message}</p>
      {result.title && <p className="mt-2 text-sm font-medium text-slate-700">{result.title}</p>}
      <div className="mt-4 rounded-md bg-slate-950 p-4 text-sm leading-6 text-slate-100">
        <pre className="max-h-80 overflow-auto whitespace-pre-wrap font-mono">
          {result.preview || result.text}
        </pre>
      </div>
      <p className="mt-3 text-xs text-slate-500">
        Showing {result.preview_characters} of {result.total_characters} extracted characters.
      </p>
      {typeof result.chunk_count === 'number' && (
        <p className="mt-1 text-xs text-slate-500">
          Created {result.chunk_count} chunks in {result.chunks_stored_filename}.
        </p>
      )}
    </div>
  );
}
