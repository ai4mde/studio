import {
    Divider,
    FormControl,
    Input,
    Textarea,
} from "@mui/joy";
import Chip from '@mui/joy/Chip';
import { Ban, Pencil, Plus, Save, Trash, Link as LinkIcon } from "lucide-react";
import Multiselect from 'multiselect-react-dropdown';
import React, { useState } from 'react';
import { useParams } from "react-router";
import { useClassAttributes, useClassCustomMethods, useSystemClasses } from "../queries";
import useLocalStorage from './useLocalStorage';

type Props = {
};

const CHROME_LAYOUTS = [
    'promo-bar', 'logo', 'search-bar', 'icon-actions', 'nav-links', 'main-header', 'minimal-header',
    'service-bar', 'link-grid', 'brand-strip',
    'site-nav', 'site-footer',
];

const METHODS_HINTS: Record<string, string> = {
    'promo-bar':      'Each line = promo strip item (e.g. "Gratis verzending vanaf €25,-"). Text field = right-side CTA label.',
    'logo':           'Text field = brand name shown in the logo.',
    'search-bar':     'Text field = search input placeholder.',
    'icon-actions':   'Each line = action label (e.g. "Inloggen", "♡", "Cart icon").',
    'nav-links':      'Line 1 = categories label. Lines 2–4 = extra nav links. Lines 5+ = top-right links (e.g. "Zakelijk").',
    'main-header':    'Text field = search placeholder. Uses promo-bar/logo/search-bar/icon-actions sections instead.',
    'minimal-header': 'Text field = cart amount shown in header button (e.g. "0,00").',
    'service-bar':    'Each line = a service bar link in the footer.',
    'link-grid':      'Line 1 = column title. Lines 2+ = footer links in that column.',
    'brand-strip':    'Each line = a brand name shown in the brand strip.',
    'site-nav':       'Lines 1–3: promo strip items. Line 4: right-side highlight text.',
    'site-footer':    'Each line becomes a service-bar link in the footer.',
};

const FIELD_RENDER_OPTIONS = [
    { value: 'text', label: 'Text' },
    { value: 'link', label: 'Link' },
    { value: 'button', label: 'Button' },
    { value: 'badge', label: 'Badge' },
];

const FIELD_ACTION_OPTIONS = [
    { value: 'none', label: 'None' },
    { value: 'navigate', label: 'Navigate' },
    { value: 'operation', label: 'Operation' },
    { value: 'copy', label: 'Copy' },
    { value: 'filter', label: 'Filter' },
    { value: 'expand', label: 'Expand' },
    { value: 'tooltip', label: 'Tooltip' },
];

const ACTIVITY_ACTION_VARIANTS = [
    { value: 'button', label: 'Button' },
    { value: 'wizard_next', label: 'Wizard next' },
    { value: 'link', label: 'Link' },
    { value: 'fab', label: 'Floating' },
    { value: 'auto', label: 'Auto' },
];

const ACTIVITY_ACTION_ALIGNS = [
    { value: 'left', label: 'Left' },
    { value: 'center', label: 'Center' },
    { value: 'right', label: 'Right' },
];

const ACTIVITY_ACTION_SIZES = [
    { value: 'sm', label: 'Small' },
    { value: 'md', label: 'Medium' },
    { value: 'lg', label: 'Large' },
];

const getAttributeName = (attr: any) => typeof attr === 'string' ? attr : attr?.name;
const getAttributeRenderAs = (attr: any) => {
    if (typeof attr === 'string') return 'text';
    return attr?.render?.as || (attr?.is_link ? 'link' : 'text');
};
const getAttributeAction = (attr: any) => {
    if (typeof attr === 'string') return { type: 'none' };
    return attr?.action || { type: attr?.is_link ? 'navigate' : 'none' };
};
const normalizeAttribute = (attr: any) => typeof attr === 'string' ? { name: attr } : { ...(attr || {}) };
const isActivityActionSection = (section: any) => section?.type === 'activity_action' || section?.layout === 'activity_action';

export const Sections: React.FC<Props> = () => {
    const { systemId } = useParams();
    const [data, setData, isSuccess] = useLocalStorage('sections', []);
    const [editIndex, setEditIndex] = useState(-1);
    const [newName, setNewName] = useState('');
    const [newText, setNewText] = useState('');
    const [newRelationField, setNewRelationField] = useState('');
    const [selectedOperations, setSelectedOperations] = useLocalStorage('selectedOperations', []);
    const [pencelClick, setPencelClick] = useState(false);
    const [pencelClickText, setPencelClickText] = useState(false);
    const [classes, isSuccessClasses] = useSystemClasses(systemId);
    const [selectedClass, setSelectedClass] = useLocalStorage('selectedClass', '');
    const [classAttributes] = useClassAttributes(systemId, selectedClass);
    const [classCustomMethods] = useClassCustomMethods(systemId, selectedClass)
    //const [attributes, setAttributes] = useState([]);
    const [selectedAttributes, setSelectedAttributes] = useLocalStorage('selectedAttributes', []);
    const [selectedCustomMethods, setSelectedCustomMethods] = useLocalStorage('selectedCustomMethods', [])
    const [pages, setPages, isSuccessPages] = useLocalStorage('pages', []);
    const [customAttr, setCustomAttr] = useState('');
    const [availablePaths, setAvailablePaths] = useState<string[]>([]);

    React.useEffect(() => {
        if (isSuccessClasses && classes) {
            const allPaths: string[] = classes.flatMap((cls: any) => 
                (cls.data?.attributes || []).map((attr: any) => `${cls.data.name.toLowerCase()}.${attr.name}`)
            );
            setAvailablePaths([...new Set(allPaths)]);
        }
    }, [isSuccessClasses, classes]);


    const handleEdit = async (index: number) => {
        // Close name editor when switching section component
        if (pencelClick) {
            setPencelClick(false);
            setPencelClickText(false);
        }

        // Retrieve local storage vars from data
        if (data[index].class) {
            const classId = data[index].class;
            setSelectedClass(classId);
        }

        if (data[index].operations) {
            setSelectedOperations(data[index].operations);
        } else {
            setSelectedOperations([]);
        }

        if (data[index].attributes) {
            setSelectedAttributes(data[index].attributes);
        } else {
            setSelectedAttributes([]);
        }

        if (data[index].methods) {
            setSelectedCustomMethods(data[index].methods);
        } else {
            setSelectedCustomMethods([]);
        }

        if (data[index].text) {
            setNewText(data[index].text);
        } else {
            setNewText('');
        }

        setNewRelationField(data[index].relation_field || '');
        setEditIndex(index);
    };

    const handleNameChange = (index: number) => {
        const newData = [...data];
        newData[index].name = newName;
        setData(newData);
        const sectionId = data[index].id;
        if (isSuccessPages) {
            const newPages = [...pages]
            newPages.map(page => {
                page.sections.map(section => {
                    section.value === sectionId ? (section.label = newName) : null
                })
            })
            setPages(newPages);
        }
        setPencelClick(false);
    };

    const handlePencilClick = () => {
        setPencelClick(true);
    }

    const handleNameCancel = () => {
        setPencelClick(false);
    };

    const handleTextChange = (index: number) => {
        const newData = [...data];
        newData[index].text = newText;
        setData(newData);
        setPencelClickText(false);
    };

    const handlePencilClickText = () => {
        setPencelClickText(true);
    }

    const handleTextCancel = () => {
        setPencelClickText(false);
    };

    const handleRelatedToChange = (index: number, sectionId: string) => {
        const newData = [...data];
        newData[index].related_to = sectionId || null;
        const sourceSection = newData.find((section) => section.id === sectionId);
        if (sectionId) {
            const sameClass = sourceSection?.class && sourceSection.class === newData[index].class;
            newData[index].relationship = {
                ...(newData[index].relationship || {}),
                mode: sameClass ? 'same_parent' : 'direct',
            };
            if (sameClass) {
                newData[index].query = {
                    ...(newData[index].query || {}),
                    exclude_source: newData[index].query?.exclude_source ?? true,
                };
            }
        } else {
            delete newData[index].relationship;
            delete newData[index].relation_field;
            setNewRelationField('');
        }
        setData(newData);
    };

    const handleRelationshipModeChange = (index: number, mode: string) => {
        const newData = [...data];
        newData[index].relationship = {
            ...(newData[index].relationship || {}),
            mode,
        };
        if (mode !== 'same_parent') {
            delete newData[index].relationship.via;
        } else {
            newData[index].query = {
                ...(newData[index].query || {}),
                exclude_source: newData[index].query?.exclude_source ?? true,
            };
        }
        setData(newData);
    };

    const handleRelationshipViaChange = (index: number, classId: string) => {
        const newData = [...data];
        newData[index].relationship = {
            ...(newData[index].relationship || { mode: 'same_parent' }),
            via: classId || null,
        };
        setData(newData);
    };

    const handleQueryExcludeSourceChange = (index: number, checked: boolean) => {
        const newData = [...data];
        newData[index].query = {
            ...(newData[index].query || {}),
            exclude_source: checked,
        };
        setData(newData);
    };

    const handleQueryNumberChange = (index: number, key: 'limit' | 'offset', value: string) => {
        const newData = [...data];
        const parsed = Number.parseInt(value, 10);
        newData[index].query = {
            ...(newData[index].query || {}),
            [key]: Number.isNaN(parsed) ? null : parsed,
        };
        setData(newData);
    };

    const handleAddOrderBy = (index: number) => {
        const newData = [...data];
        const firstField = classAttributes[0]?.name || '';
        newData[index].query = {
            ...(newData[index].query || {}),
            order_by: [...(newData[index].query?.order_by || []), { field: firstField, direction: 'asc' }],
        };
        setData(newData);
    };

    const handleOrderByChange = (index: number, orderIndex: number, key: 'field' | 'direction', value: string) => {
        const newData = [...data];
        const orderBy = [...(newData[index].query?.order_by || [])];
        orderBy[orderIndex] = { ...(orderBy[orderIndex] || {}), [key]: value };
        newData[index].query = { ...(newData[index].query || {}), order_by: orderBy };
        setData(newData);
    };

    const handleRemoveOrderBy = (index: number, orderIndex: number) => {
        const newData = [...data];
        const orderBy = [...(newData[index].query?.order_by || [])];
        orderBy.splice(orderIndex, 1);
        newData[index].query = { ...(newData[index].query || {}), order_by: orderBy };
        setData(newData);
    };

    const handleAddFilter = (index: number) => {
        const newData = [...data];
        const firstField = classAttributes[0]?.name || '';
        newData[index].query = {
            ...(newData[index].query || {}),
            filter_logic: 'and',
            filters: [...(newData[index].query?.filters || []), { field: firstField, operator: 'eq', value: '' }],
        };
        setData(newData);
    };

    const handleFilterChange = (index: number, filterIndex: number, key: 'field' | 'operator' | 'value', value: string) => {
        const newData = [...data];
        const filters = [...(newData[index].query?.filters || [])];
        filters[filterIndex] = { ...(filters[filterIndex] || {}), [key]: value };
        newData[index].query = { ...(newData[index].query || {}), filter_logic: 'and', filters };
        setData(newData);
    };

    const handleRemoveFilter = (index: number, filterIndex: number) => {
        const newData = [...data];
        const filters = [...(newData[index].query?.filters || [])];
        filters.splice(filterIndex, 1);
        newData[index].query = { ...(newData[index].query || {}), filters };
        setData(newData);
    };

    const handleRelationFieldChange = (index: number, value: string) => {
        setNewRelationField(value);
        const newData = [...data];
        newData[index].relation_field = value || null;
        setData(newData);
    };

    const handleViewDetailPageChange = (index: number, pageName: string) => {
        const newData = [...data];
        newData[index].view_detail_page = pageName || null;
        setData(newData);
    };

    const handleMinus = () => {
        setEditIndex(-1);
    };

    const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setNewName(event.target.value);
    };

    const handleInputChangeText = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
        setNewText(event.target.value);
    };

    const handleDelete = (index: number) => {
        const newData = [...data];
        newData.splice(index, 1);
        setData(newData);
        setEditIndex(-1);
    };

    const toggleOperation = (sectionIndex: number, operation: 'create' | 'update' | 'delete' | 'select') => {
        const sectionOperations = selectedOperations || {};
        const updatedOperations = {
            ...sectionOperations,
            [operation]: !sectionOperations[operation],
        };
        setSelectedOperations(updatedOperations);
        const newData = [...data];
        newData[sectionIndex].operations = updatedOperations;
        setData(newData);
    };

    const toggleClass = async (sectionIndex: number, cls) => {
        setSelectedClass(cls.id);
        const newData = [...data];
        newData[sectionIndex].class = cls.id;
        setSelectedAttributes([]);
        newData[sectionIndex].attributes = [];
        setData(newData);
    };

    const handleAttributeSelect = (selectedList, selectedItem, sectionIndex: number) => {
        const updatedAttributes = [...selectedAttributes, selectedItem];
        setSelectedAttributes(updatedAttributes);
        const newData = [...data];
        newData[sectionIndex].attributes = updatedAttributes;
        setData(newData);
    };

    const handleAttributeRemove = (selectedList, selectedItem, sectionIndex: number) => {
        const updatedAttributes = selectedAttributes.filter(attr => 
            (typeof attr === 'string' ? attr : attr.name) !== (typeof selectedItem === 'string' ? selectedItem : selectedItem.name)
        );
        setSelectedAttributes(updatedAttributes);
        const newData = [...data];
        newData[sectionIndex].attributes = updatedAttributes;
        setData(newData);
    };

    const handleAttributeRenderChange = (sectionIndex: number, attrIndex: number, renderAs: string) => {
        const updatedAttributes = [...selectedAttributes];
        const attr = normalizeAttribute(updatedAttributes[attrIndex]);
        updatedAttributes[attrIndex] = {
            ...attr,
            render: { ...(attr.render || {}), as: renderAs },
            is_link: renderAs === 'link',
            action: attr.action || { type: renderAs === 'link' ? 'navigate' : 'none' },
        };
        setSelectedAttributes(updatedAttributes);
        const newData = [...data];
        newData[sectionIndex].attributes = updatedAttributes;
        setData(newData);
    };

    const updateAttributeAction = (sectionIndex: number, attrIndex: number, patch: Record<string, any>) => {
        const updatedAttributes = [...selectedAttributes];
        const attr = normalizeAttribute(updatedAttributes[attrIndex]);
        const nextAction = { ...(attr.action || { type: 'none' }), ...patch };
        updatedAttributes[attrIndex] = {
            ...attr,
            action: nextAction,
            is_link: nextAction.type === 'navigate' && getAttributeRenderAs(attr) === 'link',
        };
        setSelectedAttributes(updatedAttributes);
        const newData = [...data];
        newData[sectionIndex].attributes = updatedAttributes;
        setData(newData);
    };

    const handleAddCustomAttribute = (sectionIndex: number) => {
        if (!customAttr) return;
        const updatedAttributes = [...selectedAttributes, { name: customAttr, render: { as: 'text' }, action: { type: 'none' } }];
        setSelectedAttributes(updatedAttributes);
        const newData = [...data];
        newData[sectionIndex].attributes = updatedAttributes;
        setData(newData);
        setCustomAttr('');
    };

    const handleCustomMethodSelect = (selectedList, selectedItem, sectionIndex: number) => {
        const updatedCustomMethods = [...selectedCustomMethods, selectedItem];
        setSelectedCustomMethods(updatedCustomMethods);
        const newData = [...data];
        newData[sectionIndex].methods = updatedCustomMethods;
        setData(newData);
    };

    const handleCustomMethodRemove = (selectedList, selectedItem, sectionIndex: number) => {
        const updatedCustomMethods = selectedCustomMethods.filter(attr => attr !== selectedItem);
        setSelectedCustomMethods(updatedCustomMethods);
        const newData = [...data];
        newData[sectionIndex].methods = updatedCustomMethods;
        setData(newData);
    };

    const handleMethodLabelChange = (sectionIndex: number, methodIndex: number, label: string) => {
        const updatedMethods = [...selectedCustomMethods];
        updatedMethods[methodIndex] = { ...updatedMethods[methodIndex], label };
        setSelectedCustomMethods(updatedMethods);
        const newData = [...data];
        newData[sectionIndex].methods = updatedMethods;
        setData(newData);
    };

    const handleActivityActionChange = (sectionIndex: number, patch: Record<string, any>) => {
        const newData = [...data];
        const section = { ...newData[sectionIndex] };
        if (patch.style) {
            section.style = { ...(section.style || {}), ...patch.style };
            delete patch.style;
        }
        newData[sectionIndex] = { ...section, ...patch };
        setData(newData);
    };

    return (
        <>
            {isSuccess && (
                <div className="flex flex-wrap gap-4">
                    {data.map((section, index) => (
                        <div key={index} className="flex flex-col gap-2">
                            {editIndex === index ? (
                                <div className="w-[280px] flex flex-col gap-2 space-y-2">
                                    <div>
                                        <h3 className="text-xl font-bold">Name</h3>
                                        {!pencelClick && (
                                            <div className="flex flex-wrap gap-2">
                                                <h2 className="text-l">{section.name}</h2>
                                                <Pencil
                                                    className="cursor-pointer ml-auto"
                                                    onClick={handlePencilClick}
                                                />
                                            </div>
                                        )}

                                        {pencelClick && (
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
                                    {isActivityActionSection(data[index]) ? (
                                    <FormControl className="space-y-2">
                                        <h3 className="text-xl font-bold">Activity Button</h3>
                                        <p className="text-xs text-gray-500">This section completes the current workflow step. Place it on activity pages just like other sections.</p>
                                        <label className="text-xs text-gray-500">Button label</label>
                                        <input
                                            type="text"
                                            value={data[index].label || data[index].name || ''}
                                            onChange={(e) => handleActivityActionChange(index, { label: e.target.value, name: e.target.value || data[index].name })}
                                            className="border border-gray-300 rounded-md px-2 py-1.5 text-sm w-full"
                                        />
                                        <label className="text-xs text-gray-500">Variant</label>
                                        <select
                                            value={data[index].style?.variant || 'button'}
                                            onChange={(e) => handleActivityActionChange(index, { style: { variant: e.target.value } })}
                                            className="border border-gray-300 rounded-md px-2 py-1.5 text-sm w-full"
                                        >
                                            {ACTIVITY_ACTION_VARIANTS.map(option => (
                                                <option key={option.value} value={option.value}>{option.label}</option>
                                            ))}
                                        </select>
                                        <label className="text-xs text-gray-500">Align</label>
                                        <select
                                            value={data[index].style?.align || 'right'}
                                            onChange={(e) => handleActivityActionChange(index, { style: { align: e.target.value } })}
                                            className="border border-gray-300 rounded-md px-2 py-1.5 text-sm w-full"
                                        >
                                            {ACTIVITY_ACTION_ALIGNS.map(option => (
                                                <option key={option.value} value={option.value}>{option.label}</option>
                                            ))}
                                        </select>
                                        <label className="text-xs text-gray-500">Size</label>
                                        <select
                                            value={data[index].style?.size || 'lg'}
                                            onChange={(e) => handleActivityActionChange(index, { style: { size: e.target.value } })}
                                            className="border border-gray-300 rounded-md px-2 py-1.5 text-sm w-full"
                                        >
                                            {ACTIVITY_ACTION_SIZES.map(option => (
                                                <option key={option.value} value={option.value}>{option.label}</option>
                                            ))}
                                        </select>
                                    </FormControl>
                                    ) : (<>
                                    <div className="space-y-1">
                                        <h3 className="text-xl font-bold">Primary Class</h3>
                                        <div className="flex max-w-full flex-wrap gap-2">
                                            {isSuccessClasses && (
                                                classes.map((e) => (
                                                    <Chip
                                                        key={e.id}
                                                        onClick={() => toggleClass(index, e)}
                                                        color={selectedClass === e.id ? 'primary' : 'neutral'}
                                                        sx={{ maxWidth: '100%' }}
                                                    >
                                                        {e.data.name}
                                                    </Chip>
                                                )
                                                ))}
                                        </div>
                                    </div>
                                    <div className="space-y-1">
                                        <h3 className="text-xl font-bold">Operations</h3>
                                        <div className="flex gap-2">
                                            <Chip
                                                onClick={() => toggleOperation(index, 'create')}
                                                color={selectedOperations.create ? 'primary' : 'neutral'}
                                            >
                                                Create
                                            </Chip>
                                            <Chip
                                                onClick={() => toggleOperation(index, 'update')}
                                                color={selectedOperations.update ? 'primary' : 'neutral'}
                                            >
                                                Update
                                            </Chip>
                                            <Chip
                                                onClick={() => toggleOperation(index, 'delete')}
                                                color={selectedOperations.delete ? 'primary' : 'neutral'}
                                            >
                                                Delete
                                            </Chip>
                                            <Chip
                                                onClick={() => toggleOperation(index, 'select')}
                                                color={selectedOperations.select ? 'primary' : 'neutral'}
                                            >
                                                Select
                                            </Chip>
                                        </div>
                                    </div>
                                    <div className='space-y-1'>
                                        <h3 className="text-xl font-bold">Attributes</h3>
                                        <Multiselect
                                            options={classAttributes}
                                            displayValue='name'
                                            placeholder="Select attributes..."
                                            showCheckbox={true}
                                            style={{ chips: { background: 'rgb(231 229 228)', color: 'rgb(61 56 70)' } }}
                                            selectedValues={selectedAttributes}
                                            onSelect={(selectedList, selectedItem) => handleAttributeSelect(selectedList, selectedItem, index)}
                                            onRemove={(selectedList, selectedItem) => handleAttributeRemove(selectedList, selectedItem, index)}
                                        />
                                        <div className="mt-2 space-y-1">
                                            {selectedAttributes.map((attr, attrIdx) => {
                                                const action = getAttributeAction(attr);
                                                return (
                                                    <div key={attrIdx} className="bg-stone-50 px-2 py-1 rounded-md border border-stone-200 space-y-1">
                                                        <div className="flex items-center gap-2">
                                                            <span className="text-xs truncate flex-1 min-w-0">{getAttributeName(attr)}</span>
                                                            {getAttributeRenderAs(attr) === 'link' && <LinkIcon size={13} className="text-blue-600" />}
                                                            <select
                                                                value={getAttributeRenderAs(attr)}
                                                                onChange={(e) => handleAttributeRenderChange(index, attrIdx, e.target.value)}
                                                                className="border border-gray-300 rounded-md bg-white px-1 py-0.5 text-xs"
                                                                title="Field render mode"
                                                            >
                                                                {FIELD_RENDER_OPTIONS.map(option => (
                                                                    <option key={option.value} value={option.value}>{option.label}</option>
                                                                ))}
                                                            </select>
                                                            <select
                                                                value={action.type || 'none'}
                                                                onChange={(e) => updateAttributeAction(index, attrIdx, { type: e.target.value })}
                                                                className="border border-gray-300 rounded-md bg-white px-1 py-0.5 text-xs"
                                                                title="Field action"
                                                            >
                                                                {FIELD_ACTION_OPTIONS.map(option => (
                                                                    <option key={option.value} value={option.value}>{option.label}</option>
                                                                ))}
                                                            </select>
                                                        </div>
                                                        {action.type !== 'none' && (
                                                            <input
                                                                type="text"
                                                                value={action.targetPageId || action.operation || action.field || action.tooltip || ''}
                                                                onChange={(e) => {
                                                                    const key = action.type === 'navigate' ? 'targetPageId'
                                                                        : action.type === 'operation' ? 'operation'
                                                                            : action.type === 'tooltip' ? 'tooltip'
                                                                                : 'field';
                                                                    updateAttributeAction(index, attrIdx, { [key]: e.target.value });
                                                                }}
                                                                placeholder={
                                                                    action.type === 'navigate' ? 'target page id/name'
                                                                        : action.type === 'operation' ? 'operation name'
                                                                            : action.type === 'tooltip' ? 'tooltip text'
                                                                                : 'field/value'
                                                                }
                                                                className="w-full border border-gray-300 rounded-md px-2 py-1 text-xs"
                                                            />
                                                        )}
                                                    </div>
                                                );
                                            })}
                                        </div>
                                        <div className="flex gap-1 mt-1">
                                            <input
                                                type="text"
                                                list="available-paths"
                                                value={customAttr}
                                                onChange={(e) => setCustomAttr(e.target.value)}
                                                placeholder="e.g. seller.name"
                                                className="border border-gray-300 rounded-md px-2 py-1 text-xs flex-1 min-w-0"
                                            />
                                            <datalist id="available-paths">
                                                {availablePaths.map(path => <option key={path} value={path} />)}
                                            </datalist>
                                            <button
                                                onClick={() => handleAddCustomAttribute(index)}
                                                className="bg-blue-500 text-white px-2 py-1 rounded-md text-xs hover:bg-blue-600"
                                            >
                                                Add
                                            </button>
                                        </div>
                                    </div>
                                    <FormControl className="space-y-1">
                                        <h3 className="text-xl font-bold">
                                            {CHROME_LAYOUTS.includes(data[index].layout) ? 'Methods (one per line)' : 'Custom Operations'}
                                        </h3>
                                        {CHROME_LAYOUTS.includes(data[index].layout) ? (
                                            <>
                                                {METHODS_HINTS[data[index].layout] && (
                                                    <p className="text-xs text-gray-400">{METHODS_HINTS[data[index].layout]}</p>
                                                )}
                                                <Textarea
                                                    minRows={4}
                                                    maxRows={6}
                                                    placeholder={"Gratis verzending vanaf €25,-\nBezorging zelfde dag*\nGratis retourneren\nSelect — Ontdek nu de 4 voordelen"}
                                                    value={(data[index].methods || []).map((m: any) =>
                                                        typeof m === 'string' ? m : (m?.name || m?.label || '')
                                                    ).join('\n')}
                                                    onChange={(e) => {
                                                        const lines = e.target.value.split('\n').map((l: string) => ({ name: l }));
                                                        const newData = [...data];
                                                        newData[index].methods = lines;
                                                        setData(newData);
                                                    }}
                                                />
                                            </>
                                        ) : (
                                            <>
                                                <Multiselect
                                                    options={classCustomMethods}
                                                    displayValue='name'
                                                    placeholder="Select methods..."
                                                    showCheckbox={true}
                                                    style={{ chips: { background: 'rgb(231 229 228)', color: 'rgb(61 56 70)' } }}
                                                    selectedValues={selectedCustomMethods}
                                                    onSelect={(selectedList, selectedItem) => handleCustomMethodSelect(selectedList, selectedItem, index)}
                                                    onRemove={(selectedList, selectedItem) => handleCustomMethodRemove(selectedList, selectedItem, index)}
                                                />
                                                <div className="mt-2 space-y-2">
                                                    {selectedCustomMethods.map((method, mIdx) => (
                                                        <div key={mIdx} className="space-y-1 bg-stone-50 p-2 rounded-md border border-stone-200">
                                                            <div className="flex justify-between items-center">
                                                                <span className="text-xs font-bold text-gray-600">{method.name}</span>
                                                            </div>
                                                            <input 
                                                                type="text"
                                                                placeholder="Label Template (e.g. Call {{ seller.phone }})"
                                                                value={method.label || ''}
                                                                onChange={(e) => handleMethodLabelChange(index, mIdx, e.target.value)}
                                                                className="w-full border border-gray-300 rounded-md px-2 py-1 text-xs"
                                                            />
                                                        </div>
                                                    ))}
                                                </div>
                                            </>
                                        )}
                                    </FormControl>
                                    <FormControl className="space-y-1">
                                        <h3 className="text-xl font-bold">Text</h3>
                                        {!pencelClickText && (
                                            <div className="flex flex-wrap gap-2">
                                                <h2 className="text-l">
                                                    {section.text ? (
                                                        <span>{section.text}</span>
                                                    ) : (
                                                        <span style={{ color: 'grey' }}>No text specified...</span>
                                                    )}
                                                </h2>
                                                <Pencil
                                                    className="cursor-pointer ml-auto"
                                                    onClick={handlePencilClickText}
                                                />
                                            </div>
                                        )}

                                        {pencelClickText && (
                                            <>
                                                <Textarea
                                                    name="text"
                                                    placeholder="Description, explanation, welcome message, ..."
                                                    minRows={4}
                                                    maxRows={4}
                                                    value={newText}
                                                    onChange={handleInputChangeText}
                                                />
                                                <div className="flex flex-wrap gap-2 ml-auto">
                                                    <button
                                                        onClick={() => handleTextChange(index)}
                                                        className="w-[40px] h-[40px] bg-blue-500 text-white px-2 py-1 rounded-md hover:bg-blue-600"
                                                    >
                                                        <Save />
                                                    </button>
                                                    <button
                                                        onClick={handleTextCancel}
                                                        className="w-[40px] h-[40px] bg-gray-300 text-gray-700 px-2 py-1 rounded-md hover:bg-gray-400"
                                                    >
                                                        <Ban />
                                                    </button>
                                                </div>
                                            </>
                                        )}
                                    </FormControl>
                                    </>)}
                                    {!isActivityActionSection(data[index]) && !CHROME_LAYOUTS.includes(data[index].layout) && (<>
                                    <FormControl className="space-y-1">
                                        <h3 className="text-xl font-bold">Related To</h3>
                                        <p className="text-xs text-gray-500">Show items related to the selected section's object (e.g. same category).</p>
                                        <select
                                            value={data[index].related_to || ''}
                                            onChange={(e) => handleRelatedToChange(index, e.target.value)}
                                            className="border border-gray-300 rounded-md px-2 py-1.5 text-sm w-full"
                                        >
                                            <option value="">None</option>
                                            {data.filter((_, i) => i !== index).map((sec) => (
                                                <option key={sec.id} value={sec.id}>{sec.name}</option>
                                            ))}
                                        </select>
                                        {data[index].related_to && (
                                            <div className="space-y-1">
                                                <label className="text-xs text-gray-500">Relationship mode</label>
                                                <select
                                                    value={data[index].relationship?.mode || 'direct'}
                                                    onChange={(e) => handleRelationshipModeChange(index, e.target.value)}
                                                    className="border border-gray-300 rounded-md px-2 py-1.5 text-sm w-full"
                                                >
                                                    <option value="direct">Direct relationship</option>
                                                    <option value="same_parent">Same parent</option>
                                                </select>
                                                {data[index].relationship?.mode === 'same_parent' && (
                                                    <>
                                                        <label className="text-xs text-gray-500">Via class</label>
                                                        <select
                                                            value={data[index].relationship?.via || ''}
                                                            onChange={(e) => handleRelationshipViaChange(index, e.target.value)}
                                                            className="border border-gray-300 rounded-md px-2 py-1.5 text-sm w-full"
                                                        >
                                                            <option value="">Auto-detect if possible</option>
                                                            {isSuccessClasses && classes.map((cls) => (
                                                                <option key={cls.id} value={cls.id}>{cls.data.name}</option>
                                                            ))}
                                                        </select>
                                                    </>
                                                )}
                                                <label className="text-xs text-gray-500">Relation field override (optional, auto-detected if blank)</label>
                                                <input
                                                    type="text"
                                                    value={newRelationField}
                                                    onChange={(e) => handleRelationFieldChange(index, e.target.value)}
                                                    placeholder="e.g. category"
                                                    className="border border-gray-300 rounded-md px-2 py-1.5 text-sm w-full"
                                                />
                                            </div>
                                        )}
                                    </FormControl>
                                    <FormControl className="space-y-2">
                                        <h3 className="text-xl font-bold">Query</h3>
                                        <div className="grid grid-cols-2 gap-2">
                                            <div className="space-y-1">
                                                <label className="text-xs text-gray-500">Limit</label>
                                                <input
                                                    type="number"
                                                    min="1"
                                                    value={data[index].query?.limit || ''}
                                                    onChange={(e) => handleQueryNumberChange(index, 'limit', e.target.value)}
                                                    placeholder="e.g. 4"
                                                    className="border border-gray-300 rounded-md px-2 py-1.5 text-sm w-full"
                                                />
                                            </div>
                                            <div className="space-y-1">
                                                <label className="text-xs text-gray-500">Offset</label>
                                                <input
                                                    type="number"
                                                    min="0"
                                                    value={data[index].query?.offset || ''}
                                                    onChange={(e) => handleQueryNumberChange(index, 'offset', e.target.value)}
                                                    placeholder="0"
                                                    className="border border-gray-300 rounded-md px-2 py-1.5 text-sm w-full"
                                                />
                                            </div>
                                        </div>
                                        {data[index].related_to && (
                                            <label className="flex items-center gap-2 text-xs text-gray-500">
                                                <input
                                                    type="checkbox"
                                                    checked={data[index].query?.exclude_source ?? false}
                                                    onChange={(e) => handleQueryExcludeSourceChange(index, e.target.checked)}
                                                />
                                                Exclude current item
                                            </label>
                                        )}
                                        <div className="space-y-1">
                                            <div className="flex items-center justify-between gap-2">
                                                <label className="text-xs text-gray-500">Sort</label>
                                                <button
                                                    type="button"
                                                    onClick={() => handleAddOrderBy(index)}
                                                    className="text-xs border border-gray-300 rounded-md px-2 py-1 hover:bg-gray-100"
                                                >
                                                    Add
                                                </button>
                                            </div>
                                            {(data[index].query?.order_by || []).map((order, orderIndex) => (
                                                <div key={orderIndex} className="flex gap-1">
                                                    <input
                                                        type="text"
                                                        list={`attr-list-${index}`}
                                                        value={order.field || ''}
                                                        onChange={(e) => handleOrderByChange(index, orderIndex, 'field', e.target.value)}
                                                        placeholder="field"
                                                        className="border border-gray-300 rounded-md px-2 py-1.5 text-xs min-w-0 flex-1"
                                                    />
                                                    <datalist id={`attr-list-${index}`}>
                                                        {classAttributes.map((attr) => (
                                                            <option key={attr.name} value={attr.name}>{attr.name}</option>
                                                        ))}
                                                    </datalist>
                                                    <select
                                                        value={order.direction || 'asc'}
                                                        onChange={(e) => handleOrderByChange(index, orderIndex, 'direction', e.target.value)}
                                                        className="border border-gray-300 rounded-md px-2 py-1.5 text-xs w-20"
                                                    >
                                                        <option value="asc">Asc</option>
                                                        <option value="desc">Desc</option>
                                                    </select>
                                                    <button
                                                        type="button"
                                                        onClick={() => handleRemoveOrderBy(index, orderIndex)}
                                                        className="border border-gray-300 rounded-md px-2 py-1 text-xs hover:bg-gray-100"
                                                    >
                                                        X
                                                    </button>
                                                </div>
                                            ))}
                                        </div>
                                        <div className="space-y-1">
                                            <div className="flex items-center justify-between gap-2">
                                                <label className="text-xs text-gray-500">Filters (AND)</label>
                                                <button
                                                    type="button"
                                                    onClick={() => handleAddFilter(index)}
                                                    className="text-xs border border-gray-300 rounded-md px-2 py-1 hover:bg-gray-100"
                                                >
                                                    Add
                                                </button>
                                            </div>
                                            {(data[index].query?.filters || []).map((filter, filterIndex) => (
                                                <div key={filterIndex} className="grid grid-cols-[1fr_78px_1fr_28px] gap-1">
                                                    <input
                                                        type="text"
                                                        list={`attr-list-${index}`}
                                                        value={filter.field || ''}
                                                        onChange={(e) => handleFilterChange(index, filterIndex, 'field', e.target.value)}
                                                        placeholder="field"
                                                        className="border border-gray-300 rounded-md px-2 py-1.5 text-xs min-w-0"
                                                    />
                                                    <select
                                                        value={filter.operator || 'eq'}
                                                        onChange={(e) => handleFilterChange(index, filterIndex, 'operator', e.target.value)}
                                                        className="border border-gray-300 rounded-md px-2 py-1.5 text-xs"
                                                    >
                                                        <option value="eq">=</option>
                                                        <option value="neq">!=</option>
                                                        <option value="lt">&lt;</option>
                                                        <option value="lte">&lt;=</option>
                                                        <option value="gt">&gt;</option>
                                                        <option value="gte">&gt;=</option>
                                                        <option value="contains">has</option>
                                                        <option value="in">in</option>
                                                        <option value="isnull">null</option>
                                                    </select>
                                                    <input
                                                        type="text"
                                                        value={filter.value || ''}
                                                        onChange={(e) => handleFilterChange(index, filterIndex, 'value', e.target.value)}
                                                        className="border border-gray-300 rounded-md px-2 py-1.5 text-xs min-w-0"
                                                    />
                                                    <button
                                                        type="button"
                                                        onClick={() => handleRemoveFilter(index, filterIndex)}
                                                        className="border border-gray-300 rounded-md px-2 py-1 text-xs hover:bg-gray-100"
                                                    >
                                                        X
                                                    </button>
                                                </div>
                                            ))}
                                        </div>
                                    </FormControl>
                                    <FormControl className="space-y-1">
                                        <h3 className="text-xl font-bold">View Detail Page</h3>
                                        <p className="text-xs text-gray-500">Each item links to this page, passing its ID as a parameter.</p>
                                        <select
                                            value={data[index].view_detail_page || ''}
                                            onChange={(e) => handleViewDetailPageChange(index, e.target.value)}
                                            className="border border-gray-300 rounded-md px-2 py-1.5 text-sm w-full"
                                        >
                                            <option value="">None</option>
                                            {pages.filter((p) => !p.type || p.type?.value !== 'activity').map((p) => (
                                                <option key={p.id} value={p.name}>{p.name}</option>
                                            ))}
                                        </select>
                                    </FormControl>
                                    </>)}
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
                                        className="flex h-fit w-58 flex-col gap-2 overflow-hidden text-ellipsis rounded-md bg-stone-200 p-4 hover:bg-stone-300 cursor-pointer"
                                    >
                                        {section.name}
                                    </h3>
                                </div>
                            )}
                        </div>
                    ))}
                    <button
                        onClick={() => {
                            const newSection = { id: window.crypto.randomUUID(), name: `Section Component ${data.length + 1}`, class: "", operations: { "create": false, "update": false, "delete": false }, attributes: [], layout: "table", col_span: 12, style: { color: "blue", density: "normal", radius: "xl", columns: "3", card_style: "elevated" } };

                            // Automatically use first class for new section component
                            if (isSuccessClasses && classes[0].id) {
                                newSection.class = classes[0].id;
                            }
                            setData([...data, newSection]);
                        }}
                        className="flex h-fit w-14 flex-col gap-2 overflow-hidden text-ellipsis rounded-md bg-stone-200 p-4 hover:bg-stone-300"
                    >
                        <Plus />
                    </button>
                    <button
                        onClick={() => {
                            const name = `Activity Button ${data.length + 1}`;
                            const newSection = {
                                id: window.crypto.randomUUID(),
                                name,
                                label: 'Complete step',
                                type: 'activity_action',
                                layout: 'activity_action',
                                class: "",
                                operations: { "create": false, "update": false, "delete": false },
                                attributes: [],
                                methods: [],
                                col_span: 12,
                                position: 'main',
                                style: { variant: 'button', align: 'right', size: 'lg' },
                            };
                            setData([...data, newSection]);
                        }}
                        className="flex h-fit min-w-28 flex-col gap-1 overflow-hidden text-ellipsis rounded-md bg-green-100 px-3 py-4 text-xs font-semibold text-green-800 hover:bg-green-200"
                    >
                        <Plus size={18} />
                        Activity button
                    </button>
                </div>
            )}
        </>
    );
};

export default Sections;
