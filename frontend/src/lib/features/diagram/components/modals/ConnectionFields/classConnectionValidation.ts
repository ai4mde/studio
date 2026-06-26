const isNonEmpty = (v: unknown): boolean =>
    typeof v === "string" && v.trim().length > 0;

export const isClassConnectionValid = (object: any): boolean => {
    const relType = object?.type;
    const mult = object?.multiplicity ?? {};

    if (relType === "association") {
        return (
            isNonEmpty(object?.label) &&
            isNonEmpty(mult.source) &&
            isNonEmpty(mult.target)
        );
    }

    if (relType === "composition") {
        return (
            isNonEmpty(mult.source) &&
            isNonEmpty(mult.target)
        );
    }

    return !!relType;
};
