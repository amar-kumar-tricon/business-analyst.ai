/**
 * ApprovePage — Final review + export.
 *
 * Shows the rendered Stage-2 markdown for the user to read. The Approve
 * button POSTs /approve which builds the approved RAG index and writes
 * the .md / .pdf / .docx artifacts. Once approved, download links go live.
 */
import {useState} from 'react';
import {Link} from 'react-router-dom';

import {projectsApi} from '../api/projects';
import {useAppStore} from '../store/useAppStore';

export default function ApprovePage() {
    const {projectId, projectName, finalDocMarkdown} = useAppStore();
    const applyApprove = useAppStore((s) => s.applyApprove);
    const [busy, setBusy] = useState(false);
    const [approved, setApproved] = useState(false);
    const [error, setError] = useState<string | null>(null);

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

    async function handleApprove() {
        if (!projectId) return;
        setError(null);
        setBusy(true);
        try {
            const r = await projectsApi.approve(projectId);
            applyApprove(r);
            setApproved(true);
        } catch (e: any) {
            setError(
                e?.response?.data?.detail ?? e.message ?? 'Approve failed.',
            );
        } finally {
            setBusy(false);
        }
    }

    return (
        <section className='space-y-5'>
            <header className='flex items-baseline justify-between'>
                <div>
                    <h2 className='text-xl font-semibold'>Final Review</h2>
                    <p className='text-sm text-muted-foreground'>
                        {projectName}
                    </p>
                </div>
                {!approved && (
                    <button
                        disabled={busy}
                        onClick={handleApprove}
                        className='inline-flex h-9 items-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50'
                    >
                        {busy ? 'Approving…' : 'Approve & Export'}
                    </button>
                )}
            </header>

            {error && (
                <div className='rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive'>
                    {error}
                </div>
            )}

            {approved && projectId && (
                <div className='rounded-lg border border-emerald-500/40 bg-emerald-500/10 p-5'>
                    <p className='font-medium text-emerald-600'>
                        Approved & exported.
                    </p>
                    <div className='mt-3 flex flex-wrap gap-3 text-sm'>
                        <a
                            href={projectsApi.artifactUrl(projectId, 'md')}
                            target='_blank'
                            rel='noreferrer'
                            className='rounded-md border border-border bg-background px-3 py-1.5 hover:bg-accent'
                        >
                            Download .md
                        </a>
                        <a
                            href={projectsApi.artifactUrl(projectId, 'pdf')}
                            target='_blank'
                            rel='noreferrer'
                            className='rounded-md border border-border bg-background px-3 py-1.5 hover:bg-accent'
                        >
                            Download .pdf
                        </a>
                        <a
                            href={projectsApi.artifactUrl(projectId, 'docx')}
                            target='_blank'
                            rel='noreferrer'
                            className='rounded-md border border-border bg-background px-3 py-1.5 hover:bg-accent'
                        >
                            Download .docx
                        </a>
                    </div>
                    <Link
                        to='/architecture'
                        className='mt-4 inline-flex h-9 items-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:opacity-90'
                    >
                        Continue to Architecture →
                    </Link>
                </div>
            )}

            <article className='rounded-lg border border-border bg-card p-5'>
                <h3 className='mb-3 text-sm font-medium text-muted-foreground'>
                    Final document preview
                </h3>
                {finalDocMarkdown ? (
                    <pre className='whitespace-pre-wrap break-words font-mono text-xs leading-relaxed'>
                        {finalDocMarkdown}
                    </pre>
                ) : (
                    <p className='text-sm text-muted-foreground'>
                        No final document available. Complete discovery first.
                    </p>
                )}
            </article>
        </section>
    );
}
