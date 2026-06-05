const BASE = '/api/v1'

async function request(path, opts = {}) {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.erro || 'Erro desconhecido')
  return data
}

export const api = {
  listarLivros:   (filtro = '') => request(`/livros?filtro=${encodeURIComponent(filtro)}`),
  buscarLivro:    (isbn)        => request(`/livros/${encodeURIComponent(isbn)}`),
  adicionarLivro: (body)        => request('/livros', { method: 'POST', body: JSON.stringify(body) }),
  busca:          (q = '')      => request(`/busca?q=${encodeURIComponent(q)}`),
}
