const json = async (response) => {
  const body = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(body.error || body.message || `Request failed (${response.status})`)
  return body
}

export const api = {
  async get(path) {
    return json(await fetch(path))
  },
  async post(path, payload) {
    return json(await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }))
  },
  async patch(path, payload) {
    return json(await fetch(path, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }))
  },
}

export const asArray = (payload, key) => {
  if (Array.isArray(payload)) return payload
  if (key && Array.isArray(payload?.[key])) return payload[key]
  return payload?.items || payload?.data || []
}

export const mediaUrl = (path) => {
  if (!path) return ''
  if (/^(https?:|blob:|data:)/.test(path)) return path
  return `/api/media/${String(path).replace(/^\/+/, '')}`
}
