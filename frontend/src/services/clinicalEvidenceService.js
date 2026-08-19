const apiUrl = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

/**
 * The UI calls one adapter rather than knowing about HTTP or backend URLs.
 * A non-2xx response intentionally throws so App displays its technical-error
 * state; clinical abstentions arrive as normal 200 responses with a status.
 */
export async function queryClinicalEvidence(question) {
  const response = await fetch(`${apiUrl}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  })

  if (!response.ok) throw new Error(`Evidence API request failed with ${response.status}`)
  return response.json()
}
