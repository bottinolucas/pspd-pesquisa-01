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
  atualizarLivro: (isbn, body)  => request(`/livros/${encodeURIComponent(isbn)}`, { method: 'PUT', body: JSON.stringify(body) }),
  deletarLivro:   (isbn)        => request(`/livros/${encodeURIComponent(isbn)}`, { method: 'DELETE' }),
  busca:          (q = '')      => request(`/busca?q=${encodeURIComponent(q)}`),
}
