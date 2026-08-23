import { authAxios } from "$auth/state/auth";
import { useQuery } from "@tanstack/react-query";

export const useSystemClasses = (systemId: string) => {
    const queryResult = useQuery({
        queryKey: ["system", "metadata", systemId],
        queryFn: async () => {
            const response = await authAxios.get(`/v1/metadata/systems/${systemId}/classes/`);
            return response.data;
        },
    });

    const classes = queryResult.data?.classifiers || [];

    return [
        classes,
        queryResult.isSuccess,
        queryResult.isLoading,
        queryResult.error,
    ];
};

export const useClassAttributes = (systemId: string, classId: string) => {
    const queryResult = useQuery({
        queryKey: ["system", "metadata", systemId, "class", classId],
        queryFn: async () => {
            if (systemId && classId) {
                const response = await authAxios.get(`/v1/metadata/systems/${systemId}/classifiers/${classId}/`);
                return response.data;
            }
            return [];
        },
    });

    const classAttributes = queryResult.data?.data?.attributes || [];

    return [
        classAttributes,
        queryResult.isSuccess,
        queryResult.isLoading,
        queryResult.error,
    ];
};

export const useClassCustomMethods = (systemId: string, classId: string) => {
    const pythonKeywords = new Set([
        "False", "None", "True", "and", "as", "assert", "async", "await",
        "break", "class", "continue", "def", "del", "elif", "else", "except",
        "finally", "for", "from", "global", "if", "import", "in", "is",
        "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try",
        "while", "with", "yield",
    ]);

    const sanitizeAttributeName = (proposedName: string) => {
        let name = proposedName || globalThis.crypto.randomUUID();
        name = name.replace(/ /g, "_");
        name = name.replace(/-/g, "_");
        while (name.includes("__")) {
            name = name.replace(/__/g, "_");
        }
        if (pythonKeywords.has(name)) {
            name = `nm_${name}`;
        }
        name = name.replace(/[^a-zA-Z0-9_]/g, "");
        if (/^[0-9]/.test(name)) {
            name = `att_${name}`;
        }
        return name;
    };

    const queryResult = useQuery({
        queryKey: ["system", "metadata", systemId, "class", classId, "methods"],
        queryFn: async () => {
            if (systemId && classId) {
                const response = await authAxios.get(`/v1/metadata/systems/${systemId}/classifiers/${classId}/`);
                return response.data;
            }
            return [];
        },
    });

    const classCustomMethods = queryResult.data?.data?.methods || [];
    const classAttributes = queryResult.data?.data?.attributes || [];
    const methodNames = new Set(
        classCustomMethods
            .map((method: { name?: string }) => method?.name)
            .filter((name: string | undefined): name is string => Boolean(name)),
    );
    const aiUserActionMethods = classAttributes.reduce(
        (
            methods: Array<{ name: string; body: string }>,
            attribute: {
                name?: string;
                ai_config?: { trigger?: { type?: string } };
            },
        ) => {
            if (
                attribute.ai_config?.trigger?.type !== "user_action"
                || !attribute.name
            ) {
                return methods;
            }

            const methodName = `generate_${sanitizeAttributeName(attribute.name)}`;
            if (methodNames.has(methodName)) {
                return methods;
            }

            methodNames.add(methodName);
            methods.push({
                name: methodName,
                body: `def ${methodName}(self):\n    pass`,
            });
            return methods;
        },
        [],
    );

    return [
        [...classCustomMethods, ...aiUserActionMethods],
        queryResult.isSuccess,
        queryResult.isLoading,
        queryResult.error,
    ];
};

export const useSystemActors = (systemId: string) => {
    const queryResult = useQuery({
        queryKey: ["system", "metadata", "actors", systemId],
        queryFn: async () => {
            const response = await authAxios.get(`/v1/metadata/systems/${systemId}/actors/`);
            return response.data;
        },
    });

    const actors = queryResult.data?.classifiers || [];

    return [
        actors,
        queryResult.isSuccess,
        queryResult.isLoading,
        queryResult.error,
    ];
};

export const useSystemActions = (systemId: string, nodeType?: string) => {
    const queryResult = useQuery({
        queryKey: ["system", "metadata", "actionnodes", systemId],
        queryFn: async() => {
            const url = nodeType
                ? `/v1/metadata/systems/${systemId}/nodes/?node_type=${nodeType}`
                : `/v1/metadata/systems/${systemId}/nodes/?node_type=action`;
            const response = await authAxios.get(url);
            return response.data;
        },
    });
 
    const actionNodes = queryResult.data || [];
 
    return [
        actionNodes,
        queryResult.isSuccess,
        queryResult.isLoading,
        queryResult.error,
    ]
}
