import React from "react";
import type { SemanticField, SemanticPageAst, SemanticSection } from "$browser/queries";

type Props = {
    pages: Array<{ name: string; semanticAst?: SemanticPageAst; sections?: unknown[] }>;
};

// ── Widget renderers keyed by semantic_role ──────────────────────────────────

function FieldWidget({ field, sample }: { field: SemanticField; sample?: string }) {
    const v = sample ?? field.name.replace(/_/g, " ");

    switch (field.semanticRole) {
        case "image_primary":
            return (
                <div className="w-full aspect-square bg-gray-100 rounded-lg overflow-hidden flex items-center justify-center">
                    <img src="https://placehold.co/400x400/e5e7eb/9ca3af?text=Image" alt={field.name} className="object-cover w-full h-full" />
                </div>
            );
        case "image_gallery":
            return (
                <div className="flex gap-2 overflow-x-auto py-1">
                    {[1, 2, 3, 4].map(i => (
                        <div key={i} className="shrink-0 w-16 h-16 bg-gray-100 rounded border-2 border-transparent hover:border-indigo-400 cursor-pointer overflow-hidden">
                            <img src={`https://placehold.co/64x64/e5e7eb/9ca3af?text=${i}`} alt="" className="w-full h-full object-cover" />
                        </div>
                    ))}
                </div>
            );
        case "title":
            return <h1 className="text-2xl font-bold text-gray-900 leading-tight">{v}</h1>;
        case "brand":
            return <a href="#" className="text-sm font-medium text-indigo-600 hover:underline">{v}</a>;
        case "category_label":
            return <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-600">{v}</span>;
        case "price_current":
            return <span className="text-3xl font-bold text-gray-900">€ {v}</span>;
        case "price_original":
            return <span className="text-base text-gray-400 line-through">€ {v}</span>;
        case "price_discount":
            return <span className="inline-flex items-center rounded-full bg-red-100 px-2 py-0.5 text-sm font-semibold text-red-600">-{v}%</span>;
        case "price_total":
            return <span className="text-xl font-bold text-gray-900">€ {v}</span>;
        case "rating_score":
            return (
                <span className="flex items-center gap-1 text-amber-500 font-medium text-sm">
                    {"★★★★☆"} <span className="text-gray-700">{v}</span>
                </span>
            );
        case "rating_count":
            return <span className="text-sm text-indigo-600 hover:underline cursor-pointer">({v} reviews)</span>;
        case "review_text":
            return <p className="text-sm text-gray-700 leading-relaxed italic">"{v}"</p>;
        case "availability":
            return (
                <span className="inline-flex items-center gap-1.5 text-sm font-medium text-green-700">
                    <span className="h-2 w-2 rounded-full bg-green-500" />
                    Op voorraad
                </span>
            );
        case "status_badge":
            return <span className="inline-flex rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-semibold text-blue-700">{v}</span>;
        case "badge":
            return <span className="inline-flex rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">{v}</span>;
        case "spec_name":
            return <dt className="text-sm font-medium text-gray-600">{v}</dt>;
        case "spec_value":
            return <dd className="text-sm text-gray-900">{v}</dd>;
        case "description_long":
            return (
                <div>
                    <p className="text-sm text-gray-600 leading-relaxed line-clamp-4">{v} — Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation...</p>
                    <button className="mt-1 text-xs text-indigo-600 hover:underline">Read more ↓</button>
                </div>
            );
        case "description_short":
            return <p className="text-sm text-gray-500">{v}</p>;
        case "quantity_input":
            return (
                <div className="flex items-center gap-2">
                    <button className="w-8 h-8 rounded border border-gray-300 flex items-center justify-center text-lg font-medium hover:bg-gray-50">−</button>
                    <input type="number" defaultValue={1} min={1} className="w-14 text-center border border-gray-300 rounded px-2 py-1 text-sm" />
                    <button className="w-8 h-8 rounded border border-gray-300 flex items-center justify-center text-lg font-medium hover:bg-gray-50">+</button>
                </div>
            );
        case "delivery_date":
            return (
                <span className="flex items-center gap-1.5 text-sm text-gray-700">
                    <span className="text-base">📦</span> Delivered: <strong>{v}</strong>
                </span>
            );
        case "delivery_option":
            return (
                <label className="flex items-start gap-3 rounded-lg border border-gray-200 p-3 cursor-pointer hover:border-indigo-400">
                    <input type="radio" name="delivery" className="mt-0.5" defaultChecked />
                    <div>
                        <div className="text-sm font-medium text-gray-900">{v}</div>
                        <div className="text-xs text-gray-500">Free · Delivered tomorrow</div>
                    </div>
                </label>
            );
        case "delivery_cost":
            return <span className="text-sm text-gray-600">{v === "0" ? "Free" : `€ ${v}`}</span>;
        case "product_sku":
            return <span className="text-xs text-gray-400">SKU: {v}</span>;
        case "identifier":
            return null;
        case "color_swatch":
            return (
                <div className="flex gap-2">
                    {["#1e3a5f", "#c0c0c0", "#f5f5f0", "#2d4a3e"].map(c => (
                        <button key={c} title={c} className="w-7 h-7 rounded-full border-2 border-transparent ring-2 ring-offset-1 hover:ring-indigo-400" style={{ backgroundColor: c }} />
                    ))}
                </div>
            );
        case "variant_selector":
            return (
                <div className="flex gap-2 flex-wrap">
                    {["128GB", "256GB", "512GB"].map(s => (
                        <button key={s} className="rounded border border-gray-300 px-3 py-1 text-sm hover:border-indigo-500 hover:text-indigo-600">{s}</button>
                    ))}
                </div>
            );
        case "verification_badge":
            return <span className="inline-flex items-center gap-1 text-xs text-green-700 font-medium">✓ Verified seller</span>;
        case "toggle":
            return <input type="checkbox" className="h-4 w-4 rounded border-gray-300" />;
        case "tag_list":
            return (
                <div className="flex gap-1.5 flex-wrap">
                    {["tag1", "tag2", "tag3"].map(t => (
                        <span key={t} className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">{t}</span>
                    ))}
                </div>
            );
        case "text_note":
            return <p className="text-sm text-gray-600 bg-gray-50 rounded p-2">{v}</p>;
        case "progress_bar":
            return (
                <div className="flex items-center gap-2">
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                        <div className="bg-indigo-500 h-2 rounded-full" style={{ width: "65%" }} />
                    </div>
                    <span className="text-xs text-gray-500">65%</span>
                </div>
            );
        case "numeric_display":
            return <span className="text-sm tabular-nums text-gray-700">{v}</span>;
        case "email":
            return <a href={`mailto:${v}`} className="text-sm text-indigo-600 hover:underline">{v}</a>;
        case "phone":
            return <a href={`tel:${v}`} className="text-sm text-gray-700">{v}</a>;
        case "url_link":
            return <a href="#" target="_blank" rel="noreferrer" className="text-sm text-indigo-600 hover:underline flex items-center gap-1">{v} ↗</a>;
        case "datetime_display":
        case "date_created":
        case "date_updated":
            return <span className="text-sm text-gray-500">{v}</span>;
        default:
            return <span className="text-sm text-gray-700">{v}</span>;
    }
}

// ── Group spec fields from a section into a table ────────────────────────────

function SpecTable({ fields }: { fields: SemanticField[] }) {
    const specPairs: Array<[SemanticField, SemanticField]> = [];
    let i = 0;
    while (i < fields.length) {
        if (fields[i].semanticRole === "spec_name" && i + 1 < fields.length && fields[i + 1].semanticRole === "spec_value") {
            specPairs.push([fields[i], fields[i + 1]]);
            i += 2;
        } else {
            i++;
        }
    }
    if (specPairs.length === 0) return null;
    return (
        <dl className="divide-y divide-gray-100">
            {specPairs.map(([nameField, valField]) => (
                <div key={nameField.name} className="flex py-2 gap-4">
                    <dt className="w-40 shrink-0 text-sm font-medium text-gray-500">{nameField.name.replace(/_/g, " ")}</dt>
                    <dd className="text-sm text-gray-900">{valField.name.replace(/_/g, " ")} value</dd>
                </div>
            ))}
        </dl>
    );
}

// ── Section renderer ──────────────────────────────────────────────────────────

function SectionRenderer({ section }: { section: SemanticSection }) {
    const roleOf = (field: SemanticField) => field.semanticRole ?? "";

    const hasSpecFields = section.fields.some(f => f.semanticRole === "spec_name" || f.semanticRole === "spec_value" || f.semanticRole === "spec_group");
    const specFields = section.fields.filter(f => ["spec_name", "spec_value", "spec_group"].includes(f.semanticRole));
    const otherFields = section.fields.filter(f => !["spec_name", "spec_value", "spec_group", "identifier"].includes(f.semanticRole));

    const imageFields = otherFields.filter(f => f.semanticRole === "image_primary" || f.semanticRole === "image_gallery");
    const priceFields = otherFields.filter(f => roleOf(f).startsWith("price_") || roleOf(f) === "currency_label");
    const ratingFields = otherFields.filter(f => roleOf(f).startsWith("rating_"));
    const deliveryFields = otherFields.filter(f => roleOf(f).startsWith("delivery_"));
    const actionFields = otherFields.filter(f => f.semanticRole === "quantity_input" || f.semanticRole === "color_swatch" || f.semanticRole === "variant_selector");
    const restFields = otherFields.filter(f =>
        !roleOf(f).startsWith("price_") &&
        !roleOf(f).startsWith("rating_") &&
        !roleOf(f).startsWith("delivery_") &&
        roleOf(f) !== "image_primary" &&
        roleOf(f) !== "image_gallery" &&
        roleOf(f) !== "quantity_input" &&
        roleOf(f) !== "color_swatch" &&
        roleOf(f) !== "variant_selector" &&
        roleOf(f) !== "currency_label"
    );

    const isMany = section.multiplicity === "many";

    // For multi-instance sections (related products, reviews), show cards
    if (isMany) {
        return (
            <div>
                <h3 className="text-base font-semibold text-gray-800 mb-3">{section.entity}</h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
                    {[1, 2, 3, 4].map(i => (
                        <div key={i} className="rounded-lg border border-gray-200 bg-white p-3 hover:shadow-md transition-shadow cursor-pointer">
                            {section.fields.filter(f => f.semanticRole === "image_primary").length > 0 && (
                                <div className="aspect-square bg-gray-100 rounded mb-2 flex items-center justify-center">
                                    <img src={`https://placehold.co/120x120/e5e7eb/9ca3af?text=${i}`} alt="" className="object-cover w-full h-full rounded" />
                                </div>
                            )}
                            {section.fields.filter(f => f.semanticRole === "title" || f.semanticRole === "brand").map(f => (
                                <p key={f.name} className="text-xs font-medium text-gray-800 line-clamp-2">{f.name.replace(/_/g, " ")} #{i}</p>
                            ))}
                            {section.fields.filter(f => f.semanticRole === "price_current").map(f => (
                                <p key={f.name} className="text-sm font-bold text-gray-900 mt-1">€ {(10 * i + 99).toFixed(2)}</p>
                            ))}
                            {section.fields.filter(f => f.semanticRole === "rating_score").map(f => (
                                <span key={f.name} className="text-xs text-amber-500">★★★★☆</span>
                            ))}
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {/* Image hero */}
            {imageFields.filter(f => f.semanticRole === "image_primary").length > 0 && (
                <div className="space-y-2">
                    <FieldWidget field={imageFields.find(f => f.semanticRole === "image_primary")!} />
                    {imageFields.filter(f => f.semanticRole === "image_gallery").length > 0 && (
                        <FieldWidget field={imageFields.find(f => f.semanticRole === "image_gallery")!} />
                    )}
                </div>
            )}

            {/* Title / brand / category */}
            {restFields.filter(f => ["title", "brand", "category_label", "description_short"].includes(f.semanticRole)).map(f => (
                <FieldWidget key={f.name} field={f} />
            ))}

            {/* Price block */}
            {priceFields.length > 0 && (
                <div className="flex items-baseline gap-3 flex-wrap">
                    {priceFields.map(f => <FieldWidget key={f.name} field={f} />)}
                </div>
            )}

            {/* Rating */}
            {ratingFields.length > 0 && (
                <div className="flex items-center gap-2">
                    {ratingFields.map(f => <FieldWidget key={f.name} field={f} />)}
                </div>
            )}

            {/* Availability / status */}
            {restFields.filter(f => f.semanticRole === "availability" || f.semanticRole === "status_badge").map(f => (
                <FieldWidget key={f.name} field={f} />
            ))}

            {/* Variant / color selectors */}
            {actionFields.filter(f => f.semanticRole === "color_swatch" || f.semanticRole === "variant_selector").length > 0 && (
                <div className="space-y-2">
                    {actionFields.filter(f => f.semanticRole === "color_swatch" || f.semanticRole === "variant_selector").map(f => (
                        <div key={f.name}>
                            <p className="text-xs font-medium text-gray-500 mb-1">{f.name.replace(/_/g, " ")}</p>
                            <FieldWidget field={f} />
                        </div>
                    ))}
                </div>
            )}

            {/* Quantity + Add to cart */}
            {actionFields.filter(f => f.semanticRole === "quantity_input").length > 0 && (
                <div className="flex items-center gap-3">
                    {actionFields.filter(f => f.semanticRole === "quantity_input").map(f => (
                        <FieldWidget key={f.name} field={f} />
                    ))}
                    <button className="flex-1 bg-indigo-600 text-white text-sm font-semibold rounded-lg px-5 py-2.5 hover:bg-indigo-700">
                        In winkelwagen
                    </button>
                </div>
            )}

            {/* Spec table */}
            {hasSpecFields && (
                <div>
                    <h4 className="text-sm font-semibold text-gray-700 mb-2">Specifications</h4>
                    <SpecTable fields={specFields} />
                </div>
            )}

            {/* Delivery options */}
            {deliveryFields.length > 0 && (
                <div className="space-y-2">
                    <h4 className="text-sm font-semibold text-gray-700">Delivery</h4>
                    {deliveryFields.map(f => <FieldWidget key={f.name} field={f} />)}
                </div>
            )}

            {/* Long description */}
            {restFields.filter(f => f.semanticRole === "description_long").map(f => (
                <FieldWidget key={f.name} field={f} />
            ))}

            {/* Remaining fields */}
            {restFields.filter(f => !["title", "brand", "category_label", "description_short", "description_long", "availability", "status_badge"].includes(f.semanticRole)).map(f => (
                f.semanticRole !== "identifier" ? (
                    <div key={f.name}>
                        <p className="text-xs font-medium text-gray-500 mb-0.5">{f.name.replace(/_/g, " ")}</p>
                        <FieldWidget field={f} />
                    </div>
                ) : null
            ))}
        </div>
    );
}

// ── Page renderer ─────────────────────────────────────────────────────────────

function PageRenderer({ page }: { page: { name: string; semanticAst?: SemanticPageAst } }) {
    const ast = page.semanticAst;
    if (!ast?.sections?.length) {
        return <p className="text-sm text-gray-400 py-8 text-center">No sections defined for this page.</p>;
    }

    // Determine layout: if there are image sections, use a two-column layout
    const hasMedia = ast.sections.some(s => s.fields.some(f => f.semanticRole === "image_primary" || f.semanticRole === "image_gallery"));
    const isDetail = ast.sections.some(s => s.kind === "region.detail");
    const manySection = ast.sections.filter(s => s.multiplicity === "many");
    const singleSections = ast.sections.filter(s => s.multiplicity !== "many");

    return (
        <div className="space-y-8">
            {/* Main content: two-column for product detail, single for others */}
            {hasMedia && isDetail ? (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Left: media sections */}
                    <div className="space-y-4">
                        {singleSections.filter(s => s.fields.some(f => f.semanticRole === "image_primary" || f.semanticRole === "image_gallery")).map((s, i) => (
                            <div key={i}>
                                <SectionRenderer section={s} />
                            </div>
                        ))}
                    </div>
                    {/* Right: info sections */}
                    <div className="space-y-5">
                        {singleSections.filter(s => !s.fields.some(f => f.semanticRole === "image_primary" || f.semanticRole === "image_gallery")).map((s, i) => (
                            <div key={i} className={i > 0 ? "border-t border-gray-100 pt-5" : ""}>
                                {s.entity && !["Product", "ProductImage"].includes(s.entity) && (
                                    <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-400 mb-3">{s.entity}</h3>
                                )}
                                <SectionRenderer section={s} />
                            </div>
                        ))}
                    </div>
                </div>
            ) : (
                <div className="space-y-6">
                    {singleSections.map((s, i) => (
                        <div key={i} className={i > 0 ? "border-t border-gray-100 pt-6" : ""}>
                            {s.entity && (
                                <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-400 mb-3">{s.entity}</h3>
                            )}
                            <SectionRenderer section={s} />
                        </div>
                    ))}
                </div>
            )}

            {/* Related / multi-instance sections at bottom */}
            {manySection.length > 0 && (
                <div className="border-t border-gray-200 pt-8 space-y-8">
                    {manySection.map((s, i) => (
                        <SectionRenderer key={i} section={s} />
                    ))}
                </div>
            )}
        </div>
    );
}

// ── Main Fragment component ───────────────────────────────────────────────────

const Fragment: React.FC<Props> = ({ pages }) => {
    const [activePageIdx, setActivePageIdx] = React.useState(0);

    if (!pages?.length) {
        return (
            <div className="flex flex-col items-center justify-center py-16 text-gray-400 gap-2">
                <p className="text-sm">No pages generated yet.</p>
                <p className="text-xs">Run the pipeline or use Auto Layout to populate pages.</p>
            </div>
        );
    }

    const activePage = pages[activePageIdx];

    return (
        <div className="flex flex-col gap-0">
            {/* Page tabs */}
            {pages.length > 1 && (
                <div className="flex items-center border-b border-gray-200 bg-gray-50 overflow-x-auto shrink-0">
                    {pages.map((p, i) => (
                        <button
                            key={i}
                            onClick={() => setActivePageIdx(i)}
                            className={`px-4 py-2.5 text-sm font-medium whitespace-nowrap transition-colors ${
                                i === activePageIdx
                                    ? "text-indigo-600 border-b-2 border-indigo-600 bg-white"
                                    : "text-gray-500 hover:text-gray-700"
                            }`}
                        >
                            {p.name}
                        </button>
                    ))}
                </div>
            )}

            {/* Page content */}
            <div className="p-6 overflow-y-auto" style={{ maxHeight: "calc(100vh - 220px)" }}>
                <PageRenderer page={activePage} />
            </div>
        </div>
    );
};

export default Fragment;
