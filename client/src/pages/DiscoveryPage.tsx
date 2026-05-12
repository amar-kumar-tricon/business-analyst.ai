/**
 * DiscoveryPage — Stage 2.
 * Interactive Q&A loop with the Discovery agent.
 */
import {useEffect, useState} from 'react';
import {useNavigate} from 'react-router-dom';

import {projectsApi} from '../api/projects';
import {useAppStore} from '../store/useAppStore';

export default function DiscoveryPage() {
    const project = useAppStore((s) => s.project);
    const [currentQuestion, setCurrentQuestion] = useState<any>(null);
    const [qaHistory, setQaHistory] = useState<any[]>([]);
    const [answer, setAnswer] = useState('');
    const [finalDoc, setFinalDoc] = useState<string | null>(null);
    const [busy, setBusy] = useState(false);
    const [loading, setLoading] = useState(true);
    const nav = useNavigate();

    useEffect(() => {
        if (!project?.id) return;
        projectsApi
            .get(project.id)
            .then((res: any) => {
                const s = res.state;
                setCurrentQuestion(s.current_question);
                setQaHistory(s.qa_history ?? []);
                setFinalDoc(s.final_doc_markdown);
            })
            .finally(() => setLoading(false));
    }, [project]);

    if (!project)
        return <p className='text-muted-foreground'>No active project.</p>;
    if (loading) return <p className='text-muted-foreground'>Loading…</p>;

    async function submit(
        status: 'answered' | 'deferred' | 'na',
        terminate = false,
    ) {
        if (!project) return;
        setBusy(true);
        try {
            const res = await projectsApi.answerDiscovery(
                project.id,
                status === 'answered' ? answer : null,
                status,
                null,
                terminate,
            );
            setCurrentQuestion(res.current_question);
            setQaHistory((prev) => [
                ...prev,
                {question: currentQuestion?.question, answer, status},
            ]);
            setAnswer('');
            setFinalDoc(res.final_doc_markdown);
        } finally {
            setBusy(false);
        }
    }

    return (
        <section className='mx-auto max-w-4xl space-y-6'>
            <h2 className='text-xl font-semibold'>Stage 2 — Discovery Q&A</h2>

            {/* Q&A History */}
            {qaHistory.length > 0 && (
                <div className='rounded-lg border border-border bg-card p-4'>
                    <h3 className='mb-3 font-medium'>Previous Q&A</h3>
                    <div className='space-y-3'>
                        {qaHistory.map((qa, i) => (
                            <div
                                key={i}
                                className='border-l-2 border-primary/30 pl-3 text-sm'
                            >
                                <p className='font-medium'>{qa.question}</p>
                                <p className='text-muted-foreground'>
                                    {qa.status === 'answered'
                                        ? `→ ${qa.answer}`
                                        : `[${qa.status}]`}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Current Question */}
            {currentQuestion && !finalDoc ? (
                <div className='rounded-lg border border-border bg-card p-4'>
                    <h3 className='mb-2 font-medium'>Agent asks:</h3>
                    <p className='mb-3 text-sm'>{currentQuestion.question}</p>
                    {currentQuestion.options?.length > 0 && (
                        <div className='mb-3 space-y-1'>
                            <p className='text-xs font-medium text-muted-foreground'>
                                Suggested options:
                            </p>
                            {currentQuestion.options.map(
                                (opt: string, i: number) => (
                                    <button
                                        key={i}
                                        onClick={() => setAnswer(opt)}
                                        className='block w-full rounded border border-input px-3 py-1.5 text-left text-sm hover:bg-accent'
                                    >
                                        {opt}
                                    </button>
                                ),
                            )}
                        </div>
                    )}
                    <textarea
                        rows={3}
                        value={answer}
                        onChange={(e) => setAnswer(e.target.value)}
                        placeholder='Type your answer...'
                        className='mb-3 flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring'
                    />
                    <div className='flex flex-wrap gap-2'>
                        <button
                            disabled={busy || !answer.trim()}
                            onClick={() => submit('answered')}
                            className='rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50'
                        >
                            Submit Answer
                        </button>
                        <button
                            disabled={busy}
                            onClick={() => submit('deferred')}
                            className='rounded-md border border-input px-3 py-1.5 text-sm font-medium hover:bg-accent'
                        >
                            Defer
                        </button>
                        <button
                            disabled={busy}
                            onClick={() => submit('na')}
                            className='rounded-md border border-input px-3 py-1.5 text-sm font-medium hover:bg-accent'
                        >
                            N/A
                        </button>
                        <button
                            disabled={busy}
                            onClick={() => submit('answered', true)}
                            className='ml-auto rounded-md bg-secondary px-3 py-1.5 text-sm font-medium text-secondary-foreground hover:opacity-90'
                        >
                            Skip remaining & finalize
                        </button>
                    </div>
                </div>
            ) : finalDoc ? (
                <div className='space-y-4'>
                    <div className='rounded-lg border border-border bg-card p-4'>
                        <h3 className='mb-2 font-medium'>Final BRD Document</h3>
                        <pre className='max-h-96 overflow-auto whitespace-pre-wrap rounded bg-muted p-3 text-sm'>
                            {finalDoc}
                        </pre>
                    </div>
                    <button
                        onClick={() => nav('/architecture')}
                        className='inline-flex h-10 items-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90'
                    >
                        Continue to Architecture →
                    </button>
                </div>
            ) : (
                <p className='text-muted-foreground'>No questions available.</p>
            )}
        </section>
    );
}
