import {
    Chip,
    Divider,
    FormControl,
    FormLabel,
    Switch,
} from "@mui/joy";
import { isEqual } from "lodash";
import React, { useEffect, useMemo, useState } from "react";
import {
    AiPreset,
    ModelProfile,
    buildAiConfig,
    findAiPreset,
    inferPresetId,
    parseAllowedValues,
    presetsFor,
} from "./aiPresets";

type Props = {
    attribute: any;
    className: string;
    update: (value: any) => void;
};

const modelProfiles: ModelProfile[] = ["cheap", "strong"];

function valuesText(values: string[] | undefined): string {
    return (values ?? []).join(", ");
}

function existingAllowedValues(attribute: any): string[] | undefined {
    const values = attribute?.ai_config?.output?.allowed_values;
    return Array.isArray(values) ? values : undefined;
}

function SemanticChips({ values }: { values?: string[] }) {
    if (!values || values.length === 0) return <span className="text-xs text-gray-500">None</span>;
    return (
        <span className="flex flex-row flex-wrap gap-1">
            {values.map((value) => (
                <Chip key={value} size="sm" variant="soft">
                    {value}
                </Chip>
            ))}
        </span>
    );
}

const UnsupportedAiConfigSection: React.FC<Props> = ({ attribute, update }) => {
    const disableAiConfig = () => {
        const { ai_config, ...attributeWithoutAiConfig } = attribute;
        update(attributeWithoutAiConfig);
    };

    return (
        <div
            className="flex flex-col gap-2 border-t border-solid border-gray-200 bg-white px-2 py-2 text-xs"
            data-t4-ai-config-section={attribute?.name ?? ""}
            data-t5-ai-config-section={attribute?.name ?? ""}
        >
            <FormControl orientation="horizontal">
                <Switch
                    size="sm"
                    checked
                    onChange={(event) => {
                        if (!event.target.checked) disableAiConfig();
                    }}
                />
                <FormLabel sx={{ marginLeft: "8px", marginTop: "2px" }}>
                    AI-managed attribute
                </FormLabel>
            </FormControl>
            <div className="rounded border border-solid border-gray-200 bg-gray-50 p-2 text-gray-600">
                Custom / unsupported configuration - edit via import
            </div>
        </div>
    );
};

const EditableAiConfigSection: React.FC<
    Props & {
        applicablePresets: AiPreset[];
        enabled: boolean;
        selectedPreset: AiPreset;
    }
> = ({ attribute, className, update, applicablePresets, enabled, selectedPreset }) => {
    const modelProfile = (attribute?.ai_config?.model_profile ??
        selectedPreset.defaultModelProfile) as ModelProfile;
    const inferredPresetId = inferPresetId(attribute?.ai_config);
    const configAllowedValues = existingAllowedValues(attribute);
    const presetAllowedValues = selectedPreset.output.allowedValues;
    const configAllowedValuesKey = JSON.stringify(configAllowedValues ?? null);
    const presetAllowedValuesKey = JSON.stringify(presetAllowedValues ?? null);
    const [allowedValuesText, setAllowedValuesText] = useState(
        valuesText(configAllowedValues ?? presetAllowedValues),
    );

    useEffect(() => {
        setAllowedValuesText(valuesText(configAllowedValues ?? presetAllowedValues));
    }, [inferredPresetId, configAllowedValuesKey, presetAllowedValuesKey]);

    const effectiveAllowedValues = useMemo(
        () => (presetAllowedValues ? configAllowedValues ?? presetAllowedValues : undefined),
        [configAllowedValues, presetAllowedValues],
    );
    const dynamicAiConfig = useMemo(() => {
        if (!enabled) return null;
        return buildAiConfig({
            preset: selectedPreset,
            className,
            attributeName: attribute?.name ?? "",
            modelProfile,
            allowedValues: effectiveAllowedValues,
        });
    }, [
        attribute?.name,
        className,
        effectiveAllowedValues,
        enabled,
        modelProfile,
        selectedPreset,
    ]);

    const applyConfig = (
        preset: AiPreset,
        nextModelProfile: ModelProfile,
        nextAllowedValues?: string[],
    ) => {
        update({
            ...attribute,
            ai_config: buildAiConfig({
                preset,
                className,
                attributeName: attribute?.name ?? "",
                modelProfile: nextModelProfile,
                allowedValues: nextAllowedValues,
            }),
        });
    };

    useEffect(() => {
        if (!enabled || !selectedPreset || !dynamicAiConfig) return;
        if (!isEqual(dynamicAiConfig, attribute.ai_config)) {
            update({ ...attribute, ai_config: dynamicAiConfig });
        }
    }, [attribute, dynamicAiConfig, enabled, selectedPreset, update]);

    const disableAiConfig = () => {
        const { ai_config, ...attributeWithoutAiConfig } = attribute;
        update(attributeWithoutAiConfig);
    };

    const enableAiConfig = () => {
        const preset = selectedPreset ?? applicablePresets[0];
        if (!preset) return;
        const nextAllowedValues = preset.output.allowedValues ?? undefined;
        setAllowedValuesText(valuesText(nextAllowedValues));
        applyConfig(preset, preset.defaultModelProfile, nextAllowedValues);
    };

    const handlePresetChange = (value: string) => {
        const preset = applicablePresets.find((candidate) => candidate.id === value);
        if (!preset) return;
        const nextAllowedValues = preset.output.allowedValues ?? undefined;
        setAllowedValuesText(valuesText(nextAllowedValues));
        applyConfig(preset, preset.defaultModelProfile, nextAllowedValues);
    };

    const handleModelProfileChange = (value: string) => {
        applyConfig(
            selectedPreset,
            value as ModelProfile,
            effectiveAllowedValues,
        );
    };

    const handleAllowedValuesChange = (value: string) => {
        setAllowedValuesText(value);
    };

    const handleAllowedValuesBlur = () => {
        if (!selectedPreset) return;
        applyConfig(
            selectedPreset,
            modelProfile,
            presetAllowedValues ? parseAllowedValues(allowedValuesText) : undefined,
        );
    };

    return (
        <div
            className="flex flex-col gap-2 border-t border-solid border-gray-200 bg-white px-2 py-2 text-xs"
            data-t4-ai-config-section={attribute?.name ?? ""}
            data-t5-ai-config-section={attribute?.name ?? ""}
        >
            <FormControl orientation="horizontal">
                <Switch
                    size="sm"
                    checked={enabled}
                    disabled={!enabled && Boolean(attribute?.derived)}
                    onChange={(event) => {
                        if (event.target.checked) enableAiConfig();
                        else disableAiConfig();
                    }}
                />
                <FormLabel sx={{ marginLeft: "8px", marginTop: "2px" }}>
                    AI-managed attribute
                </FormLabel>
            </FormControl>
            {!enabled && Boolean(attribute?.derived) && (
                <p className="text-[10px] leading-tight text-gray-500">
                    Not available: a derived property is generated as a read-only
                    <code> @property</code>, so it cannot also be written by an AI model.
                    Turn off <em>derived</em> first.
                </p>
            )}

            {enabled && (
                <div className="flex flex-col gap-2">
                    <FormControl>
                        <FormLabel>Preset</FormLabel>
                        <select
                            data-t4-ai-preset={attribute?.name ?? ""}
                            className="rounded border border-solid border-gray-300 bg-white p-1 font-mono text-xs"
                            value={selectedPreset.id}
                            onInput={(event) => handlePresetChange(event.currentTarget.value)}
                            onChange={(event) => handlePresetChange(event.currentTarget.value)}
                        >
                            {applicablePresets.map((preset) => (
                                <option key={preset.id} value={preset.id}>
                                    {preset.label}
                                </option>
                            ))}
                        </select>
                    </FormControl>

                    <div className="grid grid-cols-[8rem_1fr] gap-x-3 gap-y-2 rounded border border-solid border-gray-200 p-2">
                        <span className="font-bold">Trigger</span>
                        <span className="flex flex-row flex-wrap gap-1">
                            <Chip size="sm" variant="soft">
                                {selectedPreset.triggerType}
                            </Chip>
                            <Chip size="sm" variant="soft">
                                {className || "Class"}
                            </Chip>
                        </span>

                        <span className="font-bold">Context</span>
                        <span className="flex flex-col gap-1">
                            <span className="flex flex-row items-center gap-1">
                                <span>Fields</span>
                                <SemanticChips values={selectedPreset.context.fields} />
                            </span>
                            <span className="flex flex-row items-center gap-1">
                                <span>Relations</span>
                                <SemanticChips values={selectedPreset.context.relations} />
                            </span>
                        </span>

                        <span className="font-bold">Template</span>
                        <span className="flex flex-col gap-1">
                            {selectedPreset.template.name && (
                                <Chip size="sm" variant="soft">
                                    {selectedPreset.template.name}
                                </Chip>
                            )}
                            {selectedPreset.template.chain?.map((step) => (
                                <Chip key={step} size="sm" variant="soft">
                                    {step}
                                </Chip>
                            ))}
                        </span>

                        <span className="font-bold">Model profile</span>
                        <select
                            data-t4-model-profile={attribute?.name ?? ""}
                            className="rounded border border-solid border-gray-300 bg-white p-1 font-mono text-xs"
                            value={modelProfile}
                            onInput={(event) => handleModelProfileChange(event.currentTarget.value)}
                            onChange={(event) => handleModelProfileChange(event.currentTarget.value)}
                        >
                            {modelProfiles.map((profile) => (
                                <option key={profile} value={profile}>
                                    {profile}
                                </option>
                            ))}
                        </select>

                        <span className="font-bold">Output</span>
                        <span className="flex flex-col gap-2">
                            <span className="flex flex-row items-center gap-1">
                                <span>Writes to</span>
                                <Chip size="sm" variant="soft">
                                    {attribute?.name ?? ""}
                                </Chip>
                            </span>
                            <span className="flex flex-row items-center gap-1">
                                <span>Format</span>
                                <Chip size="sm" variant="soft">
                                    {selectedPreset.output.format}
                                </Chip>
                            </span>
                            {presetAllowedValues && (
                                <>
                                    <Divider />
                                    <FormControl>
                                        <FormLabel>Allowed values</FormLabel>
                                        <input
                                            data-t4-allowed-values={attribute?.name ?? ""}
                                            className="rounded border border-solid border-gray-300 bg-white p-1 font-mono text-xs"
                                            value={allowedValuesText}
                                            onInput={(event) => handleAllowedValuesChange(event.currentTarget.value)}
                                            onChange={(event) => handleAllowedValuesChange(event.currentTarget.value)}
                                            onBlur={handleAllowedValuesBlur}
                                        />
                                    </FormControl>
                                </>
                            )}
                        </span>
                    </div>
                </div>
            )}
        </div>
    );
};

const AiConfigSection: React.FC<Props> = ({ attribute, className, update }) => {
    const enabled = Boolean(attribute?.ai_config);
    const applicablePresets = presetsFor(className, attribute?.name);
    if (applicablePresets.length === 0 && !enabled) return null;

    const inferredPresetId = inferPresetId(attribute?.ai_config);
    const inferredPreset = findAiPreset(inferredPresetId);
    const selectedPreset = enabled
        ? applicablePresets.find((preset) => preset.id === inferredPreset?.id)
        : applicablePresets[0];
    const unsupportedExistingConfig = enabled && (!inferredPreset || !selectedPreset);

    if (unsupportedExistingConfig) {
        return (
            <UnsupportedAiConfigSection
                attribute={attribute}
                className={className}
                update={update}
            />
        );
    }

    if (!selectedPreset) return null;

    return (
        <EditableAiConfigSection
            attribute={attribute}
            className={className}
            update={update}
            applicablePresets={applicablePresets}
            enabled={enabled}
            selectedPreset={selectedPreset}
        />
    );
};

export default AiConfigSection;
