import React, { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';
import useLocalStorage from './useLocalStorage';

type SectionItem = {
  id: string;
  name?: string;
  class?: string;
  layout?: string;
  position?: string;
  visible?: boolean;
};

const REGION_POSITIONS = [
  { value: 'header', label: 'Header', color: 'bg-blue-50 border-blue-200' },
  { value: 'hero', label: 'Hero', color: 'bg-purple-50 border-purple-200' },
  { value: 'main', label: 'Main', color: 'bg-green-50 border-green-200' },
  { value: 'sidebar', label: 'Sidebar', color: 'bg-orange-50 border-orange-200' },
  { value: 'footer', label: 'Footer', color: 'bg-gray-50 border-gray-200' },
] as const;

type RegionPosition = typeof REGION_POSITIONS[number];

type SectionRowProps = {
  section: SectionItem;
  onPositionChange: (sectionId: string, position: string) => void;
  onVisibilityToggle: (sectionId: string) => void;
};

const SectionRow: React.FC<SectionRowProps> = ({ section, onPositionChange, onVisibilityToggle }) => (
  <div className="flex items-center justify-between bg-white p-3 rounded-md border border-gray-200">
    <div className="flex-1">
      <h4 className="font-medium">{section.name}</h4>
      <p className="text-xs text-gray-500">
        {section.class && `Class: ${section.class}`}
        {section.layout && ` - Layout: ${section.layout}`}
      </p>
    </div>
    <div className="flex items-center gap-2">
      <select
        value={section.position || 'main'}
        onChange={(event) => onPositionChange(section.id, event.target.value)}
        className="px-2 py-1 text-xs border border-gray-300 rounded-md bg-white cursor-pointer hover:border-blue-400"
      >
        <option value="header">Header</option>
        <option value="hero">Hero</option>
        <option value="main">Main</option>
        <option value="sidebar">Sidebar</option>
        <option value="footer">Footer</option>
      </select>
      <button
        onClick={() => onVisibilityToggle(section.id)}
        className="p-1 hover:bg-gray-100 rounded-md transition"
        title={section.visible === false ? 'show' : 'hide'}
      >
        {section.visible === false ? (
          <EyeOff size={18} className="text-gray-400" />
        ) : (
          <Eye size={18} className="text-gray-600" />
        )}
      </button>
    </div>
  </div>
);

type RegionPanelProps = {
  region: RegionPosition;
  sections: SectionItem[];
  isExpanded: boolean;
  onToggle: (position: string) => void;
  onPositionChange: (sectionId: string, position: string) => void;
  onVisibilityToggle: (sectionId: string) => void;
};

type RegionSectionsProps = {
  sections: SectionItem[];
  onPositionChange: (sectionId: string, position: string) => void;
  onVisibilityToggle: (sectionId: string) => void;
};

const RegionSections: React.FC<RegionSectionsProps> = ({
  sections,
  onPositionChange,
  onVisibilityToggle,
}) => {
  if (sections.length === 0) {
    return <p className="text-sm text-gray-500 italic">No components in this region</p>;
  }

  return (
    <>
      {sections.map((section) => (
        <SectionRow
          key={section.id}
          section={section}
          onPositionChange={onPositionChange}
          onVisibilityToggle={onVisibilityToggle}
        />
      ))}
    </>
  );
};

const RegionPanel: React.FC<RegionPanelProps> = ({
  region,
  sections,
  isExpanded,
  onToggle,
  onPositionChange,
  onVisibilityToggle,
}) => (
  <div className={`border-2 rounded-lg p-4 ${region.color}`}>
    <button
      type="button"
      onClick={() => onToggle(region.value)}
      className="flex w-full items-center justify-between cursor-pointer mb-2 border-0 bg-transparent p-0 text-left"
    >
      <div className="flex items-center gap-2">
        <h3 className="text-lg font-bold">{region.label}</h3>
        <span className="text-xs px-2 py-1 bg-white rounded-full">{sections.length}</span>
      </div>
      <span className="text-xl">{isExpanded ? 'v' : '>'}</span>
    </button>

    {isExpanded && (
      <div className="space-y-2 mt-3">
        <RegionSections
          sections={sections}
          onPositionChange={onPositionChange}
          onVisibilityToggle={onVisibilityToggle}
        />
      </div>
    )}
  </div>
);

export const PageRegions: React.FC = () => {
  const [sections, setSections, isSuccessSections] = useLocalStorage('sections', []);
  const [expandedRegions, setExpandedRegions] = useState<Set<string>>(new Set(['main']));

  const toggleRegion = (position: string) => {
    const newExpanded = new Set(expandedRegions);
    if (newExpanded.has(position)) {
      newExpanded.delete(position);
    } else {
      newExpanded.add(position);
    }
    setExpandedRegions(newExpanded);
  };

  const toggleSectionVisibility = (sectionId: string) => {
    const newSections = [...sections];
    const section = newSections.find((item) => item.id === sectionId);
    if (section) {
      section.visible = !section.visible;
      setSections(newSections);
    }
  };

  const handleSectionPositionChange = (sectionId: string, position: string) => {
    const newSections = [...sections];
    const sectionIndex = newSections.findIndex((section) => section.id === sectionId);
    if (sectionIndex >= 0) {
      newSections[sectionIndex].position = position;
      setSections(newSections);
    }
  };

  const getSectionsForPosition = (position: string) => {
    return sections.filter((section) => (section.position || 'main') === position);
  };

  if (!isSuccessSections) {
    return <div>Loading...</div>;
  }

  return (
    <div className="w-full space-y-4">
      <p className="text-sm text-gray-600 mb-6">
        Below are section components organized by page position. Expand each area to view and manage components in that region.
      </p>

      {REGION_POSITIONS.map((region) => (
        <RegionPanel
          key={region.value}
          region={region}
          sections={getSectionsForPosition(region.value)}
          isExpanded={expandedRegions.has(region.value)}
          onToggle={toggleRegion}
          onPositionChange={handleSectionPositionChange}
          onVisibilityToggle={toggleSectionVisibility}
        />
      ))}

      <div className="border-t pt-4 mt-6">
        <p className="text-xs text-gray-500">
          Tip: Edit each component&apos;s detailed properties and position in the &quot;Section Components&quot; tab.
        </p>
      </div>
    </div>
  );
};

export default PageRegions;
