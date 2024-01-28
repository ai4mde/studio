import { authAxios } from "$lib/features/auth/state/auth";
import { useQuery } from "@tanstack/react-query";

export const useDiagram = (diagram: string) => {
    return useQuery<any, Error>({
        queryKey: ["diagram", diagram],
        queryFn: async () => {
            return (await authAxios.get(`/v1/diagram/${diagram}`)).data;
        },
    });
};
