const copy = {
  insufficient: { eyebrow: 'Intentional abstention', title: 'Insufficient guideline evidence', message: 'The indexed NICE diabetes guidelines did not provide enough evidence to answer this confidently.', note: 'No clinical answer was generated.' },
  safety: { eyebrow: 'Safety boundary triggered', title: 'Patient-specific clinical decision', message: 'This assistant provides guideline evidence, not individual treatment or dosing decisions.', note: 'Please seek urgent advice from an appropriate healthcare professional.' },
  error: { eyebrow: 'Technical issue', title: 'We could not process this request', message: 'The evidence service is temporarily unavailable.', note: 'This is different from an evidence-based refusal. Please try again shortly.' }
}

export default function StatusState({ status, recommendation }) {
  const content = copy[status]
  return <section className={`status-card ${status}`} aria-live="polite"><span className="state-icon" aria-hidden="true">{status === 'error' ? '!' : '✓'}</span><div><span className="eyebrow">{content.eyebrow}</span><h2>{content.title}</h2><p>{recommendation || content.message}</p><strong>{content.note}</strong></div></section>
}
