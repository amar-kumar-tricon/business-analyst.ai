/**
 * SprintPage — Stage 4 (placeholder).
 * TODO: Implement once sprint endpoint is wired.
 */
import {useAppStore} from '../store/useAppStore';

export default function SprintPage() {
    const project = useAppStore((s) => s.project);

    if (!project)
        return <p className='text-muted-foreground'>No active project.</p>;

    return (
        <section className='mx-auto max-w-4xl space-y-4'>
            <h2 className='text-xl font-semibold'>Stage 4 — Sprint Plan</h2>
            <p className='text-muted-foreground'>
                Sprint planning is not yet implemented. Complete Stages 1–3
                first.
            </p>
        </section>
    );
}
