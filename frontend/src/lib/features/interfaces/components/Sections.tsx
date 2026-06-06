import {
    Divider,
    FormControl,
    Input,
    Textarea,
    Tooltip,
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
    'commerce-header', 'dashboard-header', 'split-header', 'app-header', 'compact-header', 'mega-header',
    'service-bar', 'link-grid', 'brand-strip', 'compact-footer', 'legal-footer', 'newsletter-footer', 'social-footer', 'mega-footer',
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
const toAttributeOption = (attr: any) => {
    if (typeof attr === 'string') return { name: attr };
    return { ...(attr || {}), name: attr?.name || '' };
};
const getAttributeRenderAs = (attr: any) => {
    if (typeof attr === 'string') return 'text';
    return attr?.render?.as || (attr?.is_link ? 'link' : 'text');
};
const getAttributeAction = (attr: any) => {
    if (typeof attr === 'string') return { type: 'none' };
    return attr?.action || { type: attr?.is_link ? 'navigate' : 'none' };
};
const normalizeAttribute = (attr: any) => typeof attr === 'string' ? { name: attr } : { ...(attr || {}) };
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
const dataScopeMode = (section: any) => section?.style?.data_scope?.mode || 'all';
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

export const Sections: React.FC<Props> = () => {
    const { systemId } = useParams();
    const [data, setData, isSuccess] = useLocalStorage('sections', []);
    const [editIndex, setEditIndex] = useState(-1);
    const [newName, setNewName] = useState('');
    const [newText, setNewText] = useState('');
    const [newImageUrl, setNewImageUrl] = useState('');
    const [newImageAlt, setNewImageAlt] = useState('');
    const [newRelationField, setNewRelationField] = useState('');
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
    const [pages, setPages, isSuccessPages] = useLocalStorage('pages', []);
    const [availablePaths, setAvailablePaths] = useState<string[]>([]);
    const selectedAttributeOptions = React.useMemo(
        () => (selectedAttributes || [])
            .filter((attr: any) => !isReadonlyAttribute(attr))
            .map(toAttributeOption)
            .filter((attr: any) => attr.name),
        [selectedAttributes],
    );
    const selectedReadonlyAttributeOptions = React.useMemo(
        () => (selectedAttributes || [])
            .filter(isReadonlyAttribute)
            .map((attr: any) => ({ ...toAttributeOption(attr), readonly: true, source: 'related' }))
            .filter((attr: any) => attr.name),
        [selectedAttributes],
    );
    const selectedAttributeNames = React.useMemo(
        () => new Set((selectedAttributes || []).map(getAttributeName).filter(Boolean)),
        [selectedAttributes],
    );
    const readonlyAttributeOptions = React.useMemo(
        () => availablePaths
            .filter((path) => !selectedClassName || !path.toLowerCase().startsWith(`${String(selectedClassName).toLowerCase()}.`))
            .filter((path) => !selectedAttributeNames.has(path))
            .map((path) => ({ name: path, readonly: true, source: 'related' })),
        [availablePaths, selectedClassName, selectedAttributeNames],
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
        setNewImageUrl(data[index].style?.image_url || data[index].image_url || '');
        setNewImageAlt(data[index].style?.image_alt || data[index].image_alt || '');

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

    const handleImageUrlChange = (index: number) => {
        const newData = [...data];
        const style = { ...(newData[index].style || {}) };
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

    const handleAddSelectField = (index: number) => {
        const newData = [...data];
        const firstField = queryFieldOptions[0] || '';
        newData[index].query = {
            ...(newData[index].query || {}),
            select: [...(newData[index].query?.select || []), firstField],
        };
        setData(newData);
    };

    const handleSelectFieldChange = (index: number, fieldIndex: number, value: string) => {
        const newData = [...data];
        const select = [...(newData[index].query?.select || [])];
        select[fieldIndex] = value;
        newData[index].query = { ...(newData[index].query || {}), select };
        setData(newData);
    };

    const handleRemoveSelectField = (index: number, fieldIndex: number) => {
        const newData = [...data];
        const select = [...(newData[index].query?.select || [])];
        select.splice(fieldIndex, 1);
        newData[index].query = { ...(newData[index].query || {}), select };
        setData(newData);
    };

    const handleDataSourceFromChange = (index: number, model: string) => {
        const newData = [...data];
        newData[index].data_source = {
            ...(newData[index].data_source || {}),
            mode: 'query',
            from: { model },
        };
        setData(newData);
    };

    const handleDataScopeModeChange = (index: number, mode: string) => {
        const newData = [...data];
        const style = { ...(newData[index].style || {}) };
        if (mode === 'actor_owned') {
            style.data_scope = {
                ...(style.data_scope || {}),
                mode: 'actor_owned',
                source: 'current_actor',
                model: newData[index].primary_model || selectedClassName || '',
            };
        } else {
            delete style.data_scope;
        }
        newData[index].style = style;
        setData(newData);
    };

    const handleAddJoin = (index: number) => {
        const newData = [...data];
        const fromModel = newData[index].data_source?.from?.model || newData[index].primary_model || selectedClassName || '';
        const model = classNameOptions.find((name: string) => name !== fromModel) || '';
        const joins = [...(newData[index].data_source?.joins || [])];
        joins.push({
            type: 'left',
            model,
            on: model && fromModel ? `${fromModel}.${sqlTableName(model)}_id = ${model}.id` : '',
        });
        newData[index].data_source = {
            ...(newData[index].data_source || {}),
            mode: 'query',
            from: { model: fromModel },
            joins,
        };
        setData(newData);
    };

    const handleJoinChange = (index: number, joinIndex: number, key: 'type' | 'model' | 'on', value: string) => {
        const newData = [...data];
        const joins = [...(newData[index].data_source?.joins || [])];
        joins[joinIndex] = { ...(joins[joinIndex] || {}), [key]: value };
        newData[index].data_source = {
            ...(newData[index].data_source || {}),
            mode: 'query',
            joins,
        };
        setData(newData);
    };

    const handleRemoveJoin = (index: number, joinIndex: number) => {
        const newData = [...data];
        const joins = [...(newData[index].data_source?.joins || [])];
        joins.splice(joinIndex, 1);
        newData[index].data_source = {
            ...(newData[index].data_source || {}),
            mode: 'query',
            joins,
        };
        setData(newData);
    };

    const buildSqlPreview = (section: any) => {
        const fromModel = section.data_source?.from?.model || section.primary_model || selectedClassName || 'Item';
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
        const relatedClause = section.related_to
            ? ['  -- plus current-object filter from Related To shortcut']
            : [];
        const scopeClause = dataScopeMode(section) === 'actor_owned'
            ? [`  -- scoped to current actor's ${section.primary_model || fromModel} record`]
            : [];
        const orderBy = (section.query?.order_by || [])
            .filter((order: any) => order.field)
            .map((order: any) => `${sqlFieldRef(order.field, fromModel)} ${String(order.direction || 'asc').toUpperCase()}`)
            .join(', ');
        return [
            'SELECT',
            selectFields,
            `FROM ${fromTable}`,
            joins,
            [...scopeClause, ...filters, ...relatedClause].length ? `WHERE\n${[...scopeClause, ...filters, ...relatedClause].join('\n  AND ')}` : '',
            orderBy ? `ORDER BY ${orderBy}` : '',
            section.query?.limit ? `LIMIT ${section.query.limit}` : '',
            section.query?.offset ? `OFFSET ${section.query.offset}` : '',
            ';',
        ].filter(Boolean).join('\n');
    };

    const handleRelationFieldChange = (index: number, value: string) => {
        setNewRelationField(value);
        const newData = [...data];
        newData[index].relation_field = value || null;
        setData(newData);
    };

    const handleItemClickTypeChange = (index: number, type: string) => {
        const newData = [...data];
        const behavior = { ...(newData[index].behavior || {}) };
        if (!type || type === 'none') {
            delete behavior.item_click;
        } else {
            behavior.item_click = {
                ...(behavior.item_click || {}),
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
        const behavior = { ...(newData[index].behavior || {}) };
        behavior.item_click = {
            ...(behavior.item_click || {}),
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

    const handleReadonlyAttributeSelect = (selectedList, selectedItem, sectionIndex: number) => {
        const selectedName = getAttributeName(selectedItem);
        if (!selectedName) return;
        const existingNames = new Set((selectedAttributes || []).map(getAttributeName));
        const readonlyAttr = {
            ...toAttributeOption(selectedItem),
            name: selectedName,
            readonly: true,
            source: 'related',
            render: selectedItem?.render || { as: 'text' },
            action: selectedItem?.action || { type: 'none' },
        };
        const updatedAttributes = existingNames.has(selectedName)
            ? selectedAttributes
            : [...selectedAttributes, readonlyAttr];
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
                                                        color={selectedClassObject?.id === e.id ? 'primary' : 'neutral'}
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
                                    <div className='space-y-1'>
                                        <h3 className="text-xl font-bold">Attributes</h3>
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
                                        {selectedClassName && (
                                            <p className="text-[11px] text-gray-500 mt-1">
                                                Fields are from {selectedClassName}. Use related fields below for read-only values from other classes.
                                            </p>
                                        )}
                                        <div className="mt-2 space-y-1">
                                            {selectedAttributes.map((attr, attrIdx) => {
                                                if (isReadonlyAttribute(attr)) return null;
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
                                        <h3 className="text-base font-bold pt-3">Read-only Attributes</h3>
                                        <Multiselect
                                            options={readonlyAttributeOptions}
                                            displayValue='name'
                                            placeholder="Select read-only attributes..."
                                            showCheckbox={true}
                                            style={{ chips: { background: 'rgb(254 215 170)', color: 'rgb(124 45 18)' } }}
                                            selectedValues={[]}
                                            onSelect={(selectedList, selectedItem) => handleReadonlyAttributeSelect(selectedList, selectedItem, index)}
                                        />
                                        <p className="text-[11px] text-gray-500 mt-1">
                                            Read-only attributes are displayed from related or non-primary classes and are not generated as editable form fields.
                                        </p>
                                        <div className="mt-2 space-y-1">
                                            {selectedAttributes.map((attr, attrIdx) => {
                                                if (!isReadonlyAttribute(attr)) return null;
                                                const action = getAttributeAction(attr);
                                                return (
                                                    <div key={attrIdx} className="bg-orange-50 px-2 py-1 rounded-md border border-orange-200 space-y-1">
                                                        <div className="flex items-center gap-2 min-w-0">
                                                            <span
                                                                className="text-xs font-medium truncate flex-1 min-w-0"
                                                                title={getAttributeName(attr)}
                                                            >
                                                                {getAttributeName(attr)}
                                                            </span>
                                                            <span className="text-[10px] rounded-full bg-orange-100 text-orange-700 px-1.5 py-0.5 shrink-0">read-only</span>
                                                            <button
                                                                type="button"
                                                                onClick={() => handleAttributeRemove([], attr, index)}
                                                                className="shrink-0 rounded-md border border-orange-200 bg-white p-1 text-orange-700 hover:bg-orange-100"
                                                                title="Remove read-only attribute"
                                                            >
                                                                <Trash size={12} />
                                                            </button>
                                                        </div>
                                                        <div className="flex items-center gap-2">
                                                            {getAttributeRenderAs(attr) === 'link' && <LinkIcon size={13} className="text-blue-600 shrink-0" />}
                                                            <select
                                                                value={getAttributeRenderAs(attr)}
                                                                onChange={(e) => handleAttributeRenderChange(index, attrIdx, e.target.value)}
                                                                className="border border-gray-300 rounded-md bg-white px-1 py-0.5 text-xs flex-1 min-w-0"
                                                                title="Field render mode"
                                                            >
                                                                {FIELD_RENDER_OPTIONS.map(option => (
                                                                    <option key={option.value} value={option.value}>{option.label}</option>
                                                                ))}
                                                            </select>
                                                            <select
                                                                value={action.type || 'none'}
                                                                onChange={(e) => updateAttributeAction(index, attrIdx, { type: e.target.value })}
                                                                className="border border-gray-300 rounded-md bg-white px-1 py-0.5 text-xs flex-1 min-w-0"
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
                                    <FormControl className="space-y-1">
                                        <h3 className="text-xl font-bold">Image URL</h3>
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
                                        <h3 className="text-xl font-bold">Data Scope</h3>
                                        <p className="text-xs text-gray-500">Controls which records this section is allowed to read before query filters are applied.</p>
                                        <select
                                            value={dataScopeMode(data[index])}
                                            onChange={(e) => handleDataScopeModeChange(index, e.target.value)}
                                            className="border border-gray-300 rounded-md px-2 py-1.5 text-sm w-full"
                                        >
                                            <option value="all">All records</option>
                                            <option value="actor_owned">Current actor only</option>
                                        </select>
                                        {dataScopeMode(data[index]) === 'actor_owned' && (
                                            <p className="text-[11px] text-emerald-700">
                                                Uses the logged-in actor to resolve this section's {data[index].primary_model || selectedClassName || 'model'} record. This is not stored as a query filter.
                                            </p>
                                        )}
                                    </FormControl>
                                    <FormControl className="space-y-2">
                                        <h3 className="text-xl font-bold">Data Source / Query</h3>
                                        <p className="text-xs text-gray-500">Configure how this section reads data. Display attributes are edited above; query columns are separate.</p>
                                        <div className="space-y-1">
                                            <label className="text-xs text-gray-500">From</label>
                                            <select
                                                value={data[index].data_source?.from?.model || data[index].primary_model || selectedClassName || ''}
                                                onChange={(e) => handleDataSourceFromChange(index, e.target.value)}
                                                className="border border-gray-300 rounded-md px-2 py-1.5 text-sm w-full"
                                            >
                                                <option value="">Auto from primary class</option>
                                                {classNameOptions.map((name: string) => (
                                                    <option key={name} value={name}>{name}</option>
                                                ))}
                                            </select>
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
                                                <div key={joinIndex} className="space-y-1 rounded-md border border-gray-200 bg-stone-50 p-2">
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
                                                <div key={fieldIndex} className="flex gap-1">
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
                                                <div key={filterIndex} className="grid grid-cols-[1fr_78px_1fr_28px] gap-1">
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
                                        <div className="space-y-1">
                                            <label className="text-xs text-gray-500">SQL Preview</label>
                                            <pre className="max-h-44 overflow-auto rounded-md border border-gray-200 bg-gray-950 p-2 text-[11px] leading-relaxed text-green-100 whitespace-pre-wrap">
                                                {buildSqlPreview(data[index])}
                                            </pre>
                                        </div>
                                    </FormControl>
                                    {isCollectionSection(data[index]) && (
                                        <FormControl className="space-y-2">
                                            <h3 className="text-xl font-bold">Item Click Action</h3>
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
                            const newSection = { id: window.crypto.randomUUID(), name: `Section Component ${data.length + 1}`, class: "", primary_model: "", operations: { "create": false, "update": false, "delete": false }, attributes: [], layout: "table", col_span: 12, style: { color: "blue", density: "normal", radius: "xl", columns: "3", card_style: "elevated" } };

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
