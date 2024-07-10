import { useAtom } from "jotai";
import { Plus } from "lucide-react";
import React from "react";
import { createInterfaceAtom } from "../../browser/atoms";
import { useInterfaces } from "$browser/queries";
import CreateInterface from "./CreateInterface";
import useLocalStorage from './useLocalStorage';

type Props = {
    system: string;
};

export const ListInterface: React.FC<Props> = ({ system }) => {
    const [, setCreate] = useAtom(createInterfaceAtom);
    const { data, isSuccess } = useInterfaces(system);
    const [, setStyling, ] = useLocalStorage('styling', '');
    const [, setCategories, ] = useLocalStorage('categories', []);
    const [, setPages, ] = useLocalStorage('pages', []);
    const [, setSections, ] = useLocalStorage('sections', []);

    const handleLoadInterface = (app_comp) => {

        setStyling(app_comp.styling);
        setCategories(app_comp.categories);
        setPages(app_comp.pages);
        setSections(app_comp.sections);
    }

    return (
        <>
            {isSuccess && (
                <div className="flex flex-wrap gap-4">
                    {data.map((e) => (
                        <a
                            key={e.id}
                            onClick={() => handleLoadInterface(e.data)}
                            href={`/systems/${system}/interfaces/${e.id}`}
                            className="flex h-fit w-48 flex-col gap-2 overflow-hidden text-ellipsis rounded-md bg-stone-200 p-4 hover:bg-stone-300"
                        >
                            <h3 className="text-xl font-bold">{e.name}</h3>
                            <h3 className="text-sm">{e.description}</h3>
                            <span className="pt-2 text-right text-xs text-stone-500">
                                {e.id.split("-").slice(-1)}
                            </span>
                        </a>
                    ))}
                    <button
                        onClick={() => setCreate(true)}
                        className="flex h-fit w-14 flex-col gap-2 overflow-hidden text-ellipsis rounded-md bg-stone-200 p-4 hover:bg-stone-300"
                    >
                        <Plus />
                    </button>
                </div>
            )}
            <CreateInterface system={system} />
        </>
    );
};

export default ListInterface;
