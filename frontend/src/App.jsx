import { useCallback, useEffect, useMemo, useState } from 'react'
import Icon from './components/Icon.jsx'

const api = async (path, opts) => {
  const r = await fetch('/api' + path, opts && { headers: { 'Content-Type': 'application/json' }, ...opts })
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || r.statusText)
  return r.json()
}

const fmtDate = (iso) => iso
  ? new Date(iso + 'T00:00').toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }) : '—'
const fmtWhen = (t) => new Date(t * 1000).toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
const plural = (n, one, many) => (n === 1 ? one : many)

const NAV = [
  { route: 'overview', label: 'Overview', icon: 'overview' },
  { route: 'case', label: 'Case', icon: 'case' },
  { route: 'hospitals', label: 'Hospitals', icon: 'hospital' },
  { route: 'safety', label: 'Safety', icon: 'safety' },
  { route: 'decision', label: 'Decision', icon: 'decisions' },
  { route: 'journal', label: 'Journal', icon: 'journal' },
]

const VOLUME = {
  high: ['Volume matters', 'risk-critical'],
  mixed: ['Volume: mixed', 'risk-approaching'],
  low: ['Volume barely matters', 'risk-ok'],
  'volume-not-the-signal': ['Volume is not the signal', 'risk-ok'],
}

// A cell is flagged when the data itself says so; nothing is judged here.
const cellTone = (v) => {
  const s = String(v ?? '')
  if (/^worse/i.test(s) || /^(hip|knee)_/i.test(s) || /outlier|alarm/i.test(s) && !/^none$/i.test(s)) return /^worse/i.test(s) ? 'risk-critical' : 'risk-approaching'
  if (/^(no different|better)/i.test(s)) return 'risk-ok'
  return null
}
const flaggedRow = (cols, r) => cols.some((c) => !c.num && cellTone(r[c.k]) && cellTone(r[c.k]) !== 'risk-ok')

function PageHead({ title, lede, actions }) {
  return (
    <div className="page-head">
      <div><h1>{title}</h1>{lede && <p className="lede">{lede}</p>}</div>
      {actions && <div className="page-head-actions">{actions}</div>}
    </div>
  )
}

function Tile({ icon, title, value, unit, body, onClick, tone }) {
  return (
    <button type="button" className="tile" onClick={onClick}>
      <span className="tile-icon"><Icon name={icon} size={24} /></span>
      <span className="tile-title">{title}</span>
      <span className={`tile-figure${tone ? ` tone-${tone}` : ''}`}>
        <span className="tile-value">{value}</span>
        <span className="tile-unit">{unit}</span>
      </span>
      <span className="tile-body">{body}</span>
      <span className="tile-arrow" aria-hidden="true"><Icon name="arrow" size={20} /></span>
    </button>
  )
}

const shortLabel = (l) => l
  .replace(/Medicare FFS volume.*/i, 'Cases (Medicare)')
  .replace(/Failure-to-rescue.*/i, 'Failure to rescue')
  .replace(/Safety composite.*/i, 'Safety composite')
  .replace(/ vs national/i, '')

function DataTable({ d, rows, limit }) {
  const [all, setAll] = useState(false)
  const shown = all || !limit ? rows : rows.slice(0, limit)
  return (
    <>
      <div className="table-wrap">
        <table className="table">
          <thead><tr>{d.columns.map((c) => <th key={c.k} className={c.num ? 'num' : ''} style={{ whiteSpace: 'normal' }}>{shortLabel(c.label)}</th>)}</tr></thead>
          <tbody>
            {shown.map((r, i) => (
              <tr key={i}>
                {d.columns.map((c, j) => {
                  const v = r[c.k]
                  const tone = !c.num && cellTone(v)
                  return (
                    <td key={c.k} className={c.num ? 'num' : j === 0 ? 'strong' : ''}>
                      {v === null || v === undefined ? '—' : tone ? <span className={`risk-chip ${tone}`}>{String(v).replace(/^No Different.*/i, 'In line').replace(/^Worse.*/i, 'Worse than national').replace(/^Better.*/i, 'Better than national')}</span> : String(v)}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {limit && rows.length > limit && (
        <p className="panel-note"><button type="button" className="btn btn-quiet" onClick={() => setAll(!all)}>
          {all ? 'Show fewer' : `Show all ${rows.length}`}</button></p>
      )}
    </>
  )
}

function Cite({ href, children }) {
  return <a className="cite" href={href} target="_blank" rel="noreferrer noopener">{children} ↗</a>
}

const sourceShort = (c) => (c.region === 'US' ? 'Medicare, Ohio' : c.operation_key === 'total hip replacement' ? 'NJR, East Midlands' : 'NOGCA, England')

// The signature: the real low-volume vs benchmark mortality, parsed from the
// cited study's own finding. Absent when no study states both figures.
function volumeFigures(a) {
  for (const e of a?.evidence || []) {
    if (e.counter) continue
    const m = e.finding.match(/(\d+(?:\.\d+)?)% at low-volume hospitals versus (\d+(?:\.\d+)?)%/i)
    if (m) return { low: parseFloat(m[1]), std: parseFloat(m[2]), cite: e.cite.split(',')[0] + ' ' + (e.cite.match(/\d{4}/) || [''])[0] }
  }
  return null
}

function VolumeChart({ f }) {
  const max = Math.max(f.low, f.std)
  const h = (v) => `${Math.round((v / max) * 78)}px`
  return (
    <figure className="vol-chart" aria-label={`30-day mortality ${f.low}% at low-volume hospitals, ${f.std}% at standard`}>
      <div className="vol-chart-bars">
        <div className="vol-col vol-col-worse"><span className="vol-num">{f.low}%</span><div className="vol-bar vol-bar-worse" style={{ height: h(f.low) }} /></div>
        <div className="vol-col"><span className="vol-num">{f.std}%</span><div className="vol-bar" style={{ height: h(f.std) }} /></div>
      </div>
      <div className="vol-labels"><span>Low volume</span><span>Meets standard</span></div>
      <figcaption className="vol-cap">30-day mortality · {f.cite}</figcaption>
    </figure>
  )
}

function Overview({ d, go, run, busy }) {
  const { case: c, assessment: a, timeline } = d
  const rows = a?.data.rows || []
  const flagged = a ? rows.filter((r) => flaggedRow(a.data.columns, r)).length : 0
  const vf = volumeFigures(a)
  const [vlabel, vtone] = VOLUME[a?.judgment.volume_weight] || ['—', null]
  return (
    <>
      <section className="status-strip">
        <div className="strip-words">
          <h1 className="strip-title">The case, so far</h1>
          <p className="strip-line">
            {c.operation.split(' (')[0]} · {rows.length} hospitals · {flagged} flagged
          </p>
          <div className="strip-actions">
            <button type="button" className="btn btn-brand btn-pill" disabled={busy} onClick={run}>
              {busy ? 'Running…' : 'Run the assessment'}
            </button>
          </div>
        </div>
        {vf && <VolumeChart f={vf} />}
      </section>
      <div className="tile-grid tile-grid-primary">
        <Tile icon="hospital" title="Hospitals" value={rows.length} unit={`${plural(rows.length, 'hospital', 'hospitals')} compared`}
          body={sourceShort(c)} onClick={() => go('hospitals')} />
        <Tile icon="safety" title="Safety" value={flagged} unit={plural(flagged, 'flag', 'flags')}
          body={flagged ? 'Worse than national' : 'None flagged'}
          tone={flagged ? 'critical' : null} onClick={() => go('safety')} />
      </div>
      <div className="tile-grid tile-grid-secondary">
        <Tile icon="decisions" title="Decision" value={a ? (a.judgment.volume_weight === 'high' ? 'Yes' : a.judgment.volume_weight === 'mixed' ? 'Partly' : 'No') : '—'}
          unit={vlabel} body=" " onClick={() => go('decision')} />
        <Tile icon="case" title="Case" value={c.travel_miles} unit="miles to travel" body={c.network.replace(/ \(.*\)/, '')} onClick={() => go('case')} />
        <Tile icon="letters" title="Questions" value={a?.questions.length ?? 0} unit="to ask"
          body="For the surgeon" onClick={() => go('decision')} />
        <Tile icon="journal" title="Journal" value={timeline.length} unit={plural(timeline.length, 'entry', 'entries')}
          body="Saved" onClick={() => go('journal')} />
      </div>
      <details style={{ marginTop: 18 }}><summary className="muted" style={{ cursor: 'pointer', fontSize: 12 }}>Sources</summary>
        <p className="muted" style={{ fontSize: 12, marginTop: 6 }}>{a?.data.source}</p></details>
    </>
  )
}

function CaseScreen({ c }) {
  const rows = [['Operation', c.operation], ['Diagnosis', c.diagnosis], ['Hospital', c.hospital], ['Surgeon', c.surgeon],
    ['Cover', c.network], ['Will travel', `${c.travel_miles} miles`], ['Appointment', fmtDate(c.consultation)], ['Region', c.region]]
  return (
    <>
      <PageHead title="Case" />
      <section className="panel">
        <h2 className="panel-title">The operation</h2>
        <dl className="kv">{rows.map(([k, v]) => <div key={k}><dt>{k}</dt><dd>{v || '—'}</dd></div>)}</dl>
      </section>
    </>
  )
}

function HospitalsScreen({ a }) {
  if (!a) return <><PageHead title="Hospitals" /><div className="empty-state"><h3>No assessment yet</h3></div></>
  return (
    <>
      <PageHead title="Hospitals" lede={`${a.data.rows.length} compared`} />
      <section className="panel">
        <DataTable d={a.data} rows={a.data.rows} limit={12} />
        <details className="panel-note"><summary style={{ cursor: 'pointer', fontWeight: 600 }}>Caveat</summary><p style={{ marginTop: 8 }}>{a.data.caveat}</p></details>
        <p className="muted" style={{ marginTop: 14, fontSize: 12 }}>{a.data.source}</p>
      </section>
    </>
  )
}

function SafetyScreen({ a }) {
  if (!a) return <><PageHead title="Safety" /><div className="empty-state"><h3>No assessment yet</h3></div></>
  const flagged = a.data.rows.filter((r) => flaggedRow(a.data.columns, r))
  const d = { ...a.data }
  return (
    <>
      <PageHead title="Safety" lede={`${flagged.length} of ${a.data.rows.length} flagged`} />
      <section className="panel">
        <h2 className="panel-title">Flagged</h2>
        {flagged.length ? <DataTable d={d} rows={flagged} /> : <p className="muted">Nothing in this table is flagged.</p>}
      </section>
      <section className="panel">
        <h2 className="panel-title">Reading</h2>
        <details><summary style={{ cursor: 'pointer', fontWeight: 600 }}>Show</summary><p style={{ marginTop: 8, maxWidth: '80ch' }}>{a.reading}</p></details>
      </section>
      <section className="panel">
        <h2 className="panel-title">Studies</h2>
        {a.evidence.length === 0 && <p className="muted">None cited.</p>}
        <dl className="kv">
          {a.evidence.map((s, i) => (
            <div key={i}>
              <dt>{s.pmid ? <Cite href={`https://pubmed.ncbi.nlm.nih.gov/${s.pmid}/`}>PMID {s.pmid}</Cite> : 'Study'}</dt>
              <dd><strong>{s.cite}</strong>{s.counter && <> <span className="tag">Counter</span></>}<br />{s.finding}</dd>
            </div>
          ))}
        </dl>
      </section>
    </>
  )
}

function DecisionScreen({ a, run, busy, err }) {
  const [why, setWhy] = useState(false)
  if (!a) return <><PageHead title="Decision" /><div className="empty-state"><h3>No assessment yet</h3></div></>
  const j = a.judgment
  const [label, tone] = VOLUME[j.volume_weight] || ['Volume', 'risk-approaching']
  return (
    <>
      <PageHead title="Decision" actions={<>
        <button type="button" className="btn btn-ghost" onClick={() => window.print()}>Print brief</button>
        <button type="button" className="btn btn-brand" disabled={busy} onClick={run}>{busy ? 'Running…' : 'Run live'}</button>
      </>} />
      {err && <div className="error-strip">{err}</div>}
      <section className="panel">
        <h2 className="panel-title">Does volume matter</h2>
        <p style={{ marginBottom: 12 }}><span className={`risk-chip ${tone}`}>{label}</span></p>
        <p style={{ fontSize: 16, lineHeight: '24px', maxWidth: '72ch' }}>{j.volume_verdict}</p>
        <p className="panel-note"><button type="button" className="btn btn-quiet" aria-expanded={why} onClick={() => setWhy(!why)}>
          {why ? 'Hide why' : 'Why'}</button></p>
        {why && <p style={{ marginTop: 14, maxWidth: '80ch' }}>{j.explanation}</p>}
      </section>
      <section className="panel">
        <h2 className="panel-title">Do not conclude</h2>
        <ul className="detail-list">{j.do_not.map((x, i) => <li key={i}>{x}</li>)}</ul>
        <p className="panel-note"><strong>Next.</strong> {j.next_step}</p>
      </section>
      <section className="panel">
        <h2 className="panel-title">Ask at the appointment</h2>
        <ol className="detail-list">{a.questions.map((q, i) => <li key={i}>{q}</li>)}</ol>
      </section>
      <section className="panel">
        <h2 className="panel-title">Law</h2>
        <dl className="kv">
          {a.cases_cited.map((s, i) => (
            <div key={i}><dt>{s.year}</dt>
              <dd><Cite href={s.url}>{s.name}</Cite> <span className="muted">{s.citation}, {s.court}</span><br />{s.why}</dd></div>
          ))}
        </dl>
      </section>
    </>
  )
}

function JournalScreen({ d, setTimeline }) {
  const id = d.case.id
  const [text, setText] = useState('')
  const [sending, setSending] = useState(false)
  const [q, setQ] = useState('')
  const [hits, setHits] = useState(null)
  const [err, setErr] = useState('')
  const send = async (e) => {
    e.preventDefault()
    if (!text.trim() || sending) return
    setSending(true); setErr('')
    try { const r = await api(`/cases/${id}/message`, { method: 'POST', body: JSON.stringify({ text }) }); setTimeline(r.timeline); setText('') }
    catch (e2) { setErr(e2.message) } finally { setSending(false) }
  }
  const search = async (e) => {
    e.preventDefault()
    if (!q.trim()) return
    try { setHits(await api(`/cases/${id}/recall?q=${encodeURIComponent(q)}`)) } catch (e2) { setErr(e2.message) }
  }
  return (
    <>
      <PageHead title="Journal" lede={`${d.timeline.length} entries`} />
      {err && <div className="error-strip">{err}</div>}
      <section className="panel">
        <h2 className="panel-title">Recall</h2>
        <form className="field-row" onSubmit={search} style={{ display: 'flex', gap: 10 }}>
          <label className="field field-grow"><span>Search the journal</span>
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="e.g. what did the surgeon say" /></label>
          <button type="submit" className="btn btn-ghost" style={{ alignSelf: 'flex-end' }}>Search</button>
        </form>
        {hits && (
          <ul className="detail-list" style={{ marginTop: 16 }}>
            {hits.map((h) => <li key={h.id}><strong>{Math.round(h.score * 100)}%</strong> {h.text}</li>)}
            {hits.length === 0 && <li className="muted">Nothing matches.</li>}
          </ul>
        )}
      </section>
      <ul className="journal" style={{ marginBottom: 20 }}>
        {d.timeline.map((m) => (
          <li key={m.id}>
            <span className="journal-at">{fmtWhen(m.created_at)}</span>
            <div className="journal-body">
              <span className="journal-sentence">{m.text}</span>
              <span className="journal-meta">
                <span className="journal-kind">{m.kind}</span>
                <span className={m.role === 'patient' ? '' : 'journal-by'}>{m.role === 'patient' ? 'You' : 'Second Opinion'}</span>
              </span>
            </div>
          </li>
        ))}
      </ul>
      <section className="panel">
        <h2 className="panel-title">Add an entry</h2>
        <form onSubmit={send} style={{ display: 'grid', gap: 12 }}>
          <label className="field"><span>What the surgeon said, or a question</span>
            <textarea rows={3} value={text} onChange={(e) => setText(e.target.value)}
              style={{ font: 'inherit', padding: 10, border: '1px solid var(--line-strong)', borderRadius: 'var(--r-sm)' }} /></label>
          <div><button type="submit" className="btn btn-brand" disabled={sending || !text.trim()}>{sending ? 'Saving…' : 'Add'}</button></div>
        </form>
      </section>
    </>
  )
}

export default function App() {
  const [cases, setCases] = useState([])
  const [id, setId] = useState(null)
  const [d, setD] = useState(null)
  const [route, setRoute] = useState('overview')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')

  useEffect(() => { api('/cases').then((c) => { setCases(c); setId(c[0]?.id) }).catch((e) => setErr(e.message)) }, [])
  useEffect(() => { if (id) { setD(null); api('/cases/' + id).then(setD).catch((e) => setErr(e.message)) } }, [id])

  const run = useCallback(async () => {
    setBusy(true); setErr('')
    try { setD(await api(`/cases/${id}/run`, { method: 'POST' })) } catch (e) { setErr(e.message) } finally { setBusy(false) }
  }, [id])
  const setTimeline = (t) => setD((x) => ({ ...x, timeline: t }))

  const a = d?.assessment
  const body = useMemo(() => {
    if (!d) return <div className="skeleton"><div className="skeleton-line" style={{ width: '32%' }} /><div className="skeleton-line" style={{ width: '88%' }} /><div className="skeleton-line" style={{ width: '66%' }} /></div>
    switch (route) {
      case 'case': return <CaseScreen c={d.case} />
      case 'hospitals': return <HospitalsScreen a={a} />
      case 'safety': return <SafetyScreen a={a} />
      case 'decision': return <DecisionScreen a={a} run={run} busy={busy} err={err} />
      case 'journal': return <JournalScreen d={d} setTimeline={setTimeline} />
      default: return <Overview d={d} go={setRoute} run={run} busy={busy} />
    }
  }, [d, route, busy, err, run, a])

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="side-brand">
          <span className="brand-mark" aria-hidden="true">S</span>
          <span className="brand-words">
            <span className="brand-name">Second Opinion</span>
            <span className="brand-sub">Surgical advocate</span>
          </span>
        </div>
        <nav className="side-nav" aria-label="Screens">
          {NAV.map((n) => (
            <button key={n.route} type="button" className={`side-nav-item${route === n.route ? ' active' : ''}`}
              aria-current={route === n.route ? 'page' : undefined} onClick={() => setRoute(n.route)}>
              <Icon name={n.icon} size={20} /><span className="side-nav-label">{n.label}</span>
            </button>
          ))}
        </nav>
        <p className="side-foot">Second Opinion prepares. You and your surgeon decide.</p>
      </aside>
      <div className="app-column">
        <header className="topbar">
          <span className="topbar-case">
            <span className="topbar-case-label">Case</span>
            <span className="topbar-case-id">{id || '—'}</span>
          </span>
          <div className="topbar-right">
            <span className="clock"><span className="clock-label">Appointment</span>{fmtDate(d?.case.consultation)}</span>
            <select className="autonomy-pill" value={id || ''} onChange={(e) => { setId(e.target.value); setRoute('overview') }} aria-label="Case"
              style={{ color: '#fff', appearance: 'none', paddingRight: 18, maxWidth: 240, textOverflow: 'ellipsis' }}>
              {cases.map((c) => <option key={c.id} value={c.id} style={{ color: '#1c1c1c' }}>{c.operation.split(' (')[0]} · {c.region}</option>)}
            </select>
          </div>
        </header>
        {a && route !== 'safety' && (() => {
          const f = a.data.rows.filter((r) => flaggedRow(a.data.columns, r))
          const nm = (r) => r[a.data.columns[0].k]
          return (
            <button type="button" className="overdue-rail" onClick={() => setRoute('safety')}>
              <strong>{f.length ? (f.length === 1 ? `${nm(f[0])} is flagged on safety.` : `${f.length} of ${a.data.rows.length} hospitals are flagged on safety.`) : 'No hospital is flagged on safety.'}</strong>
              <span>See safety →</span>
            </button>
          )
        })()}
        {busy && <div className="working-rail" role="status"><span className="working-bar" aria-hidden="true" /><span>Reading the data and the studies.</span></div>}
        <main className="app-main"><div className="screen-body">
          {err && route !== 'decision' && <div className="error-strip">{err}</div>}
          {body}
        </div></main>
      </div>
    </div>
  )
}
