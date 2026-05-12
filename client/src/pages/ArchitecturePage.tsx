import mermaid from 'mermaid';
/**
 * ArchitecturePage — Stage 3.
 * Renders Mermaid diagrams in-browser and PlantUML DSL as code blocks.
 */
import {useCallback, useEffect, useRef, useState} from 'react';

import {projectsApi} from '../api/projects';
import {useAppStore} from '../store/useAppStore';

mermaid.initialize({startOnLoad: false, theme: 'dark'});

interface Diagram {
    title: string;
    type: string;
    dsl: string;
}

function MermaidDiagram({dsl, title}: {dsl: string; title: string}) {
    const ref = useRef<HTMLDivElement>(null);
    const [svg, setSvg] = useState<string>('');
    const [error, setError] = useState<string>('');

    const render = useCallback(async () => {
        if (!dsl) return;
        try {
            const id = `mermaid-${title.replace(/\s+/g, '-')}-${Date.now()}`;
            const {svg: rendered} = await mermaid.render(id, dsl);
            setSvg(rendered);
            setError('');
        } catch (e: any) {
            setError(e.message || 'Failed to render');
        }
    }, [dsl, title]);

    useEffect(() => {
        render();
    }, [render]);

    if (error) {
        return (
            <div className='rounded border border-destructive/50 bg-destructive/10 p-3'>
                <p className='mb-2 text-xs text-destructive'>
                    Render error: {error}
                </p>
                <pre className='text-xs text-muted-foreground'>{dsl}</pre>
            </div>
        );
    }

    return (
        <div
            ref={ref}
            className='overflow-auto rounded bg-muted/50 p-4'
            dangerouslySetInnerHTML={{__html: svg}}
        />
    );
}

export default function ArchitecturePage() {
    const project = useAppStore((s) => s.project);
    const [mermaidDiagrams, setMermaidDiagrams] = useState<Diagram[]>([]);
    const [plantumlDiagrams, setPlantumlDiagrams] = useState<Diagram[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [generated, setGenerated] = useState(false);

    useEffect(() => {
        if (!project?.id) return;
        // Check if architecture already exists
        projectsApi.get(project.id).then((res: any) => {
            const arch = res.state?.architecture_output;
            if (arch) {
                setMermaidDiagrams(arch.mermaid ?? []);
                setPlantumlDiagrams(arch.plantuml ?? []);
                setGenerated(true);
            }
        });
    }, [project]);

    async function handleGenerate() {
        if (!project?.id) return;
        setLoading(true);
        setError('');
        try {
            const res = await projectsApi.runArchitecture(project.id);
            const arch = res.architecture_output;
            setMermaidDiagrams(arch?.mermaid ?? []);
            setPlantumlDiagrams(arch?.plantuml ?? []);
            setGenerated(true);
        } catch (e: any) {
            setError(
                e?.response?.data?.detail || e.message || 'Failed to generate',
            );
        } finally {
            setLoading(false);
        }
    }

    if (!project)
        return <p className='text-muted-foreground'>No active project.</p>;

    return (
        <section className='mx-auto max-w-5xl space-y-6'>
            <div className='flex items-center justify-between'>
                <h2 className='text-xl font-semibold'>
                    Stage 3 — Architecture Diagrams
                </h2>
                <button
                    onClick={handleGenerate}
                    disabled={loading}
                    className='rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50'
                >
                    {loading
                        ? 'Generating…'
                        : generated
                          ? 'Regenerate'
                          : 'Generate Diagrams'}
                </button>
            </div>

            {error && (
                <div className='rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive'>
                    {error}
                </div>
            )}

            {!generated && !loading && (
                <p className='text-muted-foreground'>
                    Click "Generate Diagrams" to create architecture diagrams
                    from the analysis.
                </p>
            )}

            {/* Mermaid Diagrams — rendered as SVG */}
            {mermaidDiagrams.map((d, i) => (
                <div
                    key={i}
                    className='rounded-lg border border-border bg-card p-4'
                >
                    <h3 className='mb-3 font-medium'>{d.title}</h3>
                    <MermaidDiagram dsl={d.dsl} title={d.title} />
                    <details className='mt-3'>
                        <summary className='cursor-pointer text-xs text-muted-foreground hover:text-foreground'>
                            View DSL source
                        </summary>
                        <pre className='mt-2 overflow-auto rounded bg-muted p-3 text-xs'>
                            {d.dsl}
                        </pre>
                    </details>
                </div>
            ))}

            {/* PlantUML Diagrams — show DSL code (can't render client-side) */}
            {plantumlDiagrams.map((d, i) => (
                <div
                    key={i}
                    className='rounded-lg border border-border bg-card p-4'
                >
                    <h3 className='mb-3 font-medium'>{d.title}</h3>
                    <pre className='overflow-auto rounded bg-muted p-4 text-sm'>
                        {d.dsl}
                    </pre>
                </div>
            ))}
        </section>
    );
}
