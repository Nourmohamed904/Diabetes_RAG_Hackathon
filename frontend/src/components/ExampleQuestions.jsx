export default function ExampleQuestions({ examples, onSelect, disabled }) {
  return (
    <section className="examples" aria-label="Example questions">
      <p>Try a demo question</p>
      <div className="example-list">
        {examples.map((example) => (
          <button key={example.question} type="button" onClick={() => onSelect(example.question)} disabled={disabled}>
            <span>{example.label}</span>{example.question}
          </button>
        ))}
      </div>
    </section>
  )
}
