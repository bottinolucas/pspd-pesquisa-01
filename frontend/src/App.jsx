import { useState, useEffect, useCallback } from 'react'
import { api } from './api'
import s from './App.module.css'

// ── Componente de alerta ───────────────────────────────────
function Alert({ msg, tipo, onClose }) {
  if (!msg) return null
  return (
    <div className={`${s.alert} ${tipo === 'error' ? s.alertError : s.alertSuccess}`}>
      <span>{msg}</span>
      <button className={s.alertClose} onClick={onClose}>✕</button>
    </div>
  )
}

function useAlert() {
  const [state, setState] = useState({ msg: '', tipo: '' })
  const show = (msg, tipo = 'success') => {
    setState({ msg, tipo })
    setTimeout(() => setState({ msg: '', tipo: '' }), 4000)
  }
  return { ...state, show, clear: () => setState({ msg: '', tipo: '' }) }
}

// ── Aba Catálogo ───────────────────────────────────────────
function TabCatalogo() {
  const [livros, setLivros] = useState([])
  const [filtro, setFiltro] = useState('')
  const [loading, setLoading] = useState(false)
  const alert = useAlert()

  const carregar = useCallback(async (f = filtro) => {
    setLoading(true)
    try {
      const data = await api.listarLivros(f)
      setLivros(data.livros || [])
    } catch (e) {
      alert.show(e.message, 'error')
    } finally {
      setLoading(false)
    }
  }, [filtro])

  useEffect(() => { carregar('') }, [])

  return (
    <section>
      <h2 className={s.paneTitle}>Catálogo de Livros</h2>
      <Alert {...alert} onClose={alert.clear} />

      <div className={s.searchRow}>
        <input
          value={filtro}
          onChange={e => setFiltro(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && carregar()}
          placeholder="Buscar por título ou autor…"
        />
        <button className={s.btn} onClick={() => carregar()}>Buscar</button>
        <button className={`${s.btn} ${s.btnSecondary}`}
          onClick={() => { setFiltro(''); carregar('') }}>
          Limpar
        </button>
      </div>

      {loading ? (
        <p className={s.muted}>Carregando…</p>
      ) : livros.length === 0 ? (
        <p className={s.muted}>Nenhum livro encontrado.</p>
      ) : (
        <div className={s.cardGrid}>
          {livros.map(l => (
            <div key={l.isbn} className={s.bookCard}>
              <div className={s.isbn}>{l.isbn}</div>
              <div className={s.bookTitle}>{l.titulo}</div>
              <div className={s.bookAuthor}>{l.autor} · {l.ano}</div>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}

// ── Aba Adicionar ──────────────────────────────────────────
function TabAdicionar() {
  const [form, setForm] = useState({ isbn: '', titulo: '', autor: '', ano: '' })
  const [loading, setLoading] = useState(false)
  const alert = useAlert()

  const set = k => e => setForm(f => ({ ...f, [k]: e.target.value }))

  const confirmar = async () => {
    if (!form.isbn || !form.titulo || !form.autor || !form.ano) {
      alert.show('Preencha todos os campos.', 'error')
      return
    }
    setLoading(true)
    try {
      const data = await api.adicionarLivro({ ...form, ano: parseInt(form.ano) })
      alert.show(data.mensagem, 'success')
      setForm({ isbn: '', titulo: '', autor: '', ano: '' })
    } catch (e) {
      alert.show(e.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section>
      <h2 className={s.paneTitle}>Adicionar ao Catálogo</h2>
      <div className={s.card}>
        <Alert {...alert} onClose={alert.clear} />
        <div className={s.formRow}>
          <div>
            <label>ISBN</label>
            <input value={form.isbn} onChange={set('isbn')} placeholder="978-0-00-000000-0" />
          </div>
          <div>
            <label>Título</label>
            <input value={form.titulo} onChange={set('titulo')} placeholder="Nome do livro" />
          </div>
          <div>
            <label>Autor</label>
            <input value={form.autor} onChange={set('autor')} placeholder="Nome do autor" />
          </div>
          <div>
            <label>Ano</label>
            <input type="number" value={form.ano} onChange={set('ano')} placeholder="2024" />
          </div>
        </div>
        <button className={s.btn} onClick={confirmar} disabled={loading}>
          {loading ? 'Adicionando…' : 'Adicionar Livro'}
        </button>
      </div>
    </section>
  )
}

// ── App principal ──────────────────────────────────────────
const TABS = [
  { id: 'catalogo',  label: 'Catálogo',       Component: TabCatalogo  },
  { id: 'adicionar', label: 'Adicionar Livro', Component: TabAdicionar },
]

export default function App() {
  const [tab, setTab] = useState('catalogo')
  const { Component } = TABS.find(t => t.id === tab)

  return (
    <div className={s.layout}>
      <header className={s.header}>
        <span className={s.logo}>📚 Biblioteca Distribuída</span>
        <span className={s.badge}>gRPC · Go · Python · PostgreSQL</span>
      </header>

      <nav className={s.nav}>
        {TABS.map(t => (
          <button
            key={t.id}
            className={`${s.navBtn} ${tab === t.id ? s.navBtnActive : ''}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <main className={s.main}>
        <Component />
      </main>

      <footer className={s.footer}>
        <span><span className={s.dot} />Frontend React :3000</span>
        <span><span className={s.dot} />Gateway Go :8080</span>
        <span><span className={s.dot} />Catálogo Python :50051</span>
        <span><span className={s.dot} />PostgreSQL :5432</span>
      </footer>
    </div>
  )
}
