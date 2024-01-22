import { authAxios } from "$lib/features/auth/state/auth";
import { useQuery } from "@tanstack/react-query";
import { useAtom } from "jotai";
import { Plus } from "lucide-react";
import React from "react";
import { createSystemAtom } from "../../atoms";
import CreateSystem from "./CreateSystem";

type SystemOut = {
    id: string;
    name: string;
    description?: string;
};

type Props = {
    project: string;
};

export const ListSystem: React.FC<Props> = ({ project }) => {
    const { data, isSuccess } = useQuery<SystemOut[]>({
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
            <CreateSystem project={project} />
            {isSuccess &&
                data.map((e) => (
                    <a
                        href={`/systems/${e.id}`}
                        className="flex flex-col gap-2 p-4 w-48 text-ellipsis overflow-hidden rounded-md bg-stone-200 hover:bg-stone-300 h-fit"
                    >
                        <h3 className="text-xl font-bold">{e.name}</h3>
                        <h3 className="text-sm">{e.description}</h3>
                        <span className="text-xs text-right pt-2 text-stone-500">
                            {e.id.split("-").slice(-1)}
                        </span>
                    </a>
                ))}
            <button
                onClick={() => setCreate(true)}
                className="flex flex-col gap-2 p-4 rounded-md bg-stone-100 hover:bg-stone-200 h-fill items-center justify-center"
            >
                <Plus />
            </button>
        </>
    );
};

export default ListSystem;
