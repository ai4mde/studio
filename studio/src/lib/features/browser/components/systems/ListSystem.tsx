import { authAxios } from "$lib/features/auth/state/auth";
import { CircularProgress } from "@mui/joy";
import { useAtom } from "jotai";
import { Plus } from "lucide-react";
import React from "react";
import { useQuery } from "react-query";
import { createSystemAtom } from "../../atoms";

type SystemOut = {
    id: string;
    name: string;
    description?: string;
};

type Props = {
    project: string;
};

export const ListSystem: React.FC<Props> = ({ project }) => {
    const systems = useQuery<SystemOut[]>({
        queryKey: ["systems", `${project}`],
        queryFn: async () => {
            return (
                await authAxios.get(`/v1/metadata/systems/`, {
                    params: {
                        project: project,
                    },
                })
            ).data;
        },
        enabled: !!project,
    });

    const [, setCreate] = useAtom(createSystemAtom);

    return (
        <>
            <div className="flex flex-col">
                <h1 className="text-lg">Systems</h1>
                <div className="flex flex-row">
                    {systems.isLoading && (
                        <CircularProgress className="animate-spin" />
                    )}
                    {systems.isSuccess &&
                        systems.data.map((e) => (
                            <a
                                href={`/projects/${e.id}`}
                                className="flex flex-col gap-2 p-4 rounded-md bg-stone-100 hover:bg-stone-200 h-fit"
                            >
                                <div className="flex flex-col mb-1 pb-2 border-b border-b-stone-400 w-64">
                                    <h3 className="text-lg">{e.name}</h3>
                                    <h4 className="text-sm text-ellipsis text-nowrap overflow-hidden">
                                        {e.description}
                                    </h4>
                                </div>
                                <span className="text-xs">
                                    {e.id.split("-").slice(-1)}
                                </span>
                            </a>
                        ))}
                    <button
                        onClick={() => setCreate(true)}
                        className="flex flex-col gap-2 p-4 rounded-md bg-stone-100 hover:bg-stone-200 h-fit"
                    >
                        <Plus />
                    </button>
                </div>
            </div>
        </>
    );
};

export default ListSystem;
