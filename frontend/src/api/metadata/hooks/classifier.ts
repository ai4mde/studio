import { useQuery } from "@tanstack/react-query";

import { queryKeys } from "../../querykeys";
import { listClassifiers } from "../classifier";
import type { ClassifierFilters } from "../classifier";

export const useClassifiers = (
  filters: ClassifierFilters = {},
  enabled = true,
) => {
  return useQuery({
    queryKey: queryKeys.classifiers.list(filters),
    queryFn: () => listClassifiers(filters),
    enabled,
  });
};

export const useClassifier = (
    systemId: string | null | undefined,
    classifierId: string | null | undefined,
) => {
    const query = useClassifiers(
        { system_id: systemId || undefined },
        !!systemId && !!classifierId,
    );

    return {
        ...query,
        data: query.data?.find(
            (classifier) => classifier.id === classifierId,
        ),
    };
};
