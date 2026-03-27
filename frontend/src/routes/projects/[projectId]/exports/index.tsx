import React, { useMemo, useState } from "react";
import { useParams } from "react-router";
import {
    Box,
    Button,
    Card,
    CardContent,
    Checkbox,
    CircularProgress,
    Radio,
    RadioGroup,
    Sheet,
    Stack,
    Typography,
} from "@mui/joy";
import ProjectLayout from "$browser/components/projects/ProjectLayout";
import { useProject, useSystems } from "$browser/queries";
import { authAxios } from "$auth/state/auth";

type ExportType = "project" | "systems";

const ProjectExports: React.FC = () => {
    const { projectId } = useParams<{ projectId: string }>();

    const project = useProject(projectId);
    const systems = useSystems(projectId);

    const [exportType, setExportType] = useState<ExportType>("project");
    const [selectedSystemIds, setSelectedSystemIds] = useState<string[]>([]);

    const { name: projectName } = project.data ?? {};
    const availableSystems = useMemo(() => systems.data ?? [], [systems.data]);

    const toggleSystem = (systemId: string) => {
        setSelectedSystemIds((current) =>
            current.includes(systemId)
                ? current.filter((id) => id !== systemId)
                : [...current, systemId]
        );
    };

    const downloadJson = (data: unknown, filename: string) => {
        const jsonStr = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonStr], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");

        link.href = url;
        link.download = filename;

        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
    };

    const canExport =
        exportType === "project" || selectedSystemIds.length > 0;

    const handleExportProject = async () => {
        const response = await authAxios.get(`/v1/metadata/projects/export/${projectId}/`);
        downloadJson(response.data, `${projectName}-export.json`);
    };

    const handleExportSystems = async () => {
        const params = new URLSearchParams();
        selectedSystemIds.forEach((id) => {
            params.append("system_ids", id);
        });

        const response = await authAxios.get(`/v1/metadata/systems/export/`, {
            params,
        });
        downloadJson(response.data, `${projectName}-systems-export.json`);
    }

    const handleExport = async () => {
        if (!projectId) return;

        if (exportType === "project") {
            await handleExportProject();
            return;
        }
        await handleExportSystems();
    }

    if (!project.data) {
        return (
            <ProjectLayout>
                <Box sx={{ p: 3 }}>
                    <Typography>Project not found.</Typography>
                </Box>
            </ProjectLayout>
        );
    }

    return (
        <ProjectLayout>
            <Box sx={{ maxWidth: 720, p: 3 }}>
                <Stack spacing={3}>
                    <Box>
                        <Typography level="h2">Export</Typography>
                        <Typography level="body-sm" sx={{ mt: 0.5 }}>
                            Choose whether to export the full project or selected
                            systems from <strong>{projectName}</strong>.
                        </Typography>
                    </Box>

                    <RadioGroup
                        value={exportType}
                        onChange={(event) =>
                            setExportType(event.target.value as ExportType)
                        }
                    >
                        <Stack spacing={1.5}>
                            <Card
                                variant={exportType === "project" ? "solid" : "outlined"}
                                color={exportType === "project" ? "primary" : "neutral"}
                                invertedColors={exportType === "project"}
                                sx={{ cursor: "pointer" }}
                                onClick={() => setExportType("project")}
                            >
                                <CardContent>
                                    <Stack direction="row" spacing={2} alignItems="flex-start">
                                        <Radio value="project" />
                                        <Box>
                                            <Typography level="title-md">
                                                Export full project
                                            </Typography>
                                            <Typography level="body-sm">
                                                Includes everything in this project.
                                            </Typography>
                                        </Box>
                                    </Stack>
                                </CardContent>
                            </Card>

                            <Card
                                variant={exportType === "systems" ? "solid" : "outlined"}
                                color={exportType === "systems" ? "primary" : "neutral"}
                                invertedColors={exportType === "systems"}
                                sx={{ cursor: "pointer" }}
                                onClick={() => setExportType("systems")}
                            >
                                <CardContent>
                                    <Stack direction="row" spacing={2} alignItems="flex-start">
                                        <Radio value="systems" />
                                        <Box>
                                            <Typography level="title-md">
                                                Export selected systems
                                            </Typography>
                                            <Typography level="body-sm">
                                                Choose one or more systems to export.
                                            </Typography>
                                        </Box>
                                    </Stack>
                                </CardContent>
                            </Card>
                        </Stack>
                    </RadioGroup>

                    {exportType === "systems" && (
                        <Sheet
                            variant="outlined"
                            sx={{
                                p: 2,
                                borderRadius: "md",
                            }}
                        >
                            <Stack spacing={2}>
                                <Box>
                                    <Typography level="title-md">Systems</Typography>
                                    <Typography level="body-sm">
                                        Select one or more systems to include.
                                    </Typography>
                                </Box>

                                {systems.isLoading ? (
                                    <Stack direction="row" spacing={1.5} alignItems="center">
                                        <CircularProgress size="sm" />
                                        <Typography level="body-sm">
                                            Loading systems…
                                        </Typography>
                                    </Stack>
                                ) : availableSystems.length === 0 ? (
                                    <Typography level="body-sm">
                                        No systems available in this project.
                                    </Typography>
                                ) : (
                                    <Stack spacing={1}>
                                        {availableSystems.map(
                                            (system: { id: string; name: string }) => (
                                                <Sheet
                                                    key={system.id}
                                                    variant="outlined"
                                                    sx={{
                                                        p: 1.5,
                                                        borderRadius: "sm",
                                                    }}
                                                >
                                                    <Checkbox
                                                        label={system.name}
                                                        checked={selectedSystemIds.includes(system.id)}
                                                        onChange={() => toggleSystem(system.id)}
                                                    />
                                                </Sheet>
                                            )
                                        )}
                                    </Stack>
                                )}
                            </Stack>
                        </Sheet>
                    )}

                    <Box sx={{ display: "flex", justifyContent: "flex-end" }}>
                        <Button onClick={handleExport} disabled={!canExport}>
                            Export
                        </Button>
                    </Box>
                </Stack>
            </Box>
        </ProjectLayout>
    );
};

export default ProjectExports;