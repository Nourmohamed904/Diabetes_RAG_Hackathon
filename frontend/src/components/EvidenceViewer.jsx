export default function EvidenceViewer({ citation, onClose }) {
  return (
    <aside className="evidence-viewer" aria-label="Retrieved evidence" aria-live="polite">
      <div className="evidence-heading"><div><span className="eyebrow">Traceable evidence</span><h3>Retrieved guideline passage</h3></div><button type="button" onClick={onClose} aria-label="Close evidence details">×</button></div>
      <div className="trace-path"><span>Claim</span><b>→</b><span>Citation</span><b>→</b><strong>Exact evidence</strong></div>
      <blockquote>“{citation.evidence}”</blockquote>
      <dl className="source-metadata">
        <div><dt>Guideline</dt><dd>{citation.document}</dd></div>
        <div><dt>Section</dt><dd>{citation.section}</dd></div>
        <div><dt>Page</dt><dd>{citation.page}</dd></div>
        <div><dt>Chunk ID</dt><dd><code>{citation.chunkId}</code></dd></div>
      </dl>
    </aside>
  )
}
