export default function ClaimCard({ claim, onViewEvidence }) {
  const citation = claim.citations[0]
  return <article className="claim-card"><p>{claim.text}</p><div className="citation-row"><span>{citation.document}</span><span>{citation.section} · p. {citation.page}</span><button type="button" onClick={() => onViewEvidence(citation)}>View exact evidence <span aria-hidden="true">→</span></button></div></article>
}
