export default function ConfidenceBadge({ confidence }) {
  return <span className={`confidence ${confidence}`}>{confidence === 'high' ? 'High confidence' : `${confidence} confidence`}</span>
}
