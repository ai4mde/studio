import React, { useState, useEffect } from "react";
import { Package } from "lucide-react";
import { useParams } from "react-router";
import { useSystemPrototypes } from "$lib/features/prototypes/queries";
import { deletePrototype} from "$lib/features/prototypes/mutations";
import { Trash } from "lucide-react";


type Props = {
    system: string;
};

export const ShowPrototypes: React.FC<Props> = ({ system }) => {
    const { systemId } = useParams();
    const [ data, isSuccess ] = useSystemPrototypes(systemId);

    const handleDelete = async (prototypeId: string) => {
        try {
            await deletePrototype(prototypeId);
            window.location.reload();
        } catch (error) {
            console.error('Error deleting prototype:', error);
        }
    };

    return (
        <>
            <table className="min-w-full bg-white text-left">
                <thead className="text-sm">
                    <tr>
                        <th className="py-2 px-4 border-b border-stone-200">
                            <span className="flex flex-row items-center gap-2">
                                <Package size={24} />
                                <h1 className="text-lg">Prototypes</h1>
                            </span>
                        </th>
                        <th className="py-2 px-4 border-b border-stone-200">Status</th>
                        <th className="py-2 px-4 border-b border-stone-200">URL</th>
                        <th className="w-40 py-2 px-4 border-b border-stone-200"></th>
                    </tr>
                </thead>
            </table>
            {isSuccess && (
                <div className="max-h-96 overflow-y-auto">
                    <table className="min-w-full bg-white text-left">
                        <tbody>
                            {[...data].reverse().map((e, index) => (
                                <tr key={index} className="hover:bg-gray-50">
                                    <td className="py-2 px-4 border-b border-gray-200">
                                        <h1 className="text-lg">{e.name}</h1>
                                        <h2 className="text-stone-400">{e.description}</h2>
                                    </td>
                                    <td className="py-2 px-4 border-b border-gray-200">
                                        {e.status}
                                    </td>
                                    <td className="py-2 px-4 border-b border-gray-200">
                                        <a href={e.url} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">
                                            {e.url}
                                        </a>
                                    </td>
                                    <td className="w-20 py-2 px-4 border-b border-gray-200">
                                    <button
                                        onClick={() => handleDelete(e.id)}
                                        className="w-[40px] h-[40px] bg-red-500 text-white px-2 py-1 rounded-md hover:bg-red-600"
                                    >
                                        <Trash />
                                    </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </>
    );
};

export default ShowPrototypes;