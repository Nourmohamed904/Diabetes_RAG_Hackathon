const steps = ['Searching approved NICE guidelines', 'Evaluating retrieved evidence', 'Building a grounded response']

export default function LoadingState() {
  return <section className="loading-card" aria-live="polite"><span className="eyebrow">Evidence review in progress</span>{steps.map((step, index) => <div className="loading-step" key={step}><span>{index + 1}</span>{step}</div>)}</section>
}
