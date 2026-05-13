import mermaid from 'mermaid';
/**
 * ArchitecturePage — Stage 3 architecture diagrams.
 *
 * Calls POST /projects/{id}/architecture then renders the returned
 * Mermaid + PlantUML diagrams with explanations. Mermaid diagrams are
 * rendered to SVG client-side; PlantUML shows the raw DSL.
 */
import {useCallback, useEffect, useRef, useState} from 'react';
import {Link} from 'react-router-dom';

import {projectsApi} from '../api/projects';
import {useAppStore} from '../store/useAppStore';

import type {DiagramEntry} from '../types';

mermaid.initialize({startOnLoad: false, theme: 'dark', securityLevel: 'loose'});

function MermaidDiagram({dsl, id}: {dsl: string; id: string}) {
    const ref = useRef<HTMLDivElement>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;
        (async () => {
            try {
                const {svg} = await mermaid.render(`mermaid-${id}`, dsl);
                if (!cancelled && ref.current) ref.current.innerHTML = svg;
            } catch (e: any) {
                if (!cancelled)
                    setError(e?.message ?? 'Failed to render diagram');
            }
        })();
        return () => {
            cancelled = true;
        };
    }, [dsl, id]);

    if (error) {
        return (
            <div className='space-y-2'>
                <p className='text-xs text-destructive'>
                    Render error: {error}
                </p>
                <pre className='max-h-60 overflow-auto rounded border border-border bg-muted p-3 text-xs'>
                    {dsl}
                </pre>
            </div>
        );
    }

    return <div ref={ref} className='overflow-auto' />;
}

function DiagramCard({
    entry,
    idx,
    type,
}: {
    entry: DiagramEntry;
    idx: number;
    type: 'mermaid' | 'plantuml';
}) {
    const [showCode, setShowCode] = useState(false);

    return (
        <article className='rounded-lg border border-border bg-card p-5 space-y-3'>
            <div className='flex items-baseline justify-between gap-2'>
                <h3 className='text-base font-semibold'>{entry.title}</h3>
                <span className='shrink-0 rounded bg-muted px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-muted-foreground'>
                    {type}
                </span>
            </div>

            {entry.explanation && (
                <p className='text-sm text-muted-foreground'>
                    {entry.explanation}
                </p>
            )}

            {type === 'mermaid' ? (
                <MermaidDiagram dsl={entry.dsl} id={`${type}-${idx}`} />
            ) : (
                <pre className='max-h-72 overflow-auto rounded border border-border bg-muted p-3 text-xs'>
                    {entry.dsl}
                </pre>
            )}

            <button
                onClick={() => setShowCode(!showCode)}
                className='text-xs text-muted-foreground underline hover:text-foreground'
            >
                {showCode ? 'Hide code' : 'Show code'}
            </button>
            {showCode && type === 'mermaid' && (
                <pre className='max-h-60 overflow-auto rounded border border-border bg-muted p-3 text-xs'>
                    {entry.dsl}
                </pre>
            )}
        </article>
    );
}

export default function ArchitecturePage() {
    const {projectId, projectName, architectureOutput} = useAppStore();
    const applyArchitecture = useAppStore((s) => s.applyArchitecture);
    const setRunning = useAppStore((s) => s.setRunning);
    const setRunError = useAppStore((s) => s.setRunError);

    const [busy, setBusy] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleGenerate = useCallback(async () => {
        if (!projectId) return;
        setError(null);
        setBusy(true);
        setRunning(true);
        try {
            const r = await projectsApi.runArchitecture(projectId);
            applyArchitecture(r);
        } catch (e: any) {
            const msg =
                e?.response?.data?.detail ??
                e?.message ??
                'Architecture generation failed.';
            setError(msg);
            setRunError(msg);
            setRunning(false);
        } finally {
            setBusy(false);
        }
    }, [projectId, applyArchitecture, setRunning, setRunError]);

    if (!projectId) {
        return (
            <div className='rounded-md border border-border bg-card p-6 text-sm'>
                No active project — start from the{' '}
                <Link to='/' className='text-primary underline'>
                    upload page
                </Link>
                .
            </div>
        );
    }

    const mermaidDiagrams = architectureOutput?.mermaid ?? [];
    const plantumlDiagrams = architectureOutput?.plantuml ?? [];
    const hasDiagrams =
        mermaidDiagrams.length > 0 || plantumlDiagrams.length > 0;

    return (
        <section className='space-y-6'>
            <header className='flex items-baseline justify-between gap-4'>
                <div>
                    <h2 className='text-xl font-semibold'>
                        Stage 3 — Architecture
                    </h2>
                    <p className='text-sm text-muted-foreground'>
                        {projectName}
                    </p>
                </div>
                <div className='flex gap-2'>
                    {!busy && (
                        <button
                            onClick={handleGenerate}
                            className='inline-flex h-9 items-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:opacity-90'
                        >
                            {hasDiagrams
                                ? 'Regenerate Diagrams'
                                : 'Generate Diagrams'}
                        </button>
                    )}
                    {hasDiagrams && (
                        <Link
                            to='/sprint'
                            className='inline-flex h-9 items-center rounded-md border border-border px-4 text-sm font-medium hover:bg-accent'
                        >
                            Continue to Sprint →
                        </Link>
                    )}
                </div>
            </header>

            {error && (
                <div className='rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive'>
                    {error}
                </div>
            )}

            {busy && (
                <div className='rounded-lg border border-border bg-card p-5'>
                    <div className='flex items-center gap-2'>
                        <span className='inline-block h-2 w-2 animate-pulse rounded-full bg-primary' />
                        <p className='text-sm font-medium'>
                            Generating architecture diagrams…
                        </p>
                    </div>
                    <p className='mt-2 text-xs text-muted-foreground'>
                        This may take 1–2 minutes as the AI generates Data Flow,
                        User Flow, System Context, ER, and Deployment diagrams.
                    </p>
                </div>
            )}

            {!hasDiagrams && !busy && !error && (
                <div className='rounded-lg border border-border bg-card p-6 text-center'>
                    <p className='text-sm text-muted-foreground'>
                        No diagrams generated yet. Click{' '}
                        <strong>Generate Diagrams</strong> to create Mermaid and
                        PlantUML diagrams from the approved analysis.
                    </p>
                </div>
            )}

            {mermaidDiagrams.length > 0 && (
                <div className='space-y-4'>
                    <h3 className='text-sm font-medium text-muted-foreground'>
                        Mermaid Diagrams ({mermaidDiagrams.length})
                    </h3>
                    {mermaidDiagrams.map((d, i) => (
                        <DiagramCard
                            key={`m-${i}`}
                            entry={d}
                            idx={i}
                            type='mermaid'
                        />
                    ))}
                </div>
            )}

            {plantumlDiagrams.length > 0 && (
                <div className='space-y-4'>
                    <h3 className='text-sm font-medium text-muted-foreground'>
                        PlantUML Diagrams ({plantumlDiagrams.length})
                    </h3>
                    {plantumlDiagrams.map((d, i) => (
                        <DiagramCard
                            key={`p-${i}`}
                            entry={d}
                            idx={i}
                            type='plantuml'
                        />
                    ))}
                </div>
            )}
        </section>
    );
}
