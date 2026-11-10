// The frontend still uses the old (mostly camelCase) names for some classifier
// fields, the new backend uses snake_case. Map between them in one place so
// the components don't have to know about it.
const FRONTEND_TO_API: Record<string, string> = {
    isAutomatic: "is_automatic",
    customCode: "custom_code",
    cls: "uml_class",
};

const API_TO_FRONTEND: Record<string, string> = Object.fromEntries(
    Object.entries(FRONTEND_TO_API).map(([frontend, api]) => [api, frontend]),
);

const renameKeys = (
    data: Record<string, any>,
    mapping: Record<string, string>,
) =>
    Object.fromEntries(
        Object.entries(data ?? {}).map(([key, value]) => [
            mapping[key] ?? key,
            value,
        ]),
    );

export const classifierDataToApi = (data: Record<string, any>) =>
    renameKeys(data, FRONTEND_TO_API);

export const classifierDataFromApi = (data: Record<string, any>) =>
    renameKeys(data, API_TO_FRONTEND);

// Classifier types that are spelled differently on the frontend
const TYPE_FRONTEND_TO_API: Record<string, string> = {
    system_boundary: "systemboundary",
};

const TYPE_API_TO_FRONTEND: Record<string, string> = Object.fromEntries(
    Object.entries(TYPE_FRONTEND_TO_API).map(([frontend, api]) => [api, frontend]),
);

export const classifierTypeToApi = (type: string) =>
    TYPE_FRONTEND_TO_API[type] ?? type;

export const classifierTypeFromApi = (type: string) =>
    TYPE_API_TO_FRONTEND[type] ?? type;

// Multiplicity is shown as "1", "0..1", "*" or "1..*" in the UI,
// the backend stores a lower and an upper bound (null means *)
const MULTIPLICITY_BOUNDS: Record<string, [number, number | null]> = {
    "1": [1, 1],
    "0..1": [0, 1],
    "*": [0, null],
    "1..*": [1, null],
};

const boundsToText = (lower: number, upper: number | null) =>
    Object.entries(MULTIPLICITY_BOUNDS).find(
        ([, [l, u]]) => l === lower && u === upper,
    )?.[0] ?? `${lower}..${upper ?? "*"}`;

export const multiplicityToApi = (multiplicity?: { source?: string; target?: string }) => {
    const [source_lower, source_upper] = MULTIPLICITY_BOUNDS[multiplicity?.source ?? "1"] ?? [1, 1];
    const [target_lower, target_upper] = MULTIPLICITY_BOUNDS[multiplicity?.target ?? "1"] ?? [1, 1];
    return { source_lower, source_upper, target_lower, target_upper };
};

export const multiplicityFromApi = (multiplicity?: any) =>
    multiplicity
        ? {
              source: boundsToText(multiplicity.source_lower, multiplicity.source_upper),
              target: boundsToText(multiplicity.target_lower, multiplicity.target_upper),
          }
        : undefined;