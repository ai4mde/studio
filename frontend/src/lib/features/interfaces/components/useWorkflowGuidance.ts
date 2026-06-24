import { driver } from 'driver.js';
import 'driver.js/dist/driver.css';

// ─── helpers ─────────────────────────────────────────────────────────────────

function getSectionId(ref: any): string {
    return typeof ref === 'string' ? ref : (ref?.value || '');
}

function getLayoutValue(layout: any): string {
    return typeof layout === 'object' ? (layout?.value || '') : (layout || '');
}

function getOperations(ops: any): string[] {
    if (!ops) return [];
    if (Array.isArray(ops)) return ops;
    return Object.entries(ops).filter(([, v]) => v).map(([k]) => k);
}

function getFieldName(attr: any): string {
    return typeof attr === 'string' ? attr : (attr?.name || '');
}

const LAYOUT_ICON: Record<string, string> = {
    form: '📝', table: '📊', list: '📋', detail: '🔍',
    gallery: '🖼', card: '🃏', filter: '🔎',
    timeline: '📅', map: '🗺',
};

// Guess the live username for an actor name string.
export function resolveActorUsername(actorName: string): string {
    const n = actorName.toLowerCase();
    if (n.includes('seller') || n.includes('merchant') || n.includes('vendor')) return 'techstore';
    if (n.includes('customer') || n.includes('buyer') || n.includes('client')) return 'jan_devries';
    if (n.includes('applicant') || n.includes('borrower') || n.includes('student')) return 'demo-applicant';
    if (n.includes('loan') && n.includes('officer')) return 'demo-loan-officer';
    if (n.includes('officer') || n.includes('admin') || n.includes('staff') || n.includes('manager')) return 'demo-loan-officer';
    if (n.includes('system') || n.includes('automated')) return 'system';
    return n.replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '') || 'jan_devries';
}

// ─── content builders ─────────────────────────────────────────────────────────

function actorBadge(name: string): string {
    return `<span style="
        background:#dbeafe;color:#1e40af;
        padding:2px 9px;border-radius:12px;
        font-size:10px;font-weight:700;letter-spacing:.04em
    ">${name}</span>`;
}

function stepBadge(n: number, total: number): string {
    return `<span style="
        background:#f3f4f6;color:#374151;
        padding:2px 9px;border-radius:12px;
        font-size:10px;font-weight:700
    ">STEP ${n} / ${total}</span>`;
}

function modelBadge(model: string): string {
    if (!model) return '';
    return `<span style="
        background:#f3e8ff;color:#7c3aed;
        padding:2px 8px;border-radius:12px;
        font-size:10px;font-weight:600
    ">${model}</span>`;
}

function sectionCard(s: any): string {
    const layout = getLayoutValue(s.layout);
    const ops = getOperations(s.operations).filter(o => !['view', 'read'].includes(o));
    const attrs = (s.attributes || []).slice(0, 5).map(getFieldName).filter(Boolean);
    const more = Math.max(0, (s.attributes || []).length - 5);
    const icon = LAYOUT_ICON[layout] || '📄';

    return `<div style="
        background:#f9fafb;border:1px solid #e5e7eb;
        border-radius:6px;padding:7px 10px;margin-bottom:5px
    ">
        <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">
            <span>${icon}</span>
            <b style="font-size:12px;color:#111827">${s.name || s.id}</b>
            ${layout ? `<span style="color:#6b7280;font-size:10px;background:#f3f4f6;padding:1px 5px;border-radius:4px">${layout}</span>` : ''}
            ${ops.length ? `<span style="font-size:10px;color:#1d4ed8;background:#dbeafe;padding:1px 6px;border-radius:8px;margin-left:auto">${ops.join(' · ')}</span>` : ''}
        </div>
        ${attrs.length ? `<div style="margin-top:4px;color:#6b7280;font-size:10.5px;margin-left:18px">
            ${attrs.join(', ')}${more > 0 ? ` <span style="color:#9ca3af">+${more}</span>` : ''}
        </div>` : ''}
    </div>`;
}

function inferInstruction(dataSections: any[], model: string, actionLabel: string): string {
    const layouts = dataSections.map(s => getLayoutValue(s.layout));
    const allOps = dataSections.flatMap(s => getOperations(s.operations));
    const m = model ? `<b>${model}</b>` : 'the item';
    const btn = `<b>"${actionLabel}"</b>`;

    if (layouts.includes('form')) {
        if (allOps.includes('create'))
            return `Fill in the ${m} form fields and submit to create the record. When done, click ${btn}.`;
        if (allOps.includes('update'))
            return `Review the pre-filled ${m} form, update any fields, then click ${btn}.`;
        return `Complete the ${m} form, then click ${btn}.`;
    }
    if (layouts.some(l => ['list', 'table', 'card', 'gallery'].includes(l))) {
        if (allOps.includes('select'))
            return `Browse the ${m} list and <b>select</b> the appropriate item. Then click ${btn}.`;
        return `Review the ${m} list. Add, edit, or remove items as needed. Then click ${btn}.`;
    }
    if (layouts.includes('detail'))
        return `Review the ${m} details shown on screen. Verify everything is correct, then click ${btn}.`;
    return `Complete this step in the prototype, then click ${btn} to proceed.`;
}

function buildStepBody(
    page: any,
    allSections: any[],
    stepNum: number,
    totalSteps: number,
    actorName: string,
): string {
    const sectionRefs = (page.sections || []).map(getSectionId).filter(Boolean);
    const pageSections = allSections.filter(s => sectionRefs.includes(String(s.id)));

    const data = pageSections.filter(s => {
        const pos = s.position || 'main';
        const l = getLayoutValue(s.layout);
        return pos === 'main' && l !== 'activity_action' && l !== 'activity_start';
    });

    const actionSec = pageSections.find(s => getLayoutValue(s.layout) === 'activity_action');
    const actionLabel = actionSec?.style?.cta_label
        || actionSec?.style?.activity_label
        || actionSec?.label
        || actionSec?.name
        || 'Complete step';

    const model = page.primary_model || data[0]?.class || '';
    const cards = data.slice(0, 4).map(sectionCard).join('');
    const empty = !data.length
        ? '<div style="color:#9ca3af;font-size:11px;padding:4px 2px;font-style:italic">No data sections.</div>'
        : '';
    const instruction = inferInstruction(data, model, actionLabel);

    return `
<div style="font-size:12px;line-height:1.6;max-width:340px">
    <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:10px">
        ${stepBadge(stepNum, totalSteps)}
        ${actorBadge(actorName)}
        ${modelBadge(model)}
    </div>
    ${cards}${empty}
    <div style="
        background:#fff7ed;border-left:3px solid #f97316;
        padding:7px 10px;border-radius:0 5px 5px 0;
        font-size:11.5px;margin-top:6px;color:#374151;line-height:1.55
    ">💡 ${instruction}</div>
</div>`;
}

function buildIntroBody(activityPages: any[], actorName: string): string {
    const items = activityPages.map((p, i) => `
<li style="margin-bottom:5px;display:flex;align-items:flex-start;gap:7px">
    <span style="
        min-width:19px;height:19px;border-radius:50%;
        background:#dbeafe;color:#1e40af;
        display:inline-flex;align-items:center;justify-content:center;
        font-size:10px;font-weight:700;flex-shrink:0;margin-top:1px
    ">${i + 1}</span>
    <span style="font-size:12px">
        ${p.name || `Step ${i + 1}`}
        ${p.primary_model ? `<span style="color:#9ca3af;font-size:10.5px;margin-left:4px">(${p.primary_model})</span>` : ''}
    </span>
</li>`).join('');

    return `
<div style="font-size:12px;line-height:1.65;max-width:340px">
    <div style="display:flex;align-items:center;gap:7px;margin-bottom:10px">
        ${actorBadge(actorName)}
        <span style="color:#6b7280;font-size:11px">${activityPages.length} workflow step${activityPages.length !== 1 ? 's' : ''}</span>
    </div>
    <ol style="margin:0;padding:0;list-style:none">${items}</ol>
    <div style="
        background:#f0fdf4;border-left:3px solid #22c55e;
        padding:7px 10px;border-radius:0 5px 5px 0;
        font-size:11.5px;margin-top:10px;color:#374151
    ">
        You'll first <b>Map UML</b>, then <b>Sync Live</b>, then <b>switch to Live mode</b>.
        After that, each workflow step loads automatically — just follow the instructions.
        Click <b>Next →</b> to begin.
    </div>
</div>`;
}

function buildActorSwitchBody(prevActor: string, nextActor: string, nextUsername: string): string {
    return `
<div style="font-size:12px;line-height:1.65;max-width:320px">
    <div style="
        display:flex;align-items:center;gap:8px;
        background:#fef9c3;border:1px solid #fde047;
        padding:9px 12px;border-radius:8px;margin-bottom:10px
    ">
        <span style="font-size:18px">🔄</span>
        <div>
            <div style="font-weight:700;font-size:12px;color:#713f12">Actor switch required</div>
            <div style="font-size:11px;color:#854d0e;margin-top:2px">${prevActor} → ${nextActor}</div>
        </div>
    </div>
    <p style="margin:0 0 8px;color:#374151">
        The next workflow step belongs to <b>${nextActor}</b>.
        Use the <b>User</b> selector in the toolbar to switch the logged-in user.
    </p>
    <div style="
        background:#f9fafb;border:1px solid #e5e7eb;
        border-radius:6px;padding:9px 12px;
        font-family:ui-monospace,monospace;font-size:12px;
        color:#1d4ed8;letter-spacing:.02em
    ">username: <b>${nextUsername}</b></div>
    <p style="margin:8px 0 0;color:#6b7280;font-size:11px">
        Click the user badge in the toolbar, type <code>${nextUsername}</code> and press Enter,
        then click <b>Next →</b>.
    </p>
</div>`;
}

function buildOutroBody(totalSteps: number, actorName: string): string {
    const stepSuffix = totalSteps === 1 ? '' : 's';
    return `
<div style="font-size:12px;line-height:1.65;max-width:320px">
    <div style="
        background:#f0fdf4;border:1px solid #bbf7d0;
        border-radius:8px;padding:10px 14px;margin-bottom:10px;
        display:flex;align-items:center;gap:9px
    ">
        <span style="font-size:20px">✅</span>
        <div>
            <div style="font-weight:700;font-size:13px;color:#14532d">Workflow complete</div>
            <div style="font-size:11px;color:#166534;margin-top:2px">
                ${totalSteps} step${stepSuffix} tested for <b>${actorName}</b>
            </div>
        </div>
    </div>
    <div style="display:flex;flex-direction:column;gap:6px">
        <div style="
            background:#eff6ff;border-left:3px solid #3b82f6;
            padding:7px 10px;border-radius:0 5px 5px 0;
            font-size:11.5px;color:#374151
        ">
            💡 To test other actors, switch the user in the toolbar and run
            <b>Test Workflow</b> again from their interface.
        </div>
        <div style="
            background:#f5f3ff;border-left:3px solid #8b5cf6;
            padding:7px 10px;border-radius:0 5px 5px 0;
            font-size:11.5px;color:#374151
        ">
            🛠 Use <b>Sync Live</b> after design changes to regenerate the prototype
            before re-testing.
        </div>
    </div>
</div>`;
}

// ─── public API ───────────────────────────────────────────────────────────────

export interface WorkflowGuidanceOptions {
    allPages: any[];
    allSections: any[];
    actorName: string;
    switchToLive: () => void;
    navigateToPage: (pageIdx: number) => void;
    switchActor: (username: string) => void;
}

export function startWorkflowGuidance({
    allPages,
    allSections,
    actorName,
    switchToLive,
    navigateToPage,
    switchActor,
}: WorkflowGuidanceOptions): void {
    const activityPages = (allPages as any[]).filter(
        p => String(p?.type?.value || p?.type || '').toLowerCase() === 'activity',
    );

    if (!activityPages.length) {
        driver({
            overlayOpacity: 0.45,
            allowClose: true,
            doneBtnText: 'OK',
            steps: [{
                element: '#tour-map-uml-btn',
                popover: {
                    title: '⚠️ No Workflow Steps Yet',
                    description: `
<div style="font-size:12px;line-height:1.6;max-width:300px">
    No <b>Activity</b> pages found. Run <b>Map UML</b> first to generate
    workflow pages from your activity diagrams, then start the test again.
</div>`,
                    side: 'bottom',
                    align: 'start',
                },
            }],
        }).drive();
        return;
    }

    const totalSteps = activityPages.length;
    const steps: any[] = [];

    // ── 0. Intro ──────────────────────────────────────────────────────────────
    steps.push({
        popover: {
            title: '🔄 Workflow Test',
            description: buildIntroBody(activityPages, actorName),
        },
    });

    // ── 1. Map UML ────────────────────────────────────────────────────────────
    steps.push({
        element: '#tour-map-uml-btn',
        popover: {
            title: '🪄 Step 1 — Map UML',
            description: `
<div style="font-size:12px;line-height:1.6;max-width:300px">
    Click <b>Map UML</b> to read your class, use-case, and activity diagrams and
    generate all pages and sections automatically.<br><br>
    Wait for the button to show <b>"Mapped!"</b> before clicking <b>Next →</b>.<br><br>
    <div style="
        background:#faf5ff;border-left:3px solid #a855f7;
        padding:7px 10px;border-radius:0 5px 5px 0;font-size:11.5px
    ">
        Already mapped? Skip directly to <b>Next →</b>.
    </div>
</div>`,
            side: 'bottom',
            align: 'end',
        },
    });

    // ── 2. Sync Live ──────────────────────────────────────────────────────────
    steps.push({
        element: '#tour-sync-live-btn',
        popover: {
            title: '🔁 Step 2 — Sync Live',
            description: `
<div style="font-size:12px;line-height:1.6;max-width:300px">
    Click <b>Sync Live</b> to rebuild the running prototype from the current
    design. This pushes your latest pages, sections, and styling to the
    prototype server so the Live view is up to date.<br><br>
    Wait for the button to show <b>"Synced!"</b> before clicking
    <b>Next →</b>.<br><br>
    <div style="
        background:#eff6ff;border-left:3px solid #3b82f6;
        padding:7px 10px;border-radius:0 5px 5px 0;font-size:11.5px
    ">
        Already synced recently? Skip directly to <b>Next →</b>.
    </div>
</div>`,
            side: 'bottom',
            align: 'start',
        },
    });

    // ── 3. Switch to Live ─────────────────────────────────────────────────────
    steps.push({
        element: '#tour-design-live-toggle',
        popover: {
            title: '🖥 Step 3 — Switch to Live',
            description: `
<div style="font-size:12px;line-height:1.6;max-width:300px">
    Click the <b>Live</b> button to launch the running prototype connected to
    real data.<br><br>
    The prototype will load in the preview area. You'll interact with it
    directly in each step of this walkthrough.
</div>`,
            side: 'bottom',
            align: 'start',
        },
        onHighlightStarted: () => switchToLive(),
    });

    // ── 4+. One step per activity page, with actor-switch steps inserted ───────
    let currentActorName = actorName;

    activityPages.forEach((page, idx) => {
        const pageActorName: string = (
            page.action?.actor_node_name
            || page.actor_name
            || actorName
        );
        const pageUsername = resolveActorUsername(pageActorName);
        const pageIdxInAll = (allPages as any[]).findIndex(p => p.id === page.id);

        // If actor changes, insert a switch step first.
        if (
            idx > 0
            && pageActorName
            && pageActorName.toLowerCase() !== currentActorName.toLowerCase()
        ) {
            const prevActor = currentActorName;
            const snapUsername = pageUsername;

            steps.push({
                element: '#tour-live-user-btn',
                popover: {
                    title: '🔄 Switch Actor',
                    description: buildActorSwitchBody(prevActor, pageActorName, snapUsername),
                    side: 'bottom',
                    align: 'start',
                },
                onHighlightStarted: () => switchActor(snapUsername),
            });

            currentActorName = pageActorName;
        }

        // Activity step.
        steps.push({
            element: '#tour-preview-area',
            popover: {
                title: `${idx + 1}. ${page.name || `Step ${idx + 1}`}`,
                description: buildStepBody(page, allSections, idx + 1, totalSteps, currentActorName),
                side: 'left',
                align: 'start',
            },
            onHighlightStarted: () => {
                if (pageIdxInAll >= 0) navigateToPage(pageIdxInAll);
            },
        });
    });

    // ── Final. Outro ──────────────────────────────────────────────────────────
    steps.push({
        element: '#tour-design-live-toggle',
        popover: {
            title: '✅ Workflow Test Complete',
            description: buildOutroBody(totalSteps, actorName),
            side: 'bottom',
            align: 'start',
        },
    });

    driver({
        showProgress: true,
        animate: true,
        overlayOpacity: 0.45,
        smoothScroll: true,
        allowClose: true,
        nextBtnText: 'Next →',
        prevBtnText: '← Back',
        doneBtnText: 'Done ✓',
        steps,
    }).drive();
}
