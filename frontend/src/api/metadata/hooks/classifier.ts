
import { useQuery } from "@tanstack/react-query";

import { listClassifiers } from "../classifier";
import type { ClassifierFilters } from "../classifier";

export const useClassifiers = (filters: ClassifierFilters = {}) => {
    return useQuery({
        queryKey: ["classifiers", filters],
        queryFn: () => listClassifiers(filters),
    });
};
