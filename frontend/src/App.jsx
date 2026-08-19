import { useState } from 'react'
import Header from './components/Header'
import QuestionInput from './components/QuestionInput'
import ExampleQuestions from './components/ExampleQuestions'
import LoadingState from './components/LoadingState'
import AnswerResult from './components/AnswerResult'
import StatusState from './components/StatusState'
import Footer from './components/Footer'
import { exampleQuestions } from './services/mockResponses'
import { queryClinicalEvidence } from './services/clinicalEvidenceService'

export default function App() {
  const [question, setQuestion] = useState('What HbA1c target should adults with Type 1 diabetes generally aim for?')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [selectedCitation, setSelectedCitation] = useState(null)

  async function submitQuestion(event) {
    event?.preventDefault()
    if (!question.trim() || loading) return
    setLoading(true); setResult(null); setSelectedCitation(null)
    try { setResult(await queryClinicalEvidence(question)) }
    catch { setResult({ status: 'error' }) }
    finally { setLoading(false) }
  }

  function selectExample(value) { setQuestion(value); setResult(null); setSelectedCitation(null) }

  return <div className="app-shell" id="top"><Header /><main><section className="hero"><span className="eyebrow">Clinical decision support demonstration</span><h1>Evidence you can <em>trace.</em></h1><p>Evidence-grounded clinical guidance from NICE NG17 and NG28—designed to answer only when the guidance supports it.</p></section><QuestionInput question={question} onChange={setQuestion} onSubmit={submitQuestion} loading={loading} /><ExampleQuestions examples={exampleQuestions} onSelect={selectExample} disabled={loading} />{loading && <LoadingState />}{result?.status === 'supported' && <AnswerResult result={result} selectedCitation={selectedCitation} onViewEvidence={setSelectedCitation} onCloseEvidence={() => setSelectedCitation(null)} />}{result && result.status !== 'supported' && <StatusState status={result.status} recommendation={result.recommendation} />}</main><Footer /></div>
}
