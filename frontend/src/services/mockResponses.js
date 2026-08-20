const typeOneQuestion = 'What HbA1c target should adults with Type 1 diabetes generally aim for?'
const unsupportedQuestion = 'What is the recommended screening interval for breast cancer?'
const medicineSafetyQuestion = 'What medicine should I take for Type 2 diabetes?'
const doseSafetyQuestion = 'I am taking insulin. Should I inject another 8 units right now?'

const typeOneResponse = {
  status: 'supported',
  question: typeOneQuestion,
  recommendation: 'Adults with type 1 diabetes should generally aim for an HbA1c level of 48 mmol/mol (6.5%) or lower.',
  confidence: 'high',
  claims: [
    {
      text: 'Adults with type 1 diabetes should generally aim for an HbA1c level of 48 mmol/mol (6.5%) or lower.',
      citations: [
        {
          document: 'NICE NG17 · Type 1 diabetes in adults',
          section: '1.6 Blood glucose management',
          page: 18,
          chunkId: '300_60_chunk_00125',
          evidence: 'Support adults with type 1 diabetes to aim for a target HbA1c level of 48 mmol/mol (6.5%) or lower, to minimise the risk of long-term vascular complications.'
        }
      ]
    }
  ]
}

export const exampleQuestions = [
  { label: 'Supported · Type 1', question: typeOneQuestion },
  { label: 'Safety boundary · Medicine', question: medicineSafetyQuestion },
  { label: 'Safety boundary · Dose', question: doseSafetyQuestion },
  { label: 'Outside guideline scope', question: unsupportedQuestion },
]

export const mockResponses = {
  supported: [typeOneResponse],
  insufficient: {
    status: 'insufficient',
    question: unsupportedQuestion,
    recommendation: 'I could not find enough information in the indexed NICE diabetes guidelines to answer this confidently.',
    confidence: 'insufficient',
    claims: []
  },
  safety: {
    status: 'safety',
    question: medicineSafetyQuestion,
    recommendation: 'This assistant does not provide information or recommendations about medicines, medication, insulin, or doses.',
    confidence: 'not-assessed',
    claims: []
  },
  error: {
    status: 'error',
    recommendation: 'We could not process this request right now. Please try again shortly.',
    confidence: null,
    claims: []
  }
}
