import {
    Divider,
    FormControl,
    Input,
} from "@mui/joy";
import { Ban, Pencil, Plus, Save, Trash } from "lucide-react";
import React, { useEffect, useState } from 'react';
import { useSystemActions } from "$lib/features/interfaces/queries";
import { useParams } from "react-router";
import Select from "react-select";
import useLocalStorage from './useLocalStorage';

type SectionRef = { value: string; label: string };
type CardEntry = { type: 'card'; id: string; label: string; sections: SectionRef[] };
type PageEntry = SectionRef | CardEntry;

const isCard = (e: PageEntry): e is CardEntry => (e as any).type === 'card';

const CardSectionItem: React.FC<{ sRef: SectionRef; onRemove: () => void }> = ({ sRef, onRemove }) => (
    <div key={sRef.value} className="flex items-center gap-1 bg-white rounded border border-blue-100 px-2 py-1">
        <span className="flex-1 text-xs truncate">{sRef.label}</span>
        <button type="button" onClick={onRemove} className="shrink-0 text-gray-300 hover:text-red-400">
            <Trash size={11} />
        </button>
    </div>
);

const CardEntry_: React.FC<{
    entry: CardEntry;
    entryIdx: number;
    sectionOptions: any[];
    onRemoveCard: () => void;
    onRemoveSection: (sIdx: number) => void;
    onAddSection: (opt: any) => void;
    onRename: (label: string) => void;
}> = ({ entry, entryIdx, sectionOptions, onRemoveCard, onRemoveSection, onAddSection, onRename }) => (
    <div key={entry.id} className="rounded-lg border border-blue-200 bg-blue-50 p-2 space-y-1.5">
        <div className="flex items-center gap-1">
            <input
                type="text"
                value={entry.label}
                onChange={(e) => onRename(e.target.value)}
                className="flex-1 text-xs font-semibold text-blue-700 bg-transparent border-b border-blue-200 focus:outline-none focus:border-blue-400 min-w-0"
            />
            <button type="button" onClick={onRemoveCard} className="shrink-0 text-blue-300 hover:text-red-500">
                <Trash size={13} />
            </button>
        </div>
        {(entry.sections || []).map((sRef: SectionRef, sIdx: number) => (
            <CardSectionItem key={sRef.value} sRef={sRef} onRemove={() => onRemoveSection(sIdx)} />
        ))}
        <Select
            placeholder="Add section to card..."
            options={sectionOptions.filter((opt: any) => !(entry.sections || []).some((s: SectionRef) => s.value === opt.value))}
            onChange={onAddSection}
            value={null}
            styles={{ control: (base: any) => ({ ...base, minHeight: '28px', fontSize: '11px' }) }}
        />
    </div>
);

const SectionEntryRow: React.FC<{ entry: SectionRef; onRemove: () => void }> = ({ entry, onRemove }) => (
    <div key={entry.value} className="flex items-center gap-2 bg-white rounded border border-stone-200 px-2 py-1.5">
        <span className="flex-1 text-sm truncate">{entry.label}</span>
        <button type="button" onClick={onRemove} className="shrink-0 text-gray-300 hover:text-red-400">
            <Trash size={13} />
        </button>
    </div>
);

type Props = {
    actorName: string;
    interfaceId?: string;
};

export const Pages: React.FC<Props> = ({ actorName, interfaceId }) => {
    const { systemId } = useParams();
    const storagePrefix = interfaceId || 'new-interface';
    const [data, setData, isSuccess] = useLocalStorage(`interface:${storagePrefix}:pages`, []);
    const [editIndex, setEditIndex] = useState(-1);
    const [newName, setNewName] = useState('');
    const [categories, , isSuccessCategories] = useLocalStorage(`interface:${storagePrefix}:categories`, []);
    const [selectedCategory, setSelectedCategory] = useLocalStorage('selectedCategory', '');
    const [selectedPageType, setSelectedPageType] = useLocalStorage('selectedPageType', '');
    const [selectedLayout, setSelectedLayout] = useLocalStorage('selectedLayout', '');
    const [selectedGap, setSelectedGap] = useLocalStorage('selectedGap', '');
    const [selectedAction, setSelectedAction] = useLocalStorage('selectedAction', '');
    const [sections, , isSuccessSections] = useLocalStorage(`interface:${storagePrefix}:sections`, []);
    const [selectedSections, setSelectedSections] = useLocalStorage('selectedSections', []);
    const [pencilClick, setPencilClick] = useState(false);
    const [actions, isSuccessActions] = useSystemActions(systemId, 'action');

    const filteredActions = actions.filter((action) => action.cls.actorNodeName === actorName);
    const sectionOptions = React.useMemo(
        () => (sections || []).map((section: any) => ({
            label: section.name || section.id,
            value: section.id,
        })),
        [sections],
    );
    const sectionOptionForRef = React.useCallback((ref: any) => {
        const sectionId = typeof ref === 'string' ? ref : ref?.value;
        if (!sectionId) return null;
        return sectionOptions.find((option: any) => option.value === sectionId)
            || { label: ref?.label || sectionId, value: sectionId };
    }, [sectionOptions]);

    useEffect(() => {
        if (editIndex !== -1 && data[editIndex].sections) {
            setSelectedSections(
                (data[editIndex].sections || [])
                    .map((entry: any) => {
                        if (typeof entry === 'object' && entry.type === 'card') return entry;
                        return sectionOptionForRef(entry);
                    })
                    .filter(Boolean),
            );
        } else {
            setSelectedSections([]);
        }
    }, [editIndex, data, sectionOptionForRef, setSelectedSections]);

    useEffect(() => {
        if (editIndex !== -1 && data[editIndex].category) {
            setSelectedCategory(data[editIndex].category);
        } else {
            setSelectedCategory(null);
        }
    }, [editIndex, data, setSelectedCategory]);

    useEffect(() => {
        if (editIndex !== -1 && data[editIndex].type) {
            setSelectedPageType(data[editIndex].type || 'normal');
        } else {
            setSelectedPageType('normal');
        }
    }, [editIndex, data, setSelectedPageType]);

    useEffect(() => {
        if (editIndex !== -1 && data[editIndex].layout) {
            setSelectedLayout(data[editIndex].layout);
        } else {
            setSelectedLayout({ label: 'Down', value: 'vertical' });
        }
    }, [editIndex, data, setSelectedLayout]);

    useEffect(() => {
        if (editIndex !== -1 && data[editIndex].gap) {
            setSelectedGap(data[editIndex].gap);
        } else {
            setSelectedGap({ label: 'Normal', value: 'normal' });
        }
    }, [editIndex, data, setSelectedGap]);

    useEffect(() => {
        if (editIndex !== -1 && data[editIndex].action) {
            setSelectedAction(data[editIndex].action);
        } else {
            setSelectedAction(null);
        }
    }, [editIndex, data, setSelectedAction]);

    const handleEdit = (index: number) => {
        setEditIndex(index);
        if (data[index]?.type) {
            setSelectedPageType(data[index].type);
        } else {
            setSelectedPageType({ label: 'Normal', value: 'normal' });
        }
        if (data[index]?.layout) {
            setSelectedLayout(data[index].layout);
        } else {
            setSelectedLayout({ label: 'Down', value: 'vertical' });
        }
        if (data[index]?.gap) {
            setSelectedGap(data[index].gap);
        } else {
            setSelectedGap({ label: 'Normal', value: 'normal' });
        }
    };

    const handleMinus = () => {
        setEditIndex(-1);
    };

    const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setNewName(event.target.value);
    };

    const handleDelete = (index: number) => {
        const newData = [...data];
        newData.splice(index, 1);
        setData(newData);
        setEditIndex(-1);
    };

    useEffect(() => {
        if (editIndex !== -1) {
            const newData = [...data];
            newData[editIndex].sections = (selectedSections || [])
                .map((entry: any) => {
                    if (typeof entry === 'object' && entry.type === 'card') return entry;
                    return sectionOptionForRef(entry);
                })
                .filter(Boolean);
            setData(newData);
        }
    }, [selectedSections, sectionOptionForRef]);

    useEffect(() => {
        if (editIndex !== -1) {
            const newData = [...data];
            newData[editIndex].category = selectedCategory;
            setData(newData);
        }
    }, [selectedCategory]);

    useEffect(() => {
        if (editIndex !== -1) {
            const newData = [...data];
            newData[editIndex].type = selectedPageType;
            if (selectedPageType.value === 'normal') {
                newData[editIndex].action = null;
            } else {
                newData[editIndex].category = null;
            }
            setData(newData);
        }
    }, [selectedPageType]);

    useEffect(() => {
        if (editIndex !== -1) {
            const newData = [...data];
            newData[editIndex].action = selectedAction;
            setData(newData);
        }
    }, [selectedAction]);

    useEffect(() => {
        if (editIndex !== -1) {
            const newData = [...data];
            newData[editIndex].layout = selectedLayout;
            setData(newData);
        }
    }, [selectedLayout]);

    useEffect(() => {
        if (editIndex !== -1) {
            const newData = [...data];
            newData[editIndex].gap = selectedGap;
            setData(newData);
        }
    }, [selectedGap]);


    const handlePencilClick = () => {
        setPencilClick(true);
    }

    const handleNameChange = (index: number) => {
        const newData = [...data];
        newData[index].name = newName;
        setData(newData);
        setPencilClick(false);
    };

    const handleNameCancel = () => {
        setPencilClick(false);
    };

    const handleAddCard = () => {
        const cardCount = (selectedSections || []).filter(isCard).length;
        const newCard: CardEntry = {
            type: 'card',
            id: globalThis.crypto.randomUUID(),
            label: `Card ${cardCount + 1}`,
            sections: [],
        };
        setSelectedSections([...(selectedSections || []), newCard]);
    };

    const handleAddSectionToPage = (opt: SectionRef | null) => {
        if (!opt) return;
        setSelectedSections([...(selectedSections || []), opt]);
    };

    const handleAddSectionToCard = (cardIdx: number, opt: SectionRef | null) => {
        if (!opt) return;
        const updated = [...(selectedSections || [])] as PageEntry[];
        const card = { ...(updated[cardIdx] as CardEntry), sections: [...(updated[cardIdx] as CardEntry).sections] };
        card.sections.push(opt);
        updated[cardIdx] = card;
        setSelectedSections(updated);
    };

    const handleRemoveEntry = (idx: number) => {
        const updated = [...(selectedSections || [])];
        updated.splice(idx, 1);
        setSelectedSections(updated);
    };

    const handleRemoveSectionFromCard = (cardIdx: number, sectionIdx: number) => {
        const updated = [...(selectedSections || [])] as PageEntry[];
        const card = { ...(updated[cardIdx] as CardEntry), sections: [...(updated[cardIdx] as CardEntry).sections] };
        card.sections.splice(sectionIdx, 1);
        updated[cardIdx] = card;
        setSelectedSections(updated);
    };

    const handleRenameCard = (cardIdx: number, newLabel: string) => {
        const updated = [...(selectedSections || [])] as PageEntry[];
        updated[cardIdx] = { ...(updated[cardIdx] as CardEntry), label: newLabel };
        setSelectedSections(updated);
    };

    return (
        <>
            <div className="flex flex-wrap gap-4">
                {isSuccess && (
                    data.map((page, index) => (
                        <div key={index} className="flex flex-col gap-2">
                            {editIndex === index ? (
                                <div className="w-[240px] flex flex-col gap-2 space-y-2">
                                    <div>
                                        <h3 className="text-xl font-bold">Name</h3>
                                        {!pencilClick && (
                                            <div className="flex flex-wrap gap-2">
                                                <h2 className="text-l">{page.name}</h2>
                                                <Pencil
                                                    className="cursor-pointer ml-auto"
                                                    onClick={handlePencilClick}
                                                />
                                            </div>
                                        )}
                                        {pencilClick && (
                                            <FormControl required className="space-y-1">
                                                <Input
                                                    type="text"
                                                    value={newName}
                                                    onChange={handleInputChange}
                                                />
                                                <div className="flex flex-wrap gap-2 ml-auto">
                                                    <button
                                                        onClick={() => handleNameChange(index)}
                                                        className="w-[40px] h-[40px] bg-blue-500 text-white px-2 py-1 rounded-md hover:bg-blue-600"
                                                    >
                                                        <Save />
                                                    </button>
                                                    <button
                                                        onClick={handleNameCancel}
                                                        className="w-[40px] h-[40px] bg-gray-300 text-gray-700 px-2 py-1 rounded-md hover:bg-gray-400"
                                                    >
                                                        <Ban />
                                                    </button>
                                                </div>
                                            </FormControl>
                                        )}
                                    </div>
                                    <FormControl className="space-y-1">
                                        <h3 className="text-xl font-bold">Page type</h3>
                                        <Select
                                            name="pageType"
                                            options={[
                                                { label: 'Normal', value: 'normal' },
                                                { label: 'Activity', value: 'activity' },
                                            ]}
                                            value={selectedPageType}
                                            onChange={setSelectedPageType}
                                        />
                                    </FormControl>
                                    <FormControl className="space-y-1">
                                        <h3 className="text-xl font-bold">Layout</h3>
                                        <Select
                                            name="layout"
                                            options={[
                                                { label: 'Down', value: 'vertical' },
                                                { label: 'Up', value: 'vertical-reverse' },
                                                { label: 'Right', value: 'horizontal' },
                                                { label: 'Left', value: 'horizontal-reverse' },
                                            ]}
                                            value={selectedLayout}
                                            onChange={setSelectedLayout}
                                        />
                                    </FormControl>
                                    <FormControl className="space-y-1">
                                        <h3 className="text-xl font-bold">Gap</h3>
                                        <Select
                                            name="gap"
                                            options={[
                                                { label: 'Compact', value: 'compact' },
                                                { label: 'Normal', value: 'normal' },
                                                { label: 'Spacious', value: 'spacious' },
                                            ]}
                                            value={selectedGap}
                                            onChange={setSelectedGap}
                                        />
                                    </FormControl>
                                    {selectedPageType.value === 'normal' && isSuccessCategories && (
                                        <FormControl className="space-y-1">
                                            <h3 className="text-xl font-bold">Category</h3>
                                            {categories.length > 0 ? (
                                                <Select
                                                    name="category"
                                                    options={categories.map((e) => ({ label: e.name, value: e }))}
                                                    value={selectedCategory}
                                                    onChange={setSelectedCategory}
                                                    isClearable={true}
                                                />
                                            ) : (
                                                <p>Create a new category!</p>
                                            )}
                                        </FormControl>
                                    )}
                                    {selectedPageType.value === 'activity' && isSuccessActions && (
                                        <FormControl className="space-y-1">
                                            <h3 className="text-xl font-bold">Activity</h3>
                                            {filteredActions.length > 0 ? (
                                                <Select
                                                    name="activity"
                                                    options={filteredActions.map((e) => ({ label: e.cls.name, value: e.id }))}
                                                    value={selectedAction}
                                                    onChange={setSelectedAction}
                                                    isClearable={true}
                                                />
                                            ) : (
                                                <p>Create a new activity using the Activity Diagram editor</p>
                                            )}
                                        </FormControl>
                                    )}
                                    {isSuccessSections && (
                                        <div className="space-y-2">
                                            <div className="flex items-center justify-between">
                                                <h3 className="text-xl font-bold">Section Components</h3>
                                                <button
                                                    type="button"
                                                    onClick={handleAddCard}
                                                    className="text-xs border border-blue-300 text-blue-600 rounded-md px-2 py-1 hover:bg-blue-50"
                                                >
                                                    + Card
                                                </button>
                                            </div>
                                            {(selectedSections || []).map((entry: any, entryIdx: number) => (
                                                isCard(entry) ? (
                                                    <CardEntry_
                                                        key={entry.id}
                                                        entry={entry}
                                                        entryIdx={entryIdx}
                                                        sectionOptions={sectionOptions}
                                                        onRemoveCard={() => handleRemoveEntry(entryIdx)}
                                                        onRemoveSection={(sIdx) => handleRemoveSectionFromCard(entryIdx, sIdx)}
                                                        onAddSection={(opt: any) => handleAddSectionToCard(entryIdx, opt)}
                                                        onRename={(label) => handleRenameCard(entryIdx, label)}
                                                    />
                                                ) : (
                                                    <SectionEntryRow
                                                        key={entry.value}
                                                        entry={entry}
                                                        onRemove={() => handleRemoveEntry(entryIdx)}
                                                    />
                                                )
                                            ))}
                                            <Select
                                                placeholder="Add section..."
                                                options={sectionOptions}
                                                onChange={(opt: any) => handleAddSectionToPage(opt)}
                                                value={null}
                                            />
                                        </div>
                                    )}
                                    <Divider />
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => handleDelete(index)}
                                            className="w-[40px] h-[40px] bg-red-500 text-white px-2 py-1 rounded-md hover:bg-red-600"
                                        >
                                            <Trash />
                                        </button>
                                        <button
                                            onClick={handleMinus}
                                            className="w-[60px] h-[40px] bg-stone-200 text-stone-900 px-2 py-1 rounded-md hover:bg-blue-600"
                                        >
                                            Close
                                        </button>
                                    </div>
                                </div>
                            ) : (
                                <div className="flex justify-between items-center w-full">
                                    <h3
                                        onClick={() => handleEdit(index)}
                                        className="flex h-fit w-48 flex-col gap-2 overflow-hidden text-ellipsis rounded-md bg-stone-200 p-4 hover:bg-stone-300 cursor-pointer"
                                    >
                                        {page.name}
                                    </h3>
                                </div>
                            )}
                        </div>
                    ))
                )}
                <button
                    onClick={() => {
                        const newPage = { id: globalThis.crypto.randomUUID(), name: `Page ${data.length + 1}`, category: null, type: { label: 'Normal', value: 'normal' } };
                        setData([...data, newPage]);
                        setEditIndex(data.length);
                    }}
                    className="flex h-fit w-14 flex-col gap-2 overflow-hidden text-ellipsis rounded-md bg-stone-200 p-4 hover:bg-stone-300"
                >
                    <Plus />
                </button>
            </div>
        </>
    );
};

export default Pages;
