const typeOneQuestion = 'What HbA1c target should adults with Type 1 diabetes generally aim for?'
const insulinQuestion = 'What insulin regimen is recommended for adults with Type 1 diabetes?'
const sgltQuestion = 'What should be checked before starting an SGLT-2 inhibitor in adults with Type 2 diabetes?'
const unsupportedQuestion = 'What is the recommended screening interval for breast cancer?'
const safetyQuestion = 'I am taking insulin. Should I inject another 8 units right now?'

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

const insulinResponse = {
  status: 'supported',
  question: insulinQuestion,
  recommendation: 'Multiple daily injection basal–bolus insulin regimens are the recommended default approach for adults with type 1 diabetes.',
  confidence: 'medium',
  claims: [
    {
      text: 'Offer multiple daily injection basal–bolus insulin regimens as the insulin injection regimen for adults with type 1 diabetes.',
      citations: [
        {
          document: 'NICE NG17 · Type 1 diabetes in adults',
          section: '1.7 Insulin therapy',
          page: 21,
          chunkId: '300_60_chunk_00146',
          evidence: 'Offer multiple daily injection basal–bolus insulin regimens, rather than twice-daily mixed insulin regimens, as the insulin injection regimen for adults with type 1 diabetes.'
        }
      ]
    }
  ]
}

const sgltResponse = {
  status: 'supported',
  question: sgltQuestion,
  recommendation: 'Before starting an SGLT-2 inhibitor, assess suitability and discuss risks as described in the relevant NICE type 2 diabetes guidance.',
  confidence: 'medium',
  claims: [
    {
      text: 'Suitability and risks should be assessed before initiating an SGLT-2 inhibitor in adults with type 2 diabetes.',
      citations: [
        {
          document: 'NICE NG28 · Type 2 diabetes in adults',
          section: '1.7 Blood glucose management',
          page: 26,
          chunkId: '300_60_chunk_00218',
          evidence: 'When starting treatment with an SGLT2 inhibitor, discuss the benefits and risks with the person, taking into account their clinical circumstances and preferences.'
        }
      ]
    }
  ]
}

export const exampleQuestions = [
  { label: 'Supported · Type 1', question: typeOneQuestion },
  { label: 'Supported · Insulin regimen', question: insulinQuestion },
  { label: 'Supported · Type 2', question: sgltQuestion },
  { label: 'Safety boundary', question: safetyQuestion },
  { label: 'Outside guideline scope', question: unsupportedQuestion },
]

export const mockResponses = {
  supported: [typeOneResponse, insulinResponse, sgltResponse],
  insufficient: {
    status: 'insufficient',
    question: unsupportedQuestion,
    recommendation: 'I could not find enough information in the indexed NICE diabetes guidelines to answer this confidently.',
    confidence: 'insufficient',
    claims: []
  },
  safety: {
    status: 'safety',
    question: safetyQuestion,
    recommendation: 'This request needs an immediate, patient-specific clinical assessment. The Evidence Assistant does not provide individual dosing instructions.',
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
