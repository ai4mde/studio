import { useDiagramStore } from "$diagram/stores";
import { FormControl, FormLabel, Option, Select } from "@mui/joy";
import React, { useMemo, useState, useEffect } from "react";
import { useSystemClassClassifiers } from "./queries/importNode";


type Props = {
    object: any;
    setObject: (o: any) => void;
};

export const ImportClassNode: React.FC<Props> = ({ object, setObject }) => {
const system = useDiagramStore((s) => s.system);
  const nodes = useDiagramStore((s) => s.nodes);

  const [classifiers, isSuccess] = useSystemClassClassifiers(system);
  const [selectedClassifier, setSelectedClassifier] = useState<string | null>(null);

  const normalize = (v: unknown) => (v ?? "").toString().toLowerCase();

  // Helper: does this classifier already exist as a node in the diagram?
  const classifierExistsInDiagram = (classifier: any, node: any): boolean => {
    const nodeData = node.data ?? node; // be defensive

    // Try a few likely shapes where classifier data might live
    const clsData =
      nodeData?.cls?.data ??
      nodeData?.classifier?.data ??
      nodeData?.classifierData ??
      nodeData;

    const nodeName = clsData?.name;
    const nodeType = clsData?.type;

    return (
      nodeName === classifier.data?.name &&
      nodeType === classifier.data?.type
    );
  };

  const availableClassifiers = useMemo(
    () =>
      classifiers.filter(
        (classifier) => !nodes.some((n) => classifierExistsInDiagram(classifier, n)),
      ),
    [classifiers, nodes],
  );

  useEffect(() => {
    if (
      selectedClassifier &&
      !availableClassifiers.some((c) => c.id === selectedClassifier)
    ) {
      setSelectedClassifier(null);
      setObject((o: any) => ({ ...o, id: undefined }));
    }
  }, [availableClassifiers, selectedClassifier, setObject]);

    return (
        <>
            <FormControl size="sm" className="w-full">
                <FormLabel>Import a Class / Enum Node</FormLabel>
                <Select
                    placeholder={
                        !isSuccess
                            ? "Loading..."
                            : availableClassifiers.length === 0
                            ? "No nodes left to import"
                            : "Choose one..."
                    }
                    value={selectedClassifier}
                    onChange={(event, newValue) => {
                        setSelectedClassifier(newValue);
                        setObject((o: any) => ({ ...o, id: newValue }))
                    }}
                    disabled={!isSuccess || availableClassifiers.length === 0}
                    required
                >
                    {isSuccess && (
                        availableClassifiers.map((e) => {
                            const sameSystem = normalize(e.system_id) === normalize(system);

                            return (
                                <Option key={e.id} value={e.id} sx={{"--Option-decoratorChildHeight": "0px",}}>{e.data.name} ({e.data.type}) 
                                    {!sameSystem && e.system_name && 
                                        <span className="ml-2 px-2 py-0.5 rounded-md text-xs fond-medium bg-gray-200 text-gray-700">
                                            {e.system_name}
                                        </span>
                                    }
                                </Option>
                            )
                        }
                        ))}
                </Select>
            </FormControl>
        </>
    );
};
