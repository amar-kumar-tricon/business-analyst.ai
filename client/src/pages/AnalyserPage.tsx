/**
 * AnalyserPage — Stage 1.
 * Shows the structured Analyser output from the /run endpoint.
 */
import {useEffect, useState} from 'react';
import {useNavigate} from 'react-router-dom';

import {projectsApi} from '../api/projects';
import {useAppStore} from '../store/useAppStore';

export default function AnalyserPage() {
    const project = useAppStore((s) => s.project);
    const [state, setState] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const nav = useNavigate();

    useEffect(() => {
        if (!project?.id) return;
        projectsApi
            .get(project.id)
            .then((res: any) => setState(res.state))
            .finally(() => setLoading(false));
    }, [project]);

    if (!project)
        return (
            <p className='text-muted-foreground'>
                No active project. Go to Upload first.
            </p>
        );
    if (loading)
        return <p className='text-muted-foreground'>Loading analysis…</p>;
    if (!state?.analyser_output)
        return (
            <p className='text-muted-foreground'>Analysis not yet available.</p>
        );

    const analyser = state.analyser_output;
    const score = state.score;

    return (
        <section className='mx-auto max-w-4xl space-y-6'>
            <h2 className='text-xl font-semibold'>Stage 1 — Analyser Output</h2>

            {/* Score */}
            <div className='rounded-lg border border-border bg-card p-4'>
                <h3 className='mb-2 font-medium'>Completeness Score</h3>
                <div className='text-3xl font-bold text-primary'>
                    {score?.weighted_total?.toFixed(2)} / 10
                </div>
                {score?.per_criterion_reasoning && (
                    <div className='mt-3 space-y-1 text-sm text-muted-foreground'>
                        {Object.entries(score.per_criterion_reasoning).map(
                            ([key, val]) => (
                                <p key={key}>
                                    <span className='font-medium text-foreground'>
                                        {key.replace(/_/g, ' ')}:
                                    </span>{' '}
                                    {val as string}
                                </p>
                            ),
                        )}
                    </div>
                )}
            </div>

            {/* Executive Summary */}
            <div className='rounded-lg border border-border bg-card p-4'>
                <h3 className='mb-2 font-medium'>Executive Summary</h3>
                <p className='text-sm'>{analyser.executive_summary}</p>
            </div>

            {/* Functional Requirements */}
            <div className='rounded-lg border border-border bg-card p-4'>
                <h3 className='mb-2 font-medium'>
                    Functional Requirements (
                    {analyser.functional_requirements?.length ?? 0})
                </h3>
                <ul className='space-y-2'>
                    {analyser.functional_requirements?.map(
                        (req: any, i: number) => (
                            <li key={i} className='text-sm'>
                                <span className='mr-2 rounded bg-primary/10 px-1.5 py-0.5 text-xs font-medium text-primary'>
                                    {req.moscow?.toUpperCase()}
                                </span>
                                {req.description}
                            </li>
                        ),
                    )}
                </ul>
            </div>

            {/* Risks */}
            <div className='rounded-lg border border-border bg-card p-4'>
                <h3 className='mb-2 font-medium'>
                    Risks ({analyser.risks?.length ?? 0})
                </h3>
                <ul className='space-y-1'>
                    {analyser.risks?.map((r: any, i: number) => (
                        <li key={i} className='text-sm'>
                            <span
                                className={`mr-2 rounded px-1.5 py-0.5 text-xs font-medium ${
                                    r.severity === 'high'
                                        ? 'bg-destructive/10 text-destructive'
                                        : 'bg-muted text-muted-foreground'
                                }`}
                            >
                                {r.severity?.toUpperCase()}
                            </span>
                            {r.description}
                        </li>
                    ))}
                </ul>
            </div>

            {/* Open Questions */}
            <div className='rounded-lg border border-border bg-card p-4'>
                <h3 className='mb-2 font-medium'>
                    Open Questions ({analyser.open_questions?.length ?? 0})
                </h3>
                <ul className='list-disc space-y-1 pl-5 text-sm'>
                    {analyser.open_questions?.map((q: any, i: number) => (
                        <li key={i}>{q.question}</li>
                    ))}
                </ul>
            </div>

            {/* Navigation */}
            {state.current_question && (
                <button
                    onClick={() => nav('/discovery')}
                    className='inline-flex h-10 items-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90'
                >
                    Continue to Discovery →
                </button>
            )}
        </section>
    );
}
