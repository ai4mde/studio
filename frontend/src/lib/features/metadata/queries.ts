import { useQuery } from "@tanstack/react-query";
import { authAxios } from "../auth/state/auth";

export const useSystemMetadata = (systemId: string) =>
    useQuery({
        queryKey: ["system", "metadata", `${systemId}`],
        queryFn: async () => {
            const response = await authAxios.get(
                `/v1/metadata/systems/${systemId}/meta/`,
            );
            return response.data;
        },
    });
