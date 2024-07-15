import { useQuery } from "@tanstack/react-query";
import { authAxios } from "$auth/state/auth";

export const useSystemInterfaces = (systemId: string) => {
    const queryResult = useQuery({
        queryKey: ["metdata", "interfaces", systemId],
        queryFn: async () => {
            const response = await authAxios.get(`/v1/metadata/interfaces/`, {
                params: {
                    system: systemId
                }
            });
            return response.data;
        },
    });


    const interfaces = queryResult.data || [];
    console.log(interfaces);

    return [
        interfaces,
        queryResult.isSuccess,
        queryResult.isLoading,
        queryResult.error,
    ];
};