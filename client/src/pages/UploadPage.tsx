/**
 * UploadPage — Stage 0.
 * Create project, optionally upload a file, provide context, then run analysis.
 */
import {useState} from 'react';
import {useNavigate} from 'react-router-dom';

import {projectsApi} from '../api/projects';
import {useAppStore} from '../store/useAppStore';

export default function UploadPage() {
    const [name, setName] = useState('');
    const [file, setFile] = useState<File | null>(null);
    const [context, setContext] = useState('');
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState('');
    const setProject = useAppStore((s) => s.setProject);
    const nav = useNavigate();

    async function handleStart() {
        if (!name.trim()) return setError('Project name is required');
        if (!file && !context.trim())
            return setError('Provide at least a file or additional context');
        setError('');
        setBusy(true);
        try {
            // 1. Create project
            const result = await projectsApi.create(name, context);
            const projectId = result.project_id;

            // 2. Upload file if provided
            if (file) {
                await projectsApi.uploadFile(projectId, file);
            }

            // 3. Run Stage 1 + 2
            const runResult = await projectsApi.run(projectId);

            // Store project info for other pages
            setProject({id: projectId, runResult});

            nav('/analyser');
        } catch (err: any) {
            setError(
                err?.response?.data?.detail ||
                    err.message ||
                    'Something went wrong',
            );
        } finally {
            setBusy(false);
        }
    }

    return (
        <section className='mx-auto max-w-3xl rounded-lg border border-border bg-card p-6 shadow-sm'>
            <h2 className='mb-1 text-xl font-semibold'>
                Stage 0 — Upload Requirement Documents
            </h2>
            <p className='mb-6 text-sm text-muted-foreground'>
                Provide your SOW, BRD, or any context to bootstrap the analysis
                pipeline.
            </p>

            {error && (
                <div className='mb-4 rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive'>
                    {error}
                </div>
            )}

            <div className='space-y-5'>
                <div className='space-y-2'>
                    <label
                        htmlFor='project-name'
                        className='text-sm font-medium'
                    >
                        Project name *
                    </label>
                    <input
                        id='project-name'
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder='E-Commerce Platform'
                        className='flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2'
                    />
                </div>

                <div className='space-y-2'>
                    <label className='text-sm font-medium'>
                        Document{' '}
                        <span className='text-muted-foreground'>
                            (optional, ≤ 50 MB)
                        </span>
                    </label>
                    <input
                        type='file'
                        accept='.pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.txt,.md,.csv,.json'
                        onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                        className='block w-full text-sm text-muted-foreground file:mr-4 file:rounded-md file:border-0 file:bg-primary file:px-3 file:py-2 file:text-sm file:font-medium file:text-primary-foreground hover:file:opacity-90'
                    />
                    {file && (
                        <p className='text-sm text-muted-foreground'>
                            {file.name} ({(file.size / 1024 / 1024).toFixed(1)}{' '}
                            MB)
                        </p>
                    )}
                </div>

                <div className='space-y-2'>
                    <label htmlFor='context' className='text-sm font-medium'>
                        Additional context / requirements *
                    </label>
                    <textarea
                        id='context'
                        rows={6}
                        value={context}
                        onChange={(e) => setContext(e.target.value)}
                        placeholder='Describe the project requirements here. E.g.: We must build an e-commerce platform. The system shall support user registration, product catalog, shopping cart...'
                        className='flex min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2'
                    />
                </div>

                <button
                    disabled={busy}
                    onClick={handleStart}
                    className='inline-flex h-10 items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground ring-offset-background transition-colors hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50'
                >
                    {busy ? 'Analyzing…' : 'Start Analysis →'}
                </button>
            </div>
        </section>
    );
}
