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
