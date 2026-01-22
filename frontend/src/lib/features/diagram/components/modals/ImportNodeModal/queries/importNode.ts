import { authAxios } from "$lib/features/auth/state/auth";
import { useQuery } from "@tanstack/react-query";

export type SystemClassifier = {
  id: string;
  system_id?: string;
  system_name?: string;
  data?: {
    type?: string;
    name?: string;
    // allow arbitrary extra fields without becoming `unknown`
    [key: string]: any;
  };
  // allow other fields without becoming `unknown`
  [key: string]: any;
};

type ClassifiersResponse = {
  classifiers?: SystemClassifier[];
};

// Shared query: fetch all classifiers for a system (project-wide)
const useSystemClassifiersQuery = (systemId: string | null | undefined) =>
  useQuery<ClassifiersResponse>({
    queryKey: ["system", "metadata", systemId],
    enabled: !!systemId,
    queryFn: async () => {
      const response = await authAxios.get(
        `/v1/metadata/systems/${systemId}/classifiers/`,
      );
      return response.data as ClassifiersResponse;
    },
  });

// Shared helper: apply a filter predicate to classifiers
const useFilteredSystemClassifiers = (
  systemId: string | null | undefined,
  predicate: (classifier: SystemClassifier) => boolean,
) => {
  const queryResult = useSystemClassifiersQuery(systemId);

  const classifiers =
    queryResult.data?.classifiers?.filter(predicate) ?? [];

  return [
    classifiers,
    queryResult.isSuccess,
    queryResult.isLoading,
    queryResult.error,
  ] as const;
};

export const useSystemClassClassifiers = (
  systemId: string | null | undefined,
) =>
  useFilteredSystemClassifiers(systemId, (classifier) => {
    const t = classifier.data?.type;
    return t === "enum" || t === "class";
  });

export const useSystemActivityClassifiers = (
  systemId: string | null | undefined,
) =>
  useFilteredSystemClassifiers(systemId, (classifier) => {
    const t = classifier.data?.type;
    return t === "action";
  });

export const useSystemUsecaseClassifiers = (
  systemId: string | null | undefined,
) =>
  useFilteredSystemClassifiers(systemId, (classifier) => {
    const t = classifier.data?.type;
    return t === "actor" || t === "usecase";
  });
