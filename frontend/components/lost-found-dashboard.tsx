'use client'

import { useMemo, useState, useEffect } from 'react'
import {
  Bell,
  Camera,
  CheckCircle2,
  ClipboardList,
  Clock3,
  FilePlus2,
  Filter,
  HelpCircle,
  LayoutDashboard,
  Loader2,
  MapPin,
  Menu,
  PackageSearch,
  Search,
  Sparkles,
  X,
} from 'lucide-react'
import { createReport, getReports, Report, MatchResponse } from '@/lib/api'

type ReportType = 'Lost' | 'Found'

const navItems = [
  { label: 'Dashboard', icon: LayoutDashboard },
  { label: 'Reports', icon: ClipboardList },
  { label: 'Report item', icon: FilePlus2 },
  { label: 'Potential matches', icon: Sparkles },
]

export function LostFoundDashboard() {
  const [activeView, setActiveView] = useState('Dashboard')
  const [reports, setReports] = useState<Report[]>([])
  const [matches, setMatches] = useState<MatchResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState<'All' | ReportType>('All')
  const [menuOpen, setMenuOpen] = useState(false)

  // Fetch reports from backend on mount
  useEffect(() => {
    async function fetchReports() {
      try {
        setLoading(true)
        const fetchedReports = await getReports()
        setReports(fetchedReports)
        setLoading(false)
      } catch (error) {
        console.error('Failed to fetch reports:', error)
        setLoading(false)
      }
    }
    
    fetchReports()
  }, [])

  // Compute matches from reports (for dashboard display)
  // Note: Individual matches are now computed by backend per report
  const computedMatches = useMemo(() => matches, [matches])

  const go = (view: string) => { setActiveView(view); setMenuOpen(false) }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <aside className={`fixed inset-y-0 left-0 z-30 flex w-64 flex-col bg-primary px-4 py-6 text-primary-foreground transition-transform lg:translate-x-0 ${menuOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex items-center gap-3 px-3 pb-10"><div className="grid size-9 place-items-center rounded-xl bg-primary-foreground/15"><PackageSearch className="size-5" /></div><div><p className="font-semibold tracking-tight">CampusFind</p><p className="text-xs text-primary-foreground/65">Lost & Found</p></div></div>
        <nav className="flex flex-col gap-2">{navItems.map(({ label, icon: Icon }) => <button key={label} onClick={() => go(label)} className={`flex items-center gap-3 rounded-xl px-3 py-3 text-left text-sm transition-colors ${activeView === label ? 'bg-primary-foreground text-primary shadow-sm' : 'text-primary-foreground/75 hover:bg-primary-foreground/10 hover:text-primary-foreground'}`}><Icon className="size-4" />{label}</button>)}</nav>
        <div className="mt-auto rounded-2xl bg-primary-foreground/10 p-4 text-sm"><HelpCircle className="mb-3 size-5" /><p className="font-medium">Need help?</p><p className="mt-1 text-xs leading-5 text-primary-foreground/65">Contact campus security for urgent items.</p></div>
      </aside>
      {menuOpen && <button aria-label="Close menu" className="fixed inset-0 z-20 bg-foreground/20 lg:hidden" onClick={() => setMenuOpen(false)} />}
      <div className="lg:pl-64">
        <header className="sticky top-0 z-10 flex h-16 items-center justify-between border-b bg-background/95 px-4 backdrop-blur sm:px-8"><div className="flex items-center gap-3"><button aria-label="Open navigation" className="rounded-lg p-2 hover:bg-muted lg:hidden" onClick={() => setMenuOpen(true)}><Menu className="size-5" /></button><div><p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">University of Northbridge</p><h1 className="font-semibold tracking-tight">{activeView}</h1></div></div><button aria-label="Notifications" className="relative rounded-lg p-2 hover:bg-muted"><Bell className="size-5 text-muted-foreground" /><span className="absolute right-1.5 top-1.5 size-1.5 rounded-full bg-accent" /></button></header>
        <main className="mx-auto max-w-6xl p-4 sm:p-8">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="size-8 animate-spin text-primary" />
              <span className="ml-3 text-muted-foreground">Loading reports...</span>
            </div>
          ) : (
            <>
              {activeView === 'Dashboard' && <Dashboard reports={reports} matches={computedMatches} go={go} />}
              {activeView === 'Reports' && <Reports reports={reports} query={query} setQuery={setQuery} filter={filter} setFilter={setFilter} />}
              {activeView === 'Report item' && <ReportForm onSubmit={async (reportData, resetForm) => { 
                try {
                  const result = await createReport(reportData);
                  // Add new report to list
                  setReports((current) => [result.report, ...current]);
                  // Store matches if any
                  if (result.matches.length > 0) {
                    setMatches((current) => [...result.matches, ...current]);
                    alert(`Great! Found ${result.matches.length} potential match${result.matches.length > 1 ? 'es' : ''}!`);
                  }
                  // Show warning if any
                  if (result.warning) {
                    console.warn(result.warning);
                  }
                  resetForm();
                  go('Reports');
                } catch (error) {
                  console.error('Failed to create report:', error);
                  alert('Failed to create report. Please try again.');
                }
              }} />}
              {activeView === 'Potential matches' && <Matches matches={computedMatches} />}
            </>
          )}
        </main>
      </div>
    </div>
  )
}

function Dashboard({ reports, matches, go }: { reports: Report[]; matches: MatchResponse[]; go: (view: string) => void }) {
  // Calculate resolved reports this month using useMemo to avoid hydration mismatch
  const resolvedThisMonth = useMemo(() => {
    if (typeof window === 'undefined') return 0; // Return 0 during SSR
    
    const currentMonth = new Date().getMonth();
    const currentYear = new Date().getFullYear();
    return reports.filter(report => {
      const reportDate = new Date(report.created_at);
      return report.status === 'RESOLVED' && 
             reportDate.getMonth() === currentMonth && 
             reportDate.getFullYear() === currentYear;
    }).length;
  }, [reports]);

  return <div className="space-y-8"><section className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><p className="mb-2 text-sm font-medium text-primary">Welcome back, Jordan</p><h2 className="text-3xl font-semibold tracking-tight text-balance">Help items find their way home.</h2><p className="mt-2 max-w-xl text-sm leading-6 text-muted-foreground">Report a missing item or check if something on campus might be yours.</p></div><button onClick={() => go('Report item')} className="inline-flex w-fit items-center gap-2 rounded-xl bg-primary px-4 py-3 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90"><FilePlus2 className="size-4" />Report an item</button></section><div className="grid gap-3 sm:grid-cols-3"><Stat label="Your reports" value={reports.length} icon={ClipboardList} /><Stat label="Potential matches" value={matches.length} icon={Sparkles} tone="accent" /><Stat label="Resolved this month" value={resolvedThisMonth} icon={CheckCircle2} /></div><section className="grid gap-6 lg:grid-cols-[1.3fr_0.7fr]"><div className="rounded-2xl border bg-card p-5"><div className="mb-5 flex items-center justify-between"><div><h3 className="font-semibold">Recent reports</h3><p className="mt-1 text-xs text-muted-foreground">Your latest activity</p></div><button onClick={() => go('Reports')} className="text-sm font-medium text-primary hover:underline">View all</button></div><div className="divide-y">{reports.slice(0, 4).map((report) => <ReportRow key={report.id} report={report} />)}</div></div><div className="rounded-2xl border bg-secondary/45 p-5"><div className="mb-5 flex size-10 items-center justify-center rounded-xl bg-accent/15 text-accent"><Sparkles className="size-5" /></div><h3 className="font-semibold">Potential matches</h3><p className="mt-2 text-sm leading-6 text-muted-foreground">We found {matches.length} possible {matches.length === 1 ? 'match' : 'matches'} based on item details, location, and timing.</p><button onClick={() => go('Potential matches')} className="mt-5 text-sm font-medium text-primary hover:underline">Review matches →</button></div></section></div>
}

function Stat({ label, value, icon: Icon, tone }: { label: string; value: string | number; icon: typeof ClipboardList; tone?: string }) { return <div className="rounded-2xl border bg-card p-4"><div className={`mb-6 grid size-9 place-items-center rounded-lg ${tone ? 'bg-accent/15 text-accent' : 'bg-primary/10 text-primary'}`}><Icon className="size-4" /></div><p className="text-2xl font-semibold tracking-tight">{value}</p><p className="mt-1 text-sm text-muted-foreground">{label}</p></div> }
function ReportRow({ report }: { report: Report }) { return <div className="flex items-center justify-between gap-3 py-4 first:pt-0 last:pb-0"><div className="min-w-0"><div className="flex items-center gap-2"><span className={`size-2 rounded-full ${report.type === 'Lost' ? 'bg-accent' : 'bg-primary'}`} /><p className="truncate text-sm font-medium">{report.item}</p></div><p className="mt-1 truncate pl-4 text-xs text-muted-foreground">{report.location} · {report.date}</p></div><span className="shrink-0 rounded-full bg-muted px-2.5 py-1 text-xs text-muted-foreground">{report.type}</span></div> }

function Reports({ reports, query, setQuery, filter, setFilter }: { reports: Report[]; query: string; setQuery: (value: string) => void; filter: 'All' | ReportType; setFilter: (value: 'All' | ReportType) => void }) { const filtered = reports.filter((report) => (filter === 'All' || report.type === filter) && `${report.item} ${report.location} ${report.category}`.toLowerCase().includes(query.toLowerCase())); return <div className="space-y-6"><div><h2 className="text-2xl font-semibold tracking-tight">All reports</h2><p className="mt-1 text-sm text-muted-foreground">Browse lost and found items reported on campus.</p></div><div className="flex flex-col gap-3 sm:flex-row"><div className="relative flex-1"><Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search reports..." className="h-11 w-full rounded-xl border bg-card pl-10 pr-4 text-sm outline-none ring-primary/30 placeholder:text-muted-foreground focus:ring-2" /></div><div className="flex gap-2"><Filter className="my-auto size-4 text-muted-foreground" />{(['All', 'Lost', 'Found'] as const).map((value) => <button key={value} onClick={() => setFilter(value)} className={`rounded-lg px-3 text-sm ${filter === value ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground hover:text-foreground'}`}>{value}</button>)}</div></div><div className="grid gap-3 sm:grid-cols-2">{filtered.map((report) => <article key={report.id} className="rounded-2xl border bg-card p-5"><div className="flex items-start justify-between gap-3"><div><span className={`rounded-full px-2.5 py-1 text-xs font-medium ${report.type === 'Lost' ? 'bg-accent/15 text-accent' : 'bg-primary/10 text-primary'}`}>{report.type}</span><h3 className="mt-4 font-semibold">{report.item}</h3></div><span className="text-xs text-muted-foreground">{report.status}</span></div><p className="mt-2 text-sm leading-6 text-muted-foreground">{report.details}</p><div className="mt-4 flex flex-wrap gap-x-4 gap-y-2 text-xs text-muted-foreground"><span className="inline-flex items-center gap-1"><MapPin className="size-3.5" />{report.location}</span><span className="inline-flex items-center gap-1"><Clock3 className="size-3.5" />{report.date}</span></div></article>)}{filtered.length === 0 && <div className="col-span-full rounded-2xl border border-dashed p-12 text-center text-sm text-muted-foreground">No reports match your search.</div>}</div></div> }

function ReportForm({ onSubmit }: { onSubmit: (reportData: any, resetForm: () => void) => Promise<void> }) { 
  const [type, setType] = useState<ReportType>('Lost'); 
  const [item, setItem] = useState(''); 
  const [category, setCategory] = useState('Electronics'); 
  const [color, setColor] = useState(''); 
  const [location, setLocation] = useState(''); 
  const [date, setDate] = useState(''); 
  const [details, setDetails] = useState(''); 
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const resetForm = () => {
    setItem('');
    setColor('');
    setLocation('');
    setDate('');
    setDetails('');
    setError('');
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    if (!item || !color || !location || !date) {
      setError('Please complete all required fields.');
      return;
    }

    try {
      setSubmitting(true);
      setError('');
      
      await onSubmit({
        type,
        item,
        category,
        color,
        location,
        date,
        details: details || undefined
      }, resetForm);
    } catch (err) {
      setError('Failed to create report. Please try again.');
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  return <div className="mx-auto max-w-2xl space-y-6"><div><h2 className="text-2xl font-semibold tracking-tight">Report an item</h2><p className="mt-1 text-sm text-muted-foreground">Add the details that will help reunite an item with its owner.</p></div><form onSubmit={handleSubmit} className="space-y-5 rounded-2xl border bg-card p-5 sm:p-7"><div className="grid grid-cols-2 gap-2 rounded-xl bg-muted p-1">{(['Lost', 'Found'] as const).map((value) => <button type="button" key={value} onClick={() => setType(value)} className={`rounded-lg py-2.5 text-sm font-medium ${type === value ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground'}`}>{value} item</button>)}</div><Field label="Item name" required><input value={item} onChange={(e) => setItem(e.target.value)} placeholder="e.g. Black North Face backpack" className="field" disabled={submitting} /></Field><div className="grid gap-5 sm:grid-cols-2"><Field label="Category" required><select value={category} onChange={(e) => setCategory(e.target.value)} className="field" disabled={submitting}><option>Electronics</option><option>Clothing</option><option>Personal items</option><option>Keys & cards</option><option>Books</option></select></Field><Field label="Color" required><input value={color} onChange={(e) => setColor(e.target.value)} placeholder="e.g. Navy blue" className="field" disabled={submitting} /></Field></div><Field label="Location" required><input value={location} onChange={(e) => setLocation(e.target.value)} placeholder="Where was it lost or found?" className="field" disabled={submitting} /></Field><Field label="Date" required><input type="date" value={date} onChange={(e) => setDate(e.target.value)} className="field" disabled={submitting} /></Field><Field label="Details"><textarea value={details} onChange={(e) => setDetails(e.target.value)} placeholder="Add identifying details, stickers, marks, or contents..." rows={4} className="field resize-none" disabled={submitting} /></Field><button type="button" className="flex w-full items-center justify-center gap-2 rounded-xl border border-dashed py-3 text-sm text-muted-foreground hover:bg-muted" disabled={submitting}><Camera className="size-4" />Add a photo (optional)</button>{error && <p className="text-sm text-accent">{error}</p>}<button type="submit" className="w-full rounded-xl bg-primary py-3 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2" disabled={submitting}>
    {submitting ? <><Loader2 className="size-4 animate-spin" />Submitting...</> : 'Submit report'}
  </button></form></div> }
function Field({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) { return <label className="block space-y-2 text-sm font-medium">{label}{required && <span className="ml-1 text-accent">*</span>}{children}</label> }

function Matches({ matches }: { matches: MatchResponse[] }) { 
  return <div className="space-y-6"><div><h2 className="text-2xl font-semibold tracking-tight">Potential matches</h2><p className="mt-1 max-w-2xl text-sm leading-6 text-muted-foreground">These pairs are ranked by AI-powered matching. Each match shows why items might be related.</p></div><div className="space-y-4">{matches.map(({ lost_report, found_report, score, component_scores, reasons }, idx) => <article key={`${lost_report.id}-${found_report.id}-${idx}`} className="rounded-2xl border bg-card p-5"><div className="flex flex-wrap items-center justify-between gap-3"><div className="flex items-center gap-2"><Sparkles className="size-4 text-accent" /><span className="text-sm font-semibold">{score.toFixed(1)}% match</span><span className={`rounded-full px-2 py-1 text-xs ${score >= 70 ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground'}`}>{score >= 70 ? 'High confidence' : 'Possible match'}</span></div><button className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted" aria-label="Dismiss match"><X className="size-4" /></button></div><div className="mt-5 grid gap-3 sm:grid-cols-2"><div className="rounded-xl bg-accent/8 p-4"><p className="text-xs font-medium uppercase tracking-wider text-accent">Lost report</p><p className="mt-2 font-medium">{lost_report.item}</p><p className="mt-1 text-xs text-muted-foreground">{lost_report.location} · {lost_report.date}</p></div><div className="rounded-xl bg-primary/6 p-4"><p className="text-xs font-medium uppercase tracking-wider text-primary">Found report</p><p className="mt-2 font-medium">{found_report.item}</p><p className="mt-1 text-xs text-muted-foreground">{found_report.location} · {found_report.date}</p></div></div><div className="mt-4 space-y-2"><p className="text-xs font-medium text-muted-foreground">Why this matches:</p><div className="flex flex-wrap gap-2">{reasons.map((reason, i) => <span key={i} className="rounded-full bg-muted px-2.5 py-1 text-xs text-muted-foreground">{reason}</span>)}</div></div><details className="mt-3"><summary className="cursor-pointer text-xs text-muted-foreground hover:text-foreground">Show score breakdown</summary><div className="mt-2 grid grid-cols-2 gap-2 text-xs"><div>Category/Item: {component_scores.item_category.toFixed(1)}/25</div><div>Semantic: {component_scores.vector.toFixed(1)}/25</div><div>Keywords: {component_scores.keywords.toFixed(1)}/15</div><div>Location: {component_scores.location.toFixed(1)}/15</div><div>Color: {component_scores.color.toFixed(1)}/10</div><div>Date: {component_scores.date.toFixed(1)}/10</div></div></details></article>)}{matches.length === 0 && <div className="rounded-2xl border border-dashed p-12 text-center text-sm text-muted-foreground">No potential matches yet. More reports will improve matching.</div>}</div></div> 
}

declare global { interface HTMLInputElement { className?: string } }

export default LostFoundDashboard
