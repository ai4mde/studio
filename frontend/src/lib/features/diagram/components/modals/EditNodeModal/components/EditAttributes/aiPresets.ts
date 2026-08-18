export type ModelProfile = "cheap" | "strong";

export type AiPreset = {
    id: "late_return_risk" | "reading_plan";
    label: string;
    applicableTo: {
        className: string;
        attributeName: string;
    };
    triggerType: "post_save" | "user_action";
    context: {
        fields?: string[];
        relations?: string[];
    };
    template: {
        name?: string;
        chain?: string[];
    };
    defaultModelProfile: ModelProfile;
    output: {
        format: string;
        allowedValues?: string[];
    };
};

export type BuildAiConfigArgs = {
    preset: AiPreset;
    className: string;
    attributeName: string;
    modelProfile: ModelProfile;
    allowedValues?: string[];
};

export const aiPresets: AiPreset[] = [
    {
        id: "late_return_risk",
        label: "Late return risk",
        applicableTo: {
            className: "BookLoan",
            attributeName: "late_risk",
        },
        triggerType: "post_save",
        context: {
            fields: ["loan_date", "due_date", "return_date"],
            relations: ["Book", "Customer", "Loan"],
        },
        template: {
            name: "library_late_risk_v1",
        },
        defaultModelProfile: "cheap",
        output: {
            allowedValues: ["LOW", "MEDIUM", "HIGH"],
            format: "risk_label",
        },
    },
    {
        id: "reading_plan",
        label: "Reading plan",
        applicableTo: {
            className: "Customer",
            attributeName: "reading_plan",
        },
        triggerType: "user_action",
        context: {
            relations: ["Loan", "BookLoan", "Book"],
        },
        template: {
            chain: [
                "reading_plan_analyze_taste_v1",
                "reading_plan_recommend_v1",
                "reading_plan_sequence_v1",
            ],
        },
        defaultModelProfile: "strong",
        output: {
            format: "reading_plan",
        },
    },
];

export function findAiPreset(id: string | undefined): AiPreset | undefined {
    return aiPresets.find((preset) => preset.id === id);
}

export function presetsFor(className: string | undefined, attributeName: string | undefined): AiPreset[] {
    return aiPresets.filter(
        (preset) =>
            preset.applicableTo.className === className &&
            preset.applicableTo.attributeName === attributeName,
    );
}

export function inferPresetId(aiConfig: any): AiPreset["id"] | undefined {
    if (aiConfig?.template?.name === "library_late_risk_v1") {
        return "late_return_risk";
    }
    if (
        Array.isArray(aiConfig?.template?.chain) &&
        aiConfig.template.chain.includes("reading_plan_sequence_v1")
    ) {
        return "reading_plan";
    }
    return undefined;
}

export function parseAllowedValues(value: string): string[] {
    return value
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean);
}

export function buildAiConfig({
    preset,
    className,
    attributeName,
    modelProfile,
    allowedValues,
}: BuildAiConfigArgs) {
    const output: Record<string, any> = {
        format: preset.output.format,
        write_back: attributeName,
    };
    if (preset.output.allowedValues) {
        output.allowed_values =
            allowedValues && allowedValues.length > 0
                ? allowedValues
                : preset.output.allowedValues;
    }

    const context: Record<string, string[]> = {};
    if (preset.context.fields) context.fields = [...preset.context.fields];
    if (preset.context.relations) context.relations = [...preset.context.relations];

    const template = preset.template.name
        ? { name: preset.template.name }
        : { chain: [...(preset.template.chain ?? [])] };

    return {
        ai_config_version: "1.0",
        context,
        model_profile: modelProfile,
        output,
        template,
        trigger: {
            class: className,
            type: preset.triggerType,
        },
    };
}
