import ConfidenceBadge from './ConfidenceBadge'
import ClaimCard from './ClaimCard'
import EvidenceViewer from './EvidenceViewer'

export default function AnswerResult({ result, selectedCitation, onViewEvidence, onCloseEvidence }) {
  return <section className="answer-result" aria-live="polite">
    <div className="result-label"><span className="eyebrow">Grounded response</span><ConfidenceBadge confidence={result.confidence} /></div>
    <h2>Recommendation</h2><p className="recommendation">{result.recommendation}</p>
    <div className="evidence-section"><div><span className="eyebrow">Evidence coverage</span><h3>Claims linked to NICE guidance</h3></div><span className="coverage">{result.claims.length} supported claim{result.claims.length !== 1 ? 's' : ''}</span></div>
    <div className="claim-list">{result.claims.map((claim, index) => <ClaimCard key={`${claim.text}-${index}`} claim={claim} onViewEvidence={onViewEvidence} />)}</div>
    {selectedCitation && <EvidenceViewer citation={selectedCitation} onClose={onCloseEvidence} />}
  </section>
}
