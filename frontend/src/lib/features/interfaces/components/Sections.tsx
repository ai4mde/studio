import {
    Divider,
    FormControl,
    Input,
    Textarea,
    Tooltip,
} from "@mui/joy";
import Chip from '@mui/joy/Chip';
import { Ban, Pencil, Plus, Save, Trash } from "lucide-react";
import Multiselect from 'multiselect-react-dropdown';
import React, { useState } from 'react';
import { useParams } from "react-router";
import { useClassAttributes, useClassCustomMethods, useSystemClasses } from "../queries";
import useLocalStorage from './useLocalStorage';

type Props = {
    interfaceId?: string;
};

const CHROME_LAYOUTS = [
    'promo-bar', 'logo', 'search-bar', 'icon-actions', 'nav-links', 'main-header', 'minimal-header',
    'commerce-header', 'dashboard-header', 'split-header', 'app-header', 'compact-header', 'mega-header',
    'service-bar', 'link-grid', 'brand-strip', 'compact-footer', 'legal-footer', 'newsletter-footer', 'social-footer', 'mega-footer',
    'site-nav', 'site-footer',
];
const CHROME_LAYOUT_SET = new Set(CHROME_LAYOUTS);

const METHODS_HINTS: Record<string, string> = {
    'promo-bar':      'Each line = promo strip item (e.g. "Gratis verzending vanaf €25,-"). Text field = right-side CTA label.',
    'logo':           'Text field = brand name shown in the logo.',
    'search-bar':     'Text field = search input placeholder.',
    'icon-actions':   'Each line = action label (e.g. "Inloggen", "♡", "Cart icon").',
    'nav-links':      'Line 1 = categories label. Lines 2–4 = extra nav links. Lines 5+ = top-right links (e.g. "Zakelijk").',
    'main-header':    'Text field = search placeholder. Uses promo-bar/logo/search-bar/icon-actions sections instead.',
    'minimal-header': 'Text field = cart amount shown in header button (e.g. "0,00").',
    'commerce-header': 'Full commerce header template.',
    'dashboard-header': 'Dense dashboard/app header template.',
    'split-header': 'Dark split header template.',
    'app-header': 'Operational app header template.',
    'compact-header': 'Compact one-row header template.',
    'mega-header': 'Large navigation-heavy header template.',
    'service-bar':    'Each line = a service bar link in the footer.',
    'link-grid':      'Line 1 = column title. Lines 2+ = footer links in that column.',
    'brand-strip':    'Each line = a brand name shown in the brand strip.',
    'compact-footer': 'Small compact footer template.',
    'legal-footer': 'Legal links footer template.',
    'newsletter-footer': 'Newsletter/CTA footer template.',
    'social-footer': 'Social/brand footer template.',
    'mega-footer': 'Large multi-column footer template.',
    'site-nav':       'Lines 1–3: promo strip items. Line 4: right-side highlight text.',
    'site-footer':    'Each line becomes a service-bar link in the footer.',
};

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

const SECTION_DATA_ROLE_OPTIONS = [
    { value: 'display_records', label: 'Display records', hint: 'Show many records from a model.' },
    { value: 'show_record', label: 'Show record', hint: 'Show one selected or contextual record.' },
    { value: 'create_record', label: 'Create record', hint: 'Collect fields and create a new database row.' },
    { value: 'update_record', label: 'Update record', hint: 'Edit selected fields on an existing row.' },
    { value: 'select_existing', label: 'Select existing', hint: 'Choose an existing row for the next action or workflow step.' },
    { value: 'decision_check', label: 'Decision check', hint: 'Show context and choose/resolve the next branch.' },
    { value: 'notify_summary', label: 'Notify summary', hint: 'Show a notification or result summary.' },
];

const SectionEditorGroup = ({
    title,
    description,
    defaultOpen = true,
    children,
}: {
    title: string;
    description?: string;
    defaultOpen?: boolean;
    children: React.ReactNode;
}) => (
    <details open={defaultOpen} className="rounded-lg border border-gray-200 bg-white p-3 shadow-sm">
        <summary className="cursor-pointer select-none text-[12px] font-semibold uppercase tracking-wide text-gray-700">
            {title}
        </summary>
        {description && <p className="mt-1 text-[11px] leading-snug text-gray-500">{description}</p>}
        <div className="mt-3 space-y-3">{children}</div>
    </details>
);

const asRecord = (value: any) => (value && typeof value === 'object' ? value : {});
const getAttributeName = (attr: any) => typeof attr === 'string' ? attr : attr?.name;
const toAttributeOption = (attr: any) => {
    if (typeof attr === 'string') return { name: attr };
    return { ...asRecord(attr), name: attr?.name || '' };
};
const normalizeAttribute = (attr: any) => typeof attr === 'string' ? { name: attr } : { ...asRecord(attr) };
const operationFlags = (operations: any) => {
    if (Array.isArray(operations)) {
        return {
            create: operations.includes('create'),
            update: operations.includes('update'),
            delete: operations.includes('delete'),
            select: operations.includes('select'),
            read: operations.includes('read'),
        };
    }
    return { ...asRecord(operations) };
};
const isReadonlyAttribute = (attr: any) => {
    const normalized = normalizeAttribute(attr);
    return !!normalized.readonly || normalized.source === 'related' || String(normalized.name || '').includes('.');
};
const isActivityActionSection = (section: any) => section?.type === 'activity_action' || section?.layout === 'activity_action';
const isCollectionSection = (section: any) => {
    const layout = String(section?.layout || '').toLowerCase();
    const role = String(section?.role || '').toLowerCase();
    return ['card', 'list', 'table', 'gallery'].includes(layout)
        || ['object_collection', 'child_collection', 'object_summary'].includes(role);
};
const inferSectionDataRole = (section: any) => {
    if (section?.data_role) return section.data_role;
    const ops = operationFlags(section?.operations);
    const layout = String(section?.layout || '').toLowerCase();
    const role = String(section?.role || '').toLowerCase();
    const intent = String(section?.style?.workflow_semantics?.intent || '').toLowerCase();
    if (intent.includes('notify')) return 'notify_summary';
    if (intent.includes('check') || intent.includes('decision')) return 'decision_check';
    if (ops.select && !ops.create && !ops.update && !ops.delete) return 'select_existing';
    if (ops.create && layout === 'form') return 'create_record';
    if (ops.update && layout === 'form') return 'update_record';
    if (layout === 'detail' || role.includes('detail') || role.includes('summary')) return 'show_record';
    return 'display_records';
};
const sqlTableName = (name: string) => String(name || 'items')
    .replace(/([a-z0-9])([A-Z])/g, '$1_$2')
    .replace(/[\s.-]+/g, '_')
    .toLowerCase();
const sqlFieldRef = (field: string, fromModel: string) => {
    const raw = String(field || '').trim();
    if (!raw) return '';
    if (raw.includes('.')) {
        const [model, attr] = raw.split('.', 2);
        return `${sqlTableName(model)}.${attr}`;
    }
    return `${sqlTableName(fromModel)}.${raw}`;
};
const sqlOperator = (op: string) => ({
    eq: '=', neq: '!=', lt: '<', lte: '<=', gt: '>', gte: '>=',
    contains: 'LIKE', in: 'IN', isnull: 'IS NULL',
}[op] || '=');
const sqlValue = (filter: any) => {
    if (filter.operator === 'isnull') return '';
    if (filter.value_from) return `:${filter.value_from}`;
    if (filter.operator === 'contains') return `'%${filter.value || ''}%'`;
    if (filter.operator === 'in') return `(${String(filter.value || '').split(',').map((v) => `'${v.trim()}'`).join(', ')})`;
    return filter.value ? `'${filter.value}'` : ':value';
};

export const Sections: React.FC<Props> = ({ interfaceId }) => {
    const { systemId } = useParams();
    const storagePrefix = interfaceId || 'new-interface';
    const [data, setData, isSuccess] = useLocalStorage(`interface:${storagePrefix}:sections`, []);
    const [editIndex, setEditIndex] = useState(-1);
    const [newName, setNewName] = useState('');
    const [newText, setNewText] = useState('');
    const [newImageUrl, setNewImageUrl] = useState('');
    const [newImageAlt, setNewImageAlt] = useState('');
    const [selectedOperations, setSelectedOperations] = useLocalStorage('selectedOperations', []);
    const [pencelClick, setPencelClick] = useState(false);
    const [pencelClickText, setPencelClickText] = useState(false);
    const [pencelClickImageUrl, setPencelClickImageUrl] = useState(false);
    const [classes, isSuccessClasses] = useSystemClasses(systemId);
    const [selectedClass, setSelectedClass] = useLocalStorage('selectedClass', '');
    const selectedClassObject = React.useMemo(() => {
        if (!classes || !selectedClass) return null;
        return classes.find((cls: any) =>
            cls.id === selectedClass ||
            cls.data?.name === selectedClass ||
            cls.data?.name?.toLowerCase() === String(selectedClass).toLowerCase()
        ) || null;
    }, [classes, selectedClass]);
    const selectedClassId = selectedClassObject?.id || selectedClass;
    const selectedClassName = selectedClassObject?.data?.name || selectedClass;
    const [classAttributes] = useClassAttributes(systemId, selectedClassId);
    const [classCustomMethods] = useClassCustomMethods(systemId, selectedClass)
    //const [attributes, setAttributes] = useState([]);
    const [selectedAttributes, setSelectedAttributes] = useLocalStorage('selectedAttributes', []);
    const [selectedCustomMethods, setSelectedCustomMethods] = useLocalStorage('selectedCustomMethods', [])
    const [pages, setPages, isSuccessPages] = useLocalStorage(`interface:${storagePrefix}:pages`, []);
    const [availablePaths, setAvailablePaths] = useState<string[]>([]);
    const selectedAttributeOptions = React.useMemo(
        () => (selectedAttributes || [])
            .filter((attr: any) => !isReadonlyAttribute(attr))
            .map(toAttributeOption)
            .filter((attr: any) => attr.name),
        [selectedAttributes],
    );
    const classNameOptions = React.useMemo(
        () => (classes || []).map((cls: any) => cls.data?.name).filter(Boolean),
        [classes],
    );
    const findClassForSection = React.useCallback((section: any) => {
        const ref = section?.class || section?.primary_model || '';
        if (!classes || !ref) return null;
        return classes.find((cls: any) =>
            cls.id === ref ||
            cls.data?.name === ref ||
            cls.data?.name?.toLowerCase() === String(ref).toLowerCase()
        ) || null;
    }, [classes]);

    const queryFieldOptions = React.useMemo(
        () => [
            ...(classAttributes || []).map((attr: any) => attr.name).filter(Boolean),
            ...availablePaths,
        ],
        [classAttributes, availablePaths],
    );

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
        const sectionClass = findClassForSection(data[index]);
        if (sectionClass) {
            setSelectedClass(sectionClass.id);
            const newData = [...data];
            newData[index].class = sectionClass.id;
            newData[index].primary_model = sectionClass.data?.name || newData[index].primary_model || '';
            setData(newData);
        } else if (data[index].class) {
            setSelectedClass(data[index].class);
        } else if (data[index].primary_model) {
            setSelectedClass(data[index].primary_model);
        }

        if (data[index].operations) {
            setSelectedOperations(operationFlags(data[index].operations));
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
        setNewImageUrl(data[index].style?.image_url || data[index].image_url || '');
        setNewImageAlt(data[index].style?.image_alt || data[index].image_alt || '');

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

    const handleImageUrlChange = (index: number) => {
        const newData = [...data];
        const style = { ...asRecord(newData[index].style) };
        if (newImageUrl) style.image_url = newImageUrl;
        else delete style.image_url;
        if (newImageAlt) style.image_alt = newImageAlt;
        else delete style.image_alt;
        newData[index].style = style;
        setData(newData);
        setPencelClickImageUrl(false);
    };

    const handlePencilClickImageUrl = () => {
        setPencelClickImageUrl(true);
    };

    const handleImageUrlCancel = () => {
        setPencelClickImageUrl(false);
        if (editIndex >= 0) {
            setNewImageUrl(data[editIndex].style?.image_url || data[editIndex].image_url || '');
            setNewImageAlt(data[editIndex].style?.image_alt || data[editIndex].image_alt || '');
        }
    };

    const handleQueryNumberChange = (index: number, key: 'limit' | 'offset', value: string) => {
        const newData = [...data];
        const parsed = Number.parseInt(value, 10);
        newData[index].query = {
            ...asRecord(newData[index].query),
            [key]: Number.isNaN(parsed) ? null : parsed,
        };
        setData(newData);
    };

    const handleAddOrderBy = (index: number) => {
        const newData = [...data];
        const firstField = classAttributes[0]?.name || '';
        newData[index].query = {
            ...asRecord(newData[index].query),
            order_by: [...(newData[index].query?.order_by || []), { field: firstField, direction: 'asc' }],
        };
        setData(newData);
    };

    const handleOrderByChange = (index: number, orderIndex: number, key: 'field' | 'direction', value: string) => {
        const newData = [...data];
        const orderBy = [...(newData[index].query?.order_by || [])];
        orderBy[orderIndex] = { ...asRecord(orderBy[orderIndex]), [key]: value };
        newData[index].query = { ...asRecord(newData[index].query), order_by: orderBy };
        setData(newData);
    };

    const handleRemoveOrderBy = (index: number, orderIndex: number) => {
        const newData = [...data];
        const orderBy = [...(newData[index].query?.order_by || [])];
        orderBy.splice(orderIndex, 1);
        newData[index].query = { ...asRecord(newData[index].query), order_by: orderBy };
        setData(newData);
    };

    const handleAddFilter = (index: number) => {
        const newData = [...data];
        const firstField = classAttributes[0]?.name || '';
        newData[index].query = {
            ...asRecord(newData[index].query),
            filter_logic: 'and',
            filters: [...(newData[index].query?.filters || []), { field: firstField, operator: 'eq', value: '' }],
        };
        setData(newData);
    };

    const handleFilterChange = (index: number, filterIndex: number, key: 'field' | 'operator' | 'value' | 'value_from', value: string) => {
        const newData = [...data];
        const filters = [...(newData[index].query?.filters || [])];
        const nextFilter = { ...asRecord(filters[filterIndex]), [key]: value };
        if (key === 'value') delete nextFilter.value_from;
        if (key === 'value_from') delete nextFilter.value;
        filters[filterIndex] = nextFilter;
        newData[index].query = { ...asRecord(newData[index].query), filter_logic: 'and', filters };
        setData(newData);
    };

    const handleFilterValueSourceChange = (index: number, filterIndex: number, source: 'value' | 'value_from') => {
        const newData = [...data];
        const filters = [...(newData[index].query?.filters || [])];
        const current = { ...asRecord(filters[filterIndex]) };
        if (source === 'value_from') {
            filters[filterIndex] = {
                ...current,
                value_from: current.value_from || current.value || '',
                value: undefined,
            };
            delete filters[filterIndex].value;
        } else {
            filters[filterIndex] = {
                ...current,
                value: current.value || '',
                value_from: undefined,
            };
            delete filters[filterIndex].value_from;
        }
        newData[index].query = { ...asRecord(newData[index].query), filter_logic: 'and', filters };
        setData(newData);
    };

    const handleRemoveFilter = (index: number, filterIndex: number) => {
        const newData = [...data];
        const filters = [...(newData[index].query?.filters || [])];
        filters.splice(filterIndex, 1);
        newData[index].query = { ...asRecord(newData[index].query), filters };
        setData(newData);
    };

    const handleAddSelectField = (index: number) => {
        const newData = [...data];
        const firstField = queryFieldOptions[0] || '';
        newData[index].query = {
            ...asRecord(newData[index].query),
            select: [...(newData[index].query?.select || []), firstField],
        };
        setData(newData);
    };

    const handleSelectFieldChange = (index: number, fieldIndex: number, value: string) => {
        const newData = [...data];
        const select = [...(newData[index].query?.select || [])];
        select[fieldIndex] = value;
        newData[index].query = { ...asRecord(newData[index].query), select };
        setData(newData);
    };

    const handleRemoveSelectField = (index: number, fieldIndex: number) => {
        const newData = [...data];
        const select = [...(newData[index].query?.select || [])];
        select.splice(fieldIndex, 1);
        newData[index].query = { ...asRecord(newData[index].query), select };
        setData(newData);
    };

    const sectionPrimaryModel = (section: any) =>
        section?.primary_model || selectedClassName || '';

    const normalizedDataSource = (section: any) => ({
        ...asRecord(section.data_source),
        mode: 'query',
        from: { model: sectionPrimaryModel(section) },
        joins: section.data_source?.joins || [],
    });

    const handleAddJoin = (index: number) => {
        const newData = [...data];
        const fromModel = sectionPrimaryModel(newData[index]);
        const model = classNameOptions.find((name: string) => name !== fromModel) || '';
        const joins = [...(newData[index].data_source?.joins || [])];
        joins.push({
            type: 'left',
            model,
            on: model && fromModel ? `${fromModel}.${sqlTableName(model)}_id = ${model}.id` : '',
        });
        newData[index].data_source = {
            ...normalizedDataSource(newData[index]),
            joins,
        };
        setData(newData);
    };

    const handleJoinChange = (index: number, joinIndex: number, key: 'type' | 'model' | 'on', value: string) => {
        const newData = [...data];
        const joins = [...(newData[index].data_source?.joins || [])];
        joins[joinIndex] = { ...asRecord(joins[joinIndex]), [key]: value };
        newData[index].data_source = {
            ...normalizedDataSource(newData[index]),
            joins,
        };
        setData(newData);
    };

    const handleRemoveJoin = (index: number, joinIndex: number) => {
        const newData = [...data];
        const joins = [...(newData[index].data_source?.joins || [])];
        joins.splice(joinIndex, 1);
        newData[index].data_source = {
            ...normalizedDataSource(newData[index]),
            joins,
        };
        setData(newData);
    };

    const buildSqlPreview = (section: any) => {
        const fromModel = sectionPrimaryModel(section) || 'Item';
        const fromTable = sqlTableName(fromModel);
        const selectedFields = (section.query?.select || []).filter(Boolean);
        const selectFields = selectedFields.length
            ? selectedFields.map((field: string) => {
                const ref = sqlFieldRef(field, fromModel);
                const alias = field.includes('.') ? ` AS ${field.replace(/[.\s-]+/g, '_').toLowerCase()}` : '';
                return `  ${ref}${alias}`;
            }).join(',\n')
            : '  *';
        const joins = (section.data_source?.joins || [])
            .filter((join: any) => join.model)
            .map((join: any) => `${String(join.type || 'left').toUpperCase()} JOIN ${sqlTableName(join.model)} ON ${join.on || '-- configure join condition'}`)
            .join('\n');
        const filters = (section.query?.filters || [])
            .filter((filter: any) => filter.field)
            .map((filter: any) => {
                const op = sqlOperator(filter.operator || 'eq');
                const value = sqlValue(filter);
                return `  ${sqlFieldRef(filter.field, fromModel)} ${op}${value ? ` ${value}` : ''}`;
            });
        const orderBy = (section.query?.order_by || [])
            .filter((order: any) => order.field)
            .map((order: any) => `${sqlFieldRef(order.field, fromModel)} ${String(order.direction || 'asc').toUpperCase()}`)
            .join(', ');
        return [
            'SELECT',
            selectFields,
            `FROM ${fromTable}`,
            joins,
            filters.length ? `WHERE\n${filters.join('\n  AND ')}` : '',
            orderBy ? `ORDER BY ${orderBy}` : '',
            section.query?.limit ? `LIMIT ${section.query.limit}` : '',
            section.query?.offset ? `OFFSET ${section.query.offset}` : '',
            ';',
        ].filter(Boolean).join('\n');
    };

    const handleItemClickTypeChange = (index: number, type: string) => {
        const newData = [...data];
        const behavior = { ...asRecord(newData[index].behavior) };
        if (!type || type === 'none') {
            delete behavior.item_click;
        } else {
            behavior.item_click = {
                ...asRecord(behavior.item_click),
                type,
            };
            if (type !== 'navigate') {
                delete behavior.item_click.target_page;
            }
        }
        newData[index].behavior = behavior;
        setData(newData);
    };

    const handleItemClickTargetPageChange = (index: number, pageName: string) => {
        const newData = [...data];
        const behavior = { ...asRecord(newData[index].behavior) };
        behavior.item_click = {
            ...asRecord(behavior.item_click),
            type: pageName ? 'navigate' : (behavior.item_click?.type || 'none'),
            target_page: pageName || '',
            params: behavior.item_click?.params || {},
        };
        if (!pageName) {
            delete behavior.item_click.target_page;
        } else {
            behavior.item_click.type = 'navigate';
        }
        newData[index].behavior = behavior;
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

    const handleInputChangeImageUrl = (event: React.ChangeEvent<HTMLInputElement>) => {
        setNewImageUrl(event.target.value);
    };

    const handleInputChangeImageAlt = (event: React.ChangeEvent<HTMLInputElement>) => {
        setNewImageAlt(event.target.value);
    };

    const handleDelete = (index: number) => {
        const newData = [...data];
        newData.splice(index, 1);
        setData(newData);
        setEditIndex(-1);
    };

    const toggleOperation = (sectionIndex: number, operation: 'create' | 'update' | 'delete' | 'select') => {
        const sectionOperations = operationFlags(selectedOperations);
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
        newData[sectionIndex].class = cls.data?.name || cls.id;
        newData[sectionIndex].primary_model = cls.data?.name || newData[sectionIndex].primary_model || '';
        setSelectedAttributes([]);
        newData[sectionIndex].attributes = [];
        setData(newData);
    };

    const handleAttributeSelect = (selectedList, selectedItem, sectionIndex: number) => {
        const selectedName = getAttributeName(selectedItem);
        if (!selectedName) return;
        const existingNames = new Set((selectedAttributes || []).map(getAttributeName));
        const updatedAttributes = existingNames.has(selectedName)
            ? selectedAttributes
            : [...selectedAttributes, toAttributeOption(selectedItem)];
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
            section.style = { ...asRecord(section.style), ...patch.style };
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
                                    <SectionEditorGroup title="Basic" description="Choose the domain class this component reads or edits.">
                                    <div className="space-y-1">
                                        <h3 className="text-sm font-semibold text-gray-700">Primary Class</h3>
                                        <div className="flex max-w-full flex-wrap gap-2">
                                            {isSuccessClasses && (
                                                classes.map((e) => (
                                                    <Chip
                                                        key={e.id}
                                                        onClick={() => toggleClass(index, e)}
                                                        color={selectedClassObject?.id === e.id ? 'primary' : 'neutral'}
                                                        sx={{ maxWidth: '100%' }}
                                                    >
                                                        {e.data.name}
                                                    </Chip>
                                                )
                                                ))}
                                        </div>
                                    </div>
                                    </SectionEditorGroup>
                                    <SectionEditorGroup title="Actions" description="Control what the user can do with records in this component.">
                                    <div className="space-y-1">
                                        <h3 className="text-sm font-semibold text-gray-700">Record operations</h3>
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
                                        </div>
                                    </div>
                                    <div className="space-y-1">
                                        <h3 className="text-sm font-semibold text-gray-600">Selection behavior</h3>
                                        <div className="flex gap-2">
                                            <Tooltip
                                                title="Enables row/item selection for choose or pick workflows and bulk actions, such as delete selected. This is not read/view."
                                                variant="soft"
                                            >
                                                <Chip
                                                    onClick={() => toggleOperation(index, 'select')}
                                                    color={selectedOperations.select ? 'primary' : 'neutral'}
                                                >
                                                    Enable selection
                                                </Chip>
                                            </Tooltip>
                                        </div>
                                        <p className="text-xs text-gray-500">
                                            Use only when users need to choose records or act on selected rows.
                                        </p>
                                    </div>
                                    </SectionEditorGroup>
                                    <SectionEditorGroup title="Fields" description="Choose display, editable, and read-only fields. Related fields are read-only context only.">
                                    <div className='space-y-1'>
                                        <h3 className="text-sm font-semibold text-gray-700">Editable / display attributes</h3>
                                        <Multiselect
                                            options={classAttributes}
                                            displayValue='name'
                                            placeholder="Select attributes..."
                                            showCheckbox={true}
                                            style={{ chips: { background: 'rgb(231 229 228)', color: 'rgb(61 56 70)' } }}
                                            selectedValues={selectedAttributeOptions}
                                            onSelect={(selectedList, selectedItem) => handleAttributeSelect(selectedList, selectedItem, index)}
                                            onRemove={(selectedList, selectedItem) => handleAttributeRemove(selectedList, selectedItem, index)}
                                        />
                                    </div>
                                    </SectionEditorGroup>
                                    <SectionEditorGroup title="Content" description="Optional copy, media, and section-level actions shown once for this component." defaultOpen={false}>
                                    <FormControl className="space-y-1">
                                        <h3 className="text-sm font-semibold text-gray-700">
                                            {CHROME_LAYOUT_SET.has(data[index].layout) ? 'Methods (one per line)' : 'Section Actions'}
                                        </h3>
                                        {CHROME_LAYOUT_SET.has(data[index].layout) ? (
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
                                                        <div key={method.id || method.name} className="space-y-1 bg-stone-50 p-2 rounded-md border border-stone-200">
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
                                        <h3 className="text-sm font-semibold text-gray-700">Text</h3>
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
                                    <FormControl className="space-y-1">
                                        <h3 className="text-sm font-semibold text-gray-700">Image URL</h3>
                                        {!pencelClickImageUrl && (
                                            <div className="flex flex-wrap gap-2">
                                                <h2 className="text-l break-all">
                                                    {section.style?.image_url ? (
                                                        <span>{section.style.image_url}</span>
                                                    ) : (
                                                        <span style={{ color: 'grey' }}>No image URL specified...</span>
                                                    )}
                                                </h2>
                                                <Pencil
                                                    className="cursor-pointer ml-auto"
                                                    onClick={handlePencilClickImageUrl}
                                                />
                                                {section.style?.image_url && (
                                                    <img
                                                        src={section.style.image_url}
                                                        alt={section.style?.image_alt || section.name || 'Section image'}
                                                        className="w-full h-24 object-cover rounded-md border border-gray-200"
                                                    />
                                                )}
                                            </div>
                                        )}

                                        {pencelClickImageUrl && (
                                            <>
                                                <Input
                                                    name="image_url"
                                                    placeholder="https://example.com/header.jpg"
                                                    value={newImageUrl}
                                                    onChange={handleInputChangeImageUrl}
                                                />
                                                <Input
                                                    name="image_alt"
                                                    placeholder="Alt text"
                                                    value={newImageAlt}
                                                    onChange={handleInputChangeImageAlt}
                                                />
                                                <div className="flex flex-wrap gap-2 ml-auto">
                                                    <button
                                                        onClick={() => handleImageUrlChange(index)}
                                                        className="w-[40px] h-[40px] bg-blue-500 text-white px-2 py-1 rounded-md hover:bg-blue-600"
                                                    >
                                                        <Save />
                                                    </button>
                                                    <button
                                                        onClick={handleImageUrlCancel}
                                                        className="w-[40px] h-[40px] bg-gray-300 text-gray-700 px-2 py-1 rounded-md hover:bg-gray-400"
                                                    >
                                                        <Ban />
                                                    </button>
                                                </div>
                                            </>
                                        )}
                                    </FormControl>
                                    </SectionEditorGroup>
                                    <SectionEditorGroup title="Advanced Query" description="Optional joins, select columns, sort, filters, and SQL preview." defaultOpen={false}>
                                    <FormControl className="space-y-2">
                                        <h3 className="text-sm font-semibold text-gray-700">Data Source / Query</h3>
                                        <p className="text-xs text-gray-500">Configure how this section reads data. Display attributes are edited above; query columns are separate.</p>
                                        <div className="space-y-1">
                                            <label className="text-xs text-gray-500">From</label>
                                            <div className="border border-gray-200 rounded-md px-2 py-1.5 text-sm w-full bg-stone-50 text-gray-700">
                                                {sectionPrimaryModel(data[index]) || 'Select a primary class first'}
                                            </div>
                                            <p className="text-[11px] text-gray-400">
                                                Query returns records of this section's primary class. Join other classes only for filtering, sorting, or read-only context.
                                            </p>
                                        </div>
                                        <div className="space-y-1">
                                            <div className="flex items-center justify-between gap-2">
                                                <label className="text-xs text-gray-500">Joins</label>
                                                <button
                                                    type="button"
                                                    onClick={() => handleAddJoin(index)}
                                                    className="text-xs border border-gray-300 rounded-md px-2 py-1 hover:bg-gray-100"
                                                >
                                                    Add
                                                </button>
                                            </div>
                                            {(data[index].data_source?.joins || []).map((join, joinIndex) => (
                                                <div key={`${join.type || 'left'}-${join.model || 'model'}-${join.on || 'condition'}`} className="space-y-1 rounded-md border border-gray-200 bg-stone-50 p-2">
                                                    <div className="grid grid-cols-[74px_1fr_28px] gap-1">
                                                        <select
                                                            value={join.type || 'left'}
                                                            onChange={(e) => handleJoinChange(index, joinIndex, 'type', e.target.value)}
                                                            className="border border-gray-300 rounded-md px-1 py-1.5 text-xs"
                                                        >
                                                            <option value="left">Left</option>
                                                            <option value="inner">Inner</option>
                                                            <option value="right">Right</option>
                                                        </select>
                                                        <select
                                                            value={join.model || ''}
                                                            onChange={(e) => handleJoinChange(index, joinIndex, 'model', e.target.value)}
                                                            className="border border-gray-300 rounded-md px-2 py-1.5 text-xs min-w-0"
                                                        >
                                                            <option value="">Model</option>
                                                            {classNameOptions.map((name: string) => (
                                                                <option key={name} value={name}>{name}</option>
                                                            ))}
                                                        </select>
                                                        <button
                                                            type="button"
                                                            onClick={() => handleRemoveJoin(index, joinIndex)}
                                                            className="border border-gray-300 rounded-md px-2 py-1 text-xs hover:bg-gray-100"
                                                        >
                                                            X
                                                        </button>
                                                    </div>
                                                    <input
                                                        type="text"
                                                        value={join.on || ''}
                                                        onChange={(e) => handleJoinChange(index, joinIndex, 'on', e.target.value)}
                                                        placeholder="e.g. CartItem.product_id = Product.id"
                                                        className="border border-gray-300 rounded-md px-2 py-1.5 text-xs w-full"
                                                    />
                                                </div>
                                            ))}
                                        </div>
                                        <div className="space-y-1">
                                            <div className="flex items-center justify-between gap-2">
                                                <label className="text-xs text-gray-500">Select Columns</label>
                                                <button
                                                    type="button"
                                                    onClick={() => handleAddSelectField(index)}
                                                    className="text-xs border border-gray-300 rounded-md px-2 py-1 hover:bg-gray-100"
                                                >
                                                    Add
                                                </button>
                                            </div>
                                            <p className="text-[11px] text-gray-400">Used only for SQL/query preview. It does not change rendered attributes.</p>
                                            {(data[index].query?.select || []).map((field, fieldIndex) => (
                                                <div key={field || 'select-field'} className="flex gap-1">
                                                    <input
                                                        type="text"
                                                        list={`query-field-list-${index}`}
                                                        value={field || ''}
                                                        onChange={(e) => handleSelectFieldChange(index, fieldIndex, e.target.value)}
                                                        placeholder="field or joined.field"
                                                        className="border border-gray-300 rounded-md px-2 py-1.5 text-xs min-w-0 flex-1"
                                                    />
                                                    <button
                                                        type="button"
                                                        onClick={() => handleRemoveSelectField(index, fieldIndex)}
                                                        className="border border-gray-300 rounded-md px-2 py-1 text-xs hover:bg-gray-100"
                                                    >
                                                        X
                                                    </button>
                                                </div>
                                            ))}
                                            <datalist id={`query-field-list-${index}`}>
                                                {queryFieldOptions.map((field: string) => (
                                                    <option key={field} value={field}>{field}</option>
                                                ))}
                                            </datalist>
                                        </div>
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
                                                <div key={`${order.field || 'field'}-${order.direction || 'asc'}`} className="flex gap-1">
                                                    <input
                                                        type="text"
                                                        list={`query-field-list-${index}`}
                                                        value={order.field || ''}
                                                        onChange={(e) => handleOrderByChange(index, orderIndex, 'field', e.target.value)}
                                                        placeholder="field"
                                                        className="border border-gray-300 rounded-md px-2 py-1.5 text-xs min-w-0 flex-1"
                                                    />
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
                                                <div key={`${filter.field || 'field'}-${filter.operator || 'eq'}-${filter.value_from || filter.value || 'value'}`} className="grid grid-cols-[1fr_78px_90px_1fr_28px] gap-1">
                                                    <input
                                                        type="text"
                                                        list={`query-field-list-${index}`}
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
                                                    <select
                                                        value={filter.value_from ? 'value_from' : 'value'}
                                                        onChange={(e) => handleFilterValueSourceChange(index, filterIndex, e.target.value as 'value' | 'value_from')}
                                                        className="border border-gray-300 rounded-md px-2 py-1.5 text-xs"
                                                        disabled={filter.operator === 'isnull'}
                                                    >
                                                        <option value="value">Literal</option>
                                                        <option value="value_from">Dynamic</option>
                                                    </select>
                                                    <input
                                                        type="text"
                                                        value={filter.value_from || filter.value || ''}
                                                        onChange={(e) => handleFilterChange(index, filterIndex, filter.value_from ? 'value_from' : 'value', e.target.value)}
                                                        placeholder={filter.value_from ? 'request.GET.instance_id_Model' : 'value'}
                                                        className="border border-gray-300 rounded-md px-2 py-1.5 text-xs min-w-0"
                                                        disabled={filter.operator === 'isnull'}
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
                                        <div className="space-y-1">
                                            <label className="text-xs text-gray-500">SQL Preview</label>
                                            <pre className="max-h-44 overflow-auto rounded-md border border-gray-200 bg-gray-950 p-2 text-[11px] leading-relaxed text-green-100 whitespace-pre-wrap">
                                                {buildSqlPreview(data[index])}
                                            </pre>
                                        </div>
                                    </FormControl>
                                    </SectionEditorGroup>
                                    {isCollectionSection(data[index]) && (
                                        <SectionEditorGroup title="Item Interaction" description="Component-level action when users click a card, row, or list item." defaultOpen={false}>
                                        <FormControl className="space-y-2">
                                            <h3 className="text-sm font-semibold text-gray-700">Item Click Action</h3>
                                            <p className="text-xs text-gray-500">Component-level interaction for clicking a card, list item, or table row.</p>
                                            <select
                                                value={data[index].behavior?.item_click?.type || 'none'}
                                                onChange={(e) => handleItemClickTypeChange(index, e.target.value)}
                                                className="border border-gray-300 rounded-md px-2 py-1.5 text-sm w-full"
                                            >
                                                <option value="none">None</option>
                                                <option value="navigate">Navigate to page</option>
                                                <option value="select">Select item</option>
                                            </select>
                                            {data[index].behavior?.item_click?.type === 'navigate' && (
                                                <div className="space-y-1">
                                                    <label className="text-xs text-gray-500">Target Page</label>
                                                    <select
                                                        value={data[index].behavior?.item_click?.target_page || ''}
                                                        onChange={(e) => handleItemClickTargetPageChange(index, e.target.value)}
                                                        className="border border-gray-300 rounded-md px-2 py-1.5 text-sm w-full"
                                                    >
                                                        <option value="">None</option>
                                                        {pages.filter((p) => !p.type || p.type?.value !== 'activity').map((p) => (
                                                            <option key={p.id} value={p.name}>{p.name}</option>
                                                        ))}
                                                    </select>
                                                </div>
                                            )}
                                        </FormControl>
                                        </SectionEditorGroup>
                                    )}
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
                            const newSection = { id: globalThis.crypto.randomUUID(), name: `Section Component ${data.length + 1}`, class: "", primary_model: "", data_role: "display_records", operations: { "create": false, "update": false, "delete": false, "select": false }, attributes: [], fields: [], actions: [], layout: "table", role: "object_collection", component: "ObjectList", col_span: 12, style: { color: "blue", density: "normal", radius: "xl", columns: "3", card_style: "elevated" } };

                            // Automatically use first class for new section component
                            if (isSuccessClasses && classes[0].id) {
                                newSection.class = classes[0].id;
                                newSection.primary_model = classes[0].data?.name || '';
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
                                id: globalThis.crypto.randomUUID(),
                                name,
                                label: 'Complete step',
                                type: 'activity_action',
                                data_role: 'workflow_action',
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
