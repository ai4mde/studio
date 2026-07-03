import { driver } from 'driver.js';
import 'driver.js/dist/driver.css';

interface TourCallbacks {
    switchToExplore?: () => void;
    switchToRefine?: () => void;
}

export function startInterfaceTour(callbacks: TourCallbacks = {}) {
    const { switchToExplore, switchToRefine } = callbacks;

    const driverObj = driver({
        showProgress: true,
        animate: true,
        overlayOpacity: 0.35,
        smoothScroll: true,
        allowClose: true,
        nextBtnText: 'Next →',
        prevBtnText: '← Back',
        doneBtnText: 'Done ✓',
        steps: [
            // ── TOP-LEVEL TABS ───────────────────────────────────────
            {
                element: '#tour-tablist',
                popover: {
                    title: '📑 Interface Tabs',
                    description:
                        'The interface is split into tabs. <b>Interface Designer</b> is your main workspace. ' +
                        'The other tabs — <b>Pages</b>, <b>Section Components</b>, and <b>Styling</b> — ' +
                        'let you manage the raw data that Interface Designer works with.',
                    side: 'bottom',
                    align: 'start',
                },
            },
            {
                element: '#tour-tab-pages',
                popover: {
                    title: '📄 Pages Tab',
                    description:
                        'Lists all pages in this interface. Each page has a name, a primary model, and a type ' +
                        '(normal or activity). You can add, edit, or delete pages here, or let <b>Map UML</b> create them automatically.',
                    side: 'bottom',
                    align: 'start',
                },
            },
            {
                element: '#tour-tab-sections',
                popover: {
                    title: '🧩 Section Components Tab',
                    description:
                        'Raw section definitions — layout, component, model, fields, operations, and style. ' +
                        'Sections created here appear in the Refine panel. You can also add sections directly from Interface Designer.',
                    side: 'bottom',
                    align: 'start',
                },
            },
            // ── EXPLORE MODE ─────────────────────────────────────────
            {
                element: '#tour-mode-toggle',
                popover: {
                    title: '✦ Explore  /  ⟲ Refine',
                    description:
                        '<b>Explore</b> — generate 3 AI layout candidates from a prompt and pick the best one.<br>' +
                        '<b>Refine</b> — inspect and edit the current sections one-by-one and send targeted AI instructions.',
                    side: 'right',
                    align: 'start',
                },
                onHighlightStarted: () => switchToExplore?.(),
            },
            {
                element: '#tour-explore-prompt',
                popover: {
                    title: '✍️ Describe the Actor\'s Goals',
                    description:
                        'Describe the look or feel you want — e.g. <i>"Change the theme to a dark blue accent with green highlights"</i>. ' +
                        'Use the quick chips below for common styles (compact table, left sidebar, gallery, etc.).',
                    side: 'right',
                    align: 'start',
                },
            },
            {
                element: '#tour-generate-btn',
                popover: {
                    title: '⚡ Generate Candidates',
                    description:
                        'Sends your prompt to the AI agent and streams back <b>3 distinct interface designs</b>. ' +
                        'Each candidate has a mini-preview thumbnail so you can compare at a glance.',
                    side: 'top',
                    align: 'start',
                },
            },
            {
                element: '#tour-candidate-area',
                popover: {
                    title: '🃏 Candidate Cards',
                    description:
                        '<b>Preview</b> — expand the full-size preview of that candidate.<br>' +
                        '<b>Regenerate 3</b> — use this candidate as the base and generate 3 more variants.<br>' +
                        '<b>Apply →</b> — apply this candidate as the current interface design.',
                    side: 'right',
                    align: 'start',
                },
            },

            // ── REFINE MODE ──────────────────────────────────────────
            {
                element: '#tour-sections-panel',
                popover: {
                    title: '📐 Sections List',
                    description:
                        'Every section on the current page. Click a section to select it — its settings appear in the inspector below. ' +
                        'Drag to reorder. Use <b>+ Header</b> / <b>+ Footer</b> to add chrome sections.',
                    side: 'right',
                    align: 'start',
                },
                onHighlightStarted: () => switchToRefine?.(),
            },
            {
                element: '#tour-section-inspector',
                popover: {
                    title: '🔧 Section Inspector',
                    description:
                        'When a section is selected, edit its layout (table, card, form, detail…), component, model, ' +
                        'visible fields, operations (CRUD), and visual style options like density, colour, and shadow.',
                    side: 'right',
                    align: 'start',
                },
            },
            {
                element: '#tour-prompt-panel',
                popover: {
                    title: '💬 AI Refine Prompt',
                    description:
                        'Send a targeted instruction to the AI — e.g. <i>"make the form more compact"</i> or ' +
                        '<i>"add a filter panel above the table"</i>. The agent edits sections in-place without regenerating everything.',
                    side: 'top',
                    align: 'start',
                },
            },

            // ── PREVIEW AREA ─────────────────────────────────────────
            {
                element: '#tour-design-live-toggle',
                popover: {
                    title: '🖥 Design  /  Live',
                    description:
                        '<b>Design</b> — rendered HTML preview of the current schema. Click any component to select that section.<br>' +
                        '<b>Live</b> — the actual running prototype connected to real data. Use this to test interactions end-to-end.',
                    side: 'bottom',
                    align: 'start',
                },
            },
            {
                element: '#tour-page-tabs',
                popover: {
                    title: '📄 Page Tabs',
                    description:
                        'Switch between pages of the interface. ' +
                        '<span style="background:#dcfce7;color:#15803d;padding:1px 6px;border-radius:9px;font-size:11px;font-weight:700">Activity</span> ' +
                        'pages come from workflow steps in your activity diagram — one page per actor action.',
                    side: 'bottom',
                    align: 'start',
                },
            },
            {
                element: '#tour-map-uml-btn',
                popover: {
                    title: '🪄 Map UML',
                    description:
                        'Reads your system\'s class, use case, and activity diagrams and <b>auto-generates all pages and sections</b> ' +
                        'for this interface. Run this first when starting from a fresh interface — then use Explore or Refine to refine the result.',
                    side: 'bottom',
                    align: 'end',
                },
            },
            {
                element: '#tour-preview-area',
                popover: {
                    title: '🖼 Preview',
                    description:
                        'Live rendered preview of the selected page. ' +
                        'Click any component to instantly select and edit that section in the Refine panel. ' +
                        'Switch to <b>Live</b> mode to test the real running prototype.',
                    side: 'left',
                    align: 'start',
                },
            },
        ],
    });

    driverObj.drive();
}
