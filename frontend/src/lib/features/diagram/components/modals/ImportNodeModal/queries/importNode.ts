import { useClassifiers } from "../../../../../../../api/metadata/hooks/classifier";
import type { ClassifierRead } from "../../../../../../../api/metadata/classifier";


type ClassifierType = ClassifierRead["type"];

type ClassifierOfType<T extends ClassifierType> =
  Extract<ClassifierRead, { type: T }>;

const useFilteredSystemClassifiers = <T extends ClassifierType>(
  systemId: string | null | undefined,
  types: readonly T[],
) => {
  const queryResult = useClassifiers(
    { system_id: systemId || undefined },
    !!systemId,
  );

  const classifiers = (queryResult.data ?? []).filter(
    (classifier): classifier is ClassifierOfType<T> =>
      types.some((type) => type === classifier.type),
  );

  return [
    classifiers,
    queryResult.isSuccess,
    queryResult.isLoading,
    queryResult.error,
  ] as const;
};

export const useSystemClassClassifiers = (
  systemId: string | null | undefined,
) => useFilteredSystemClassifiers(systemId, ["enum", "class"]);

export const useSystemActivityClassifiers = (
  systemId: string | null | undefined,
) => useFilteredSystemClassifiers(systemId, ["action"]);

export const useSystemUsecaseClassifiers = (
  systemId: string | null | undefined,
) => useFilteredSystemClassifiers(systemId, ["actor", "usecase"]);

export const useSystemObjectClassifiers = (
  systemId: string | null | undefined,
) => useFilteredSystemClassifiers(systemId, ["class"]);

export const useSystemSignalClassifiers = (
  systemId: string | null | undefined,
) => useFilteredSystemClassifiers(systemId, ["signal"]);

export const useSystemInternalTypeClassifiers = (
  systemId: string | null | undefined,
) =>
  useFilteredSystemClassifiers(systemId, [
    "class",
    "system",
    "container",
    "component",
  ]);
