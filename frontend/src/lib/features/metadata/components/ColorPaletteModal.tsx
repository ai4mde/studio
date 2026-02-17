import React, { useState, useEffect } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { authAxios } from "$lib/features/auth/state/auth";
import { queryClient } from "$lib/shared/hooks/queryClient";
import { Modal, ModalClose, ModalDialog, Button, Divider, LinearProgress } from "@mui/joy";
import { ChevronDown } from "lucide-react";

interface ClassifierColor {
  background_hex: string;
  text_hex: string;
}

interface ClassifierColors {
  [key: string]: ClassifierColor;
}

interface SystemSettings {
  classifier_colors: ClassifierColors;
}

interface ColorPaletteModalProps {
  systemId: string;
  open: boolean;
  onClose: () => void;
}

const DEFAULT_COLOR: ClassifierColor = {
  background_hex: "#FFFFFF",
  text_hex: "#000000",
};

const CLASSIFIER_GROUPS = [
  {
    name: "Class Diagram",
    types: ["class", "enum", "signal", "c4container", "c4component"],
  },
  {
    name: "Use Case Diagram",
    types: ["actor", "usecase", "system_boundary", "trigger", "scenario", "precondition", "postcondition", "system"],
  },
  {
    name: "Activity Diagram",
    types: ["action", "initial", "final", "fork", "join", "decision", "merge", "buffer", "swimlanegroup"],
  },
];

const ColorPaletteModal: React.FC<ColorPaletteModalProps> = ({
  systemId,
  open,
  onClose,
}) => {
  const [colors, setColors] = useState<ClassifierColors>({});
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(
    new Set()
  );

  // Fetch current settings
  const { data: settings, isLoading } = useQuery<SystemSettings>({
    queryKey: ["system", "settings", systemId],
    queryFn: async () => {
      const response = await authAxios.get(
        `/v1/metadata/systems/${systemId}/settings/`
      );
      return response.data;
    },
    enabled: open,
  });

  // Update settings mutation
  const updateSettings = useMutation({
    mutationFn: async (newColors: ClassifierColors) => {
      await authAxios.put(
        `/v1/metadata/systems/${systemId}/settings/`,
        {
          classifier_colors: newColors,
        }
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["system", "settings", systemId],
      });
      queryClient.invalidateQueries({
        queryKey: ["system", systemId],
      });
    },
  });

  // Initialize colors when settings are loaded
  useEffect(() => {
    const initialColors: ClassifierColors = {};
    CLASSIFIER_GROUPS.forEach((group) => {
      group.types.forEach((type) => {
        initialColors[type] = settings?.classifier_colors?.[type] || {
          ...DEFAULT_COLOR,
        };
      });
    });
    setColors(initialColors);
  }, [settings]);

  const toggleGroup = (groupName: string) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(groupName)) {
        next.delete(groupName);
      } else {
        next.add(groupName);
      }
      return next;
    });
  };

  const handleColorChange = (
    type: string,
    colorType: "background_hex" | "text_hex",
    value: string
  ) => {
    setColors((prev) => ({
      ...prev,
      [type]: {
        ...prev[type],
        [colorType]: value,
      },
    }));
  };

  const handleSave = async () => {
    try {
      await updateSettings.mutateAsync(colors);
      onClose();
    } catch (error) {
      console.error("Failed to save colors:", error);
    }
  };

  return (
    <Modal open={open} onClose={onClose}>
      <ModalDialog className="flex flex-col max-h-screen">
        <ModalClose
          sx={{
            position: "relative",
          }}
        />
        <div className="flex-1 overflow-y-auto p-4">
          <h1 className="text-xl font-bold mb-4">Edit Color Palette</h1>

          {isLoading && <LinearProgress />}

          <div className="space-y-2">
            {CLASSIFIER_GROUPS.map((group) => (
              <div key={group.name} className="w-[56rem] border rounded-lg overflow-hidden">
                {/* Group Header */}
                <button
                  onClick={() => toggleGroup(group.name)}
                  className="w-full flex items-center justify-between gap-2 p-4 bg-gray-100 hover:bg-gray-200 transition-colors"
                >
                  <h2 className="font-semibold text-sm">{group.name}</h2>
                  <ChevronDown
                    size={20}
                    className={`transition-transform ${
                      expandedGroups.has(group.name) ? "rotate-180" : ""
                    }`}
                  />
                </button>

                {/* Group Content */}
                {expandedGroups.has(group.name) && (
                  <div className="p-4 space-y-4 bg-white">
                    {group.types.map((type) => (
                      <div key={type} className="border-l-2 border-gray-300 pl-4">
                        <h3 className="font-semibold text-xs uppercase tracking-wide mb-2 text-gray-600">
                          {type}
                        </h3>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="flex flex-col gap-2">
                            <label className="text-xs font-medium">Background Color</label>
                            <div className="flex gap-2">
                              <input
                                type="color"
                                value={colors[type]?.background_hex || "#FFFFFF"}
                                onChange={(e) =>
                                  handleColorChange(type, "background_hex", e.target.value)
                                }
                                className="w-12 h-8 rounded cursor-pointer"
                              />
                              <input
                                type="text"
                                value={colors[type]?.background_hex || "#FFFFFF"}
                                onChange={(e) =>
                                  handleColorChange(type, "background_hex", e.target.value)
                                }
                                className="flex-1 px-2 py-1 border rounded text-xs font-mono"
                                placeholder="#FFFFFF"
                              />
                            </div>
                          </div>

                          <div className="flex flex-col gap-2">
                            <label className="text-xs font-medium">Text Color</label>
                            <div className="flex gap-2">
                              <input
                                type="color"
                                value={colors[type]?.text_hex || "#000000"}
                                onChange={(e) =>
                                  handleColorChange(type, "text_hex", e.target.value)
                                }
                                className="w-12 h-8 rounded cursor-pointer"
                              />
                              <input
                                type="text"
                                value={colors[type]?.text_hex || "#000000"}
                                onChange={(e) =>
                                  handleColorChange(type, "text_hex", e.target.value)
                                }
                                className="flex-1 px-2 py-1 border rounded text-xs font-mono"
                                placeholder="#000000"
                              />
                            </div>
                          </div>
                        </div>

                        {/* Preview */}
                        <div
                          className="mt-2 p-2 rounded text-center font-semibold text-xs"
                          style={{
                            backgroundColor: colors[type]?.background_hex || "#FFFFFF",
                            color: colors[type]?.text_hex || "#000000",
                          }}
                        >
                          Preview
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="border-t border-gray-200 p-4 flex gap-2 justify-end">
          <Button
            onClick={onClose}
            variant="outlined"
            color="neutral"
          >
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            variant="solid"
            loading={updateSettings.isPending}
          >
            Save Colors
          </Button>
        </div>
      </ModalDialog>
    </Modal>
  );
};

export default ColorPaletteModal;
