import React, { useState } from 'react';
import { Eye, EyeOff, Trash, Plus } from 'lucide-react';
import useLocalStorage from './useLocalStorage';

type Props = {};

const REGION_POSITIONS = [
  { value: 'header', label: 'Header', color: 'bg-blue-50 border-blue-200' },
  { value: 'hero', label: 'Hero', color: 'bg-purple-50 border-purple-200' },
  { value: 'main', label: 'Main', color: 'bg-green-50 border-green-200' },
  { value: 'sidebar', label: 'Sidebar', color: 'bg-orange-50 border-orange-200' },
  { value: 'footer', label: 'Footer', color: 'bg-gray-50 border-gray-200' },
];

export const PageRegions: React.FC<Props> = () => {
  const [sections, setSections, isSuccessSections] = useLocalStorage('sections', []);
  const [expandedRegions, setExpandedRegions] = useState<Set<string>>(
    new Set(['main']) // Default expand main region
  );

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
    const section = newSections.find((s) => s.id === sectionId);
    if (section) {
      section.visible = !section.visible;
      setSections(newSections);
    }
  };

  const getSectionsForPosition = (position: string) => {
    return sections.filter((s) => (s.position || 'main') === position);
  };

  if (!isSuccessSections) {
    return <div>Loading...</div>;
  }

  return (
    <div className="w-full space-y-4">
      <p className="text-sm text-gray-600 mb-6">
        Below are section components organized by page position. Expand each area to view and manage components in that region.
      </p>

      {REGION_POSITIONS.map((region) => {
        const regionSections = getSectionsForPosition(region.value);
        const isExpanded = expandedRegions.has(region.value);

        return (
          <div
            key={region.value}
            className={`border-2 rounded-lg p-4 ${region.color}`}
          >
            <div
              onClick={() => toggleRegion(region.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                  event.preventDefault();
                  toggleRegion(region.value);
                }
              }}
              role="button"
              tabIndex={0}
              className="flex items-center justify-between cursor-pointer mb-2"
            >
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold">{region.label}</h3>
                <span className="text-xs px-2 py-1 bg-white rounded-full">
                  {regionSections.length}
                </span>
              </div>
              <span className="text-xl">
                {isExpanded ? '▼' : '▶'}
              </span>
            </div>

            {isExpanded && (
              <div className="space-y-2 mt-3">
                {regionSections.length === 0 ? (
                  <p className="text-sm text-gray-500 italic">
                    No components in this region
                  </p>
                ) : (
                  regionSections.map((section) => (
                    <div
                      key={section.id}
                      className="flex items-center justify-between bg-white p-3 rounded-md border border-gray-200"
                    >
                      <div className="flex-1">
                        <h4 className="font-medium">{section.name}</h4>
                        <p className="text-xs text-gray-500">
                          {section.class && `Class: ${section.class}`}
                          {section.layout && ` • Layout: ${section.layout}`}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <select
                          value={section.position || 'main'}
                          onChange={(e) => {
                            const newSections = [...sections];
                            const idx = newSections.findIndex((s) => s.id === section.id);
                            if (idx >= 0) {
                              newSections[idx].position = e.target.value;
                              setSections(newSections);
                            }
                          }}
                          className="px-2 py-1 text-xs border border-gray-300 rounded-md bg-white cursor-pointer hover:border-blue-400"
                        >
                          <option value="header">Header</option>
                          <option value="hero">Hero</option>
                          <option value="main">Main</option>
                          <option value="sidebar">Sidebar</option>
                          <option value="footer">Footer</option>
                        </select>
                        <button
                          onClick={() => toggleSectionVisibility(section.id)}
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
                  ))
                )}
              </div>
            )}
          </div>
        );
      })}

      <div className="border-t pt-4 mt-6">
        <p className="text-xs text-gray-500">
          💡 Tip: Edit each component's detailed properties and position in the "Section Components" tab.
        </p>
      </div>
    </div>
  );
};

export default PageRegions;
