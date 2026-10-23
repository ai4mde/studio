import { FormControl, FormLabel, Switch } from "@mui/joy";
import React, { useState } from "react";
import { AiPreset, buildAiConfig, inferPresetId, parseAllowedValues, presetsFor, upgradeAiConfig, validateAiConfig, validatePreviousAiConfig } from "./aiPresets";

type Props = { attribute: any; className: string; update: (value: any) => void };

function DraftField({ label, value, commit, testId }: {
    label: string; value: string; commit: (value: string) => void; testId?: string;
}) {
    const [draft, setDraft] = useState(value);
    return <label className="flex flex-col gap-1">{label}
        <input aria-label={label} className="rounded border border-solid border-gray-300 p-1"
            data-t4-allowed-values={testId} value={draft}
            onChange={e => setDraft(e.target.value)} onBlur={() => commit(draft)} />
    </label>;
}

function ConfigEditor({ config, preset, apply }: { config: any; preset: AiPreset; apply: (next: any) => void }) {
    const risk = preset.id === "late_return_risk";
    const history = config.context?.history ?? {};
    const output = config.output ?? {};
    // Only the edited path is replaced. Imported policies and future descriptive data are preserved.
    const editHistory = (key: string, value: any) => apply({
        ...config, context: { ...config.context, history: { ...history, [key]: value } },
    });
    const editOutput = (key: string, value: any) => apply({ ...config, output: { ...output, [key]: value } });
    return <div className="flex flex-col gap-2">
        <div className="rounded border border-solid border-gray-200 p-2">
            <strong>{preset.label} · v1.2</strong>
            <p>{risk ? "Assessed on creation; later saves retain the checkout snapshot." : "Generate a plan from books borrowed and returned."}</p>
            <p>Completed book borrowing records only · as of {history.as_of} · order {history.order_by} · scan budget {history.max_scan_records}</p>
            <p>Trigger: {config.trigger?.type}{risk ? " / create" : ""} · writes to {output.write_back}</p>
            <p>Template: {config.template?.name ?? config.template?.chain?.join(" → ")}</p>
            {risk && <p>Reason required, up to {output.reason?.max_length} characters. Labels run from lower to higher risk.</p>}
        </div>
        <label>Model profile
            <select aria-label="Model profile" data-t4-model-profile={preset.applicableTo.attributeName}
                value={config.model_profile} onChange={e => apply({ ...config, model_profile: e.target.value })}>
                <option value="cheap">cheap</option><option value="strong">strong</option>
            </select>
        </label>
        <DraftField key={"limit-" + history.limit} label="History limit" value={String(history.limit ?? "")}
            commit={v => editHistory("limit", /^\d+$/.test(v) ? Number(v) : v)} />
        {risk && <DraftField key={"labels-" + JSON.stringify(output.allowed_values)} label="Allowed values"
            testId={preset.applicableTo.attributeName} value={(output.allowed_values ?? []).join(", ")}
            commit={v => editOutput("allowed_values", parseAllowedValues(v))} />}
        <DraftField key={"skip-" + output.on_skip} label="On skip" value={output.on_skip ?? ""}
            commit={v => editOutput("on_skip", v.trim())} />
    </div>;
}

const AiConfigSection: React.FC<Props> = ({ attribute, className, update }) => {
    const [error, setError] = useState<string>();
    const config = attribute?.ai_config;
    const preset = presetsFor(className, attribute?.name)[0];
    if (!config && !preset) return null;
    const supported = preset && inferPresetId(config) === preset.id;
    const resetError = config && supported ? validatePreviousAiConfig(config, preset) : "Unrecognized preset";
    const canReset = Boolean(config && supported && config.ai_config_version === "1.1" && !resetError);
    // Not resettable does not mean editable: 1.0 must never enter the 1.2 editor.
    const currentError = config && supported ? validateAiConfig(config, preset) : "Unrecognized preset";
    const editable = Boolean(config && supported && config.ai_config_version === "1.2" && !currentError);
    const resetPreview = canReset ? upgradeAiConfig(config, preset!) : undefined;
    const apply = (next: any) => {
        const problem = preset ? validateAiConfig(next, preset) : "Unsupported configuration";
        setError(problem);
        if (!problem) update({ ...attribute, ai_config: next });
    };
    const toggle = (enabled: boolean) => {
        setError(undefined);
        if (!enabled) {
            const { ai_config: _removed, ...rest } = attribute;
            update(rest);
        } else if (preset) {
            apply(buildAiConfig({ preset, className, attributeName: attribute.name, modelProfile: preset.defaultModelProfile }));
        }
    };
    return <div className="flex flex-col gap-2 border-t border-solid border-gray-200 bg-white px-2 py-2 text-xs"
        data-t4-ai-config-section={attribute?.name ?? ""} data-t5-ai-config-section={attribute?.name ?? ""}>
        <FormControl orientation="horizontal">
            <Switch size="sm" checked={Boolean(config)} disabled={Boolean(config && !editable && !canReset) || (!config && (Boolean(attribute?.derived) || attribute?.type !== "str"))}
                slotProps={{ input: { "aria-label": "AI-managed attribute" } }}
                onChange={event => toggle(event.target.checked)} />
            <FormLabel sx={{ marginLeft: "8px" }}>AI-managed attribute</FormLabel>
        </FormControl>
        {!config && (attribute?.derived || attribute?.type !== "str") && <p>Requires a stored string attribute.</p>}
        {config && !editable && !canReset && <div>Custom / unsupported configuration — original content retained.
            <p role="alert">{config.ai_config_version === "1.1" ? resetError : currentError}</p>
            <pre className="overflow-auto">{JSON.stringify(config, null, 2)}</pre></div>}
        {canReset && <div>
            <p>This reset replaces all preset settings, including model profile, history order, limit and scan budget
                {preset?.id === "late_return_risk" ? ", labels, on-skip value and reason limit" : " and on-skip value"}.
                History now counts BookLoan records instead of Loan groups. Equal numbers do not imply equal coverage.
                The scan key becomes max_scan_records; the risk template becomes v3. The class diagram and database are not migrated.</p>
            <p>Original configuration</p><pre>{JSON.stringify(config, null, 2)}</pre>
            <p>New preset defaults</p><pre>{JSON.stringify(resetPreview, null, 2)}</pre>
            <button type="button" onClick={() => {
                try { apply(upgradeAiConfig(config, preset!)); }
                catch (problem) { setError((problem as Error).message); }
            }}>Reset to v1.2 preset</button>
        </div>}
        {editable && <ConfigEditor config={config} preset={preset!} apply={apply} />}
        {error && <p role="alert" className="text-red-700">{error}</p>}
    </div>;
};
export default AiConfigSection;
