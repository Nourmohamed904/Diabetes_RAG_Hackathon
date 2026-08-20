export default function QuestionInput({ question, onChange, onSubmit, loading }) {
  return (
    <form className="question-form" onSubmit={onSubmit}>
      <label htmlFor="clinical-question">Clinical guideline question (not medicine or dose advice)</label>
      <div className="input-row">
        <textarea
          id="clinical-question"
          value={question}
          onChange={(event) => onChange(event.target.value)}
          placeholder="Ask about diabetes monitoring or targets; medicine and dose questions are safely declined…"
          rows="2"
          disabled={loading}
        />
        <button type="submit" disabled={loading || !question.trim()}>
          {loading ? 'Reviewing evidence…' : 'Ask Evidence Assistant'} <span aria-hidden="true">→</span>
        </button>
      </div>
    </form>
  )
}
