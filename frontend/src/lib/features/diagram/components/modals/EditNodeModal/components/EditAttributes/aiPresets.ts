export type ModelProfile = "cheap" | "strong";
export type AiPreset = {
    id: "late_return_risk" | "reading_plan";
    label: string;
    applicableTo: { className: string; attributeName: string };
    defaultModelProfile: ModelProfile;
};
export const aiPresets: AiPreset[] = [
    { id: "late_return_risk", label: "Late return risk",
      applicableTo: { className: "BookLoan", attributeName: "late_risk" }, defaultModelProfile: "cheap" },
    { id: "reading_plan", label: "Reading plan",
      applicableTo: { className: "Customer", attributeName: "reading_plan" }, defaultModelProfile: "strong" },
];
export const readingChain = ["reading_plan_analyze_taste_v1", "reading_plan_recommend_v1", "reading_plan_sequence_v1"];
export const findAiPreset = (id: string | undefined) => aiPresets.find(p => p.id === id);
export const presetsFor = (className?: string, attributeName?: string) =>
    aiPresets.filter(p => p.applicableTo.className === className && p.applicableTo.attributeName === attributeName);

// Recognition only identifies the preset; callers must separately validate its version and content.
export function inferPresetId(config: any): AiPreset["id"] | undefined {
    if (["library_late_risk_v1", "library_late_risk_v2", "library_late_risk_v3"].includes(config?.template?.name))
        return "late_return_risk";
    if (JSON.stringify(config?.template?.chain) === JSON.stringify(readingChain)) return "reading_plan";
}
export const parseAllowedValues = (text: string) => text.split(",").map(s => s.trim());

export type BuildAiConfigArgs = {
    preset: AiPreset; className: string; attributeName: string;
    modelProfile: ModelProfile; allowedValues?: string[];
};
export function buildAiConfig({ preset, className, attributeName, modelProfile, allowedValues }: BuildAiConfigArgs) {
    const risk = preset.id === "late_return_risk";
    return {
        ai_config_version: "1.2",
        trigger: { type: risk ? "post_save" : "user_action", class: className, ...(risk ? { on: "create" } : {}) },
        context: {
            ...(risk ? { fields: ["loan_date", "due_date"] } : {}),
            relations: risk ? ["Book", "Customer", "Loan"] : ["Loan", "BookLoan", "Book"],
            history: { scope: "Loan.Customer", unit: "book_loan", completed_only: true, as_of: risk ? "loan_date" : "today",
                order_by: "-return_date", limit: risk ? 10 : 20, max_scan_records: 200 },
        },
        template: risk ? { name: "library_late_risk_v3" } : { chain: [...readingChain] },
        model_profile: modelProfile,
        output: { format: risk ? "risk_label" : "reading_plan", write_back: attributeName,
            on_skip: risk ? "NOT_ASSESSED" : "Not assessed",
            ...(risk ? { allowed_values: allowedValues ?? ["LOW", "MEDIUM", "HIGH"],
                reason: { required: true, max_length: 120 } } : {}),
        },
    };
}

// UI validation mirrors the supported contract; generation/runtime remain authoritative.
function validateVersion(config: any, preset: AiPreset, version: "1.1" | "1.2"): string | undefined {
    try {
        const fail = (key: string, message: string): never => { throw new Error(key + ": " + message); };
        const object = (value: any, path: string, required: string[], optional: string[] = []) => {
            if (!value || typeof value !== "object" || Array.isArray(value)) fail(path, "object required");
            required.forEach(k => { if (!(k in value)) fail(path + "." + k, "required"); });
            Object.keys(value).forEach(k => { if (![...required, ...optional].includes(k)) fail(path + "." + k, "unsupported key"); });
        };
        const same = (value: any, expected: any, key: string) => {
            if (JSON.stringify(value) !== JSON.stringify(expected)) fail(key, "unsupported value");
        };
        const text = (value: any, key: string, max: number) => {
            if (typeof value !== "string" || !value.trim() || value !== value.trim() || value.length > max)
                fail(key, "nonblank, trimmed text required (max " + max + ")");
        };
        const integer = (value: any, key: string, low: number, high: number) => {
            if (!Number.isInteger(value) || value < low || value > high) fail(key, "integer " + low + "–" + high + " required");
        };
        const risk = preset.id === "late_return_risk";
        object(config, "config", ["ai_config_version", "trigger", "context", "template", "model_profile", "output"]);
        same(config.ai_config_version, version, "ai_config_version");
        object(config.trigger, "trigger", risk ? ["class", "type", "on"] : ["class", "type"]);
        same(config.trigger.class, preset.applicableTo.className, "trigger.class");
        same(config.trigger.type, risk ? "post_save" : "user_action", "trigger.type");
        if (risk) same(config.trigger.on, "create", "trigger.on");
        object(config.context, "context", ["history"], ["fields", "relations"]);
        for (const key of ["fields", "relations"]) {
            const values = config.context[key];
            if (values !== undefined && (!Array.isArray(values) || values.some((v: any) => typeof v !== "string")))
                fail("context." + key, "string list required");
        }
        const h = config.context.history;
        const budget = version === "1.2" ? "max_scan_records" : "max_scan_loans";
        object(h, "context.history", ["scope", "completed_only", "as_of", "order_by", "limit", budget, ...(version === "1.2" ? ["unit"] : [])]);
        if (version === "1.2") same(h.unit, "book_loan", "context.history.unit");
        same(h.scope, "Loan.Customer", "context.history.scope");
        same(h.completed_only, true, "context.history.completed_only");
        same(h.as_of, risk ? "loan_date" : "today", "context.history.as_of");
        if (!["-return_date", "-loan_date"].includes(h.order_by)) fail("context.history.order_by", "unsupported ordering");
        integer(h.limit, "context.history.limit", 1, 50);
        integer(h[budget], "context.history." + budget, h.limit, 1000);
        object(config.template, "template", risk ? ["name"] : ["chain"]);
        same(risk ? config.template.name : config.template.chain, risk ? (version === "1.2" ? "library_late_risk_v3" : "library_late_risk_v2") : readingChain, "template");
        if (!["cheap", "strong"].includes(config.model_profile)) fail("model_profile", "unknown profile");
        const o = config.output;
        object(o, "output", ["format", "write_back", "on_skip", ...(risk ? ["allowed_values", "reason"] : [])]);
        same(o.format, risk ? "risk_label" : "reading_plan", "output.format");
        same(o.write_back, preset.applicableTo.attributeName, "output.write_back");
        text(o.on_skip, "output.on_skip", 255);
        if (risk) {
            if (!Array.isArray(o.allowed_values) || o.allowed_values.length < 2 || o.allowed_values.length > 5)
                fail("output.allowed_values", "2–5 labels required, ordered from lower to higher risk");
            o.allowed_values.forEach((v: any) => text(v, "output.allowed_values", 32));
            if (new Set(o.allowed_values).size !== o.allowed_values.length || o.allowed_values.includes(o.on_skip))
                fail("output.allowed_values", "labels must be unique and exclude on_skip");
            object(o.reason, "output.reason", ["required", "max_length"]);
            same(o.reason.required, true, "output.reason.required");
            integer(o.reason.max_length, "output.reason.max_length", 1, 120);
        }
    } catch (error) { return (error as Error).message; }
}

export const validateAiConfig = (config: any, preset: AiPreset) => validateVersion(config, preset, "1.2");
export const validatePreviousAiConfig = (config: any, preset: AiPreset) => validateVersion(config, preset, "1.1");

// Explicit preset reset, not a value-preserving cross-version migration.
export function upgradeAiConfig(previous: any, preset: AiPreset) {
    const error = validatePreviousAiConfig(previous, preset);
    if (error || inferPresetId(previous) !== preset.id) throw new Error(error ?? "Unrecognized preset");
    return buildAiConfig({preset, className: preset.applicableTo.className,
        attributeName: preset.applicableTo.attributeName, modelProfile: preset.defaultModelProfile});
}
