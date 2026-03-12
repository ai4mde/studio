import React, { useState } from 'react';
import { authAxios } from '$auth/state/auth';
import {
    Modal,
    ModalClose,
    ModalDialog,
    Button,
    Textarea,
    CircularProgress,
    Select,
    Option,
    Divider,
    Card,
    Typography,
    Chip,
} from '@mui/joy';
import { Sparkles, RefreshCw, Check, AlertCircle, Maximize2, Minimize2 } from 'lucide-react';

type Candidate = {
    candidate_index: number;
    style_name: string;
    num_pages: number;
    num_sections: number;
    styling: {
        backgroundColor?: string;
        accentColor?: string;
        textColor?: string;
        selectedStyle?: string;
    };
    html_preview?: string;
};

type Props = {
    interfaceId: string;
    onUpdate: () => void;
};

export const AIGeneration: React.FC<Props> = ({ interfaceId, onUpdate }) => {
    // Generate candidates state
    const [showGenerateModal, setShowGenerateModal] = useState(false);
    const [requirements, setRequirements] = useState('');
    const [model, setModel] = useState('llama-3.3-70b-versatile');
    const [isGenerating, setIsGenerating] = useState(false);
    const [candidates, setCandidates] = useState<Candidate[]>([]);
    const [showCandidatesModal, setShowCandidatesModal] = useState(false);
    const [selectedCandidate, setSelectedCandidate] = useState<number | null>(null);
    const [isSelecting, setIsSelecting] = useState(false);
    const [expandedPreview, setExpandedPreview] = useState<number | null>(null);

    // Refine state
    const [showRefineModal, setShowRefineModal] = useState(false);
    const [refinementPrompt, setRefinementPrompt] = useState('');
    const [isRefining, setIsRefining] = useState(false);
    const [refinementStatus, setRefinementStatus] = useState<{
        refinements_used: number;
        refinements_remaining: number;
        can_refine: boolean;
    } | null>(null);

    const [error, setError] = useState('');

    // Fetch refinement status
    const fetchRefinementStatus = async () => {
        try {
            const response = await authAxios.get(
                `/v1/metadata/interfaces/${interfaceId}/refinement_status/`
            );
            setRefinementStatus(response.data);
        } catch (err) {
            console.error('Error fetching refinement status:', err);
        }
    };

    // Generate candidates
    const handleGenerate = async () => {
        setIsGenerating(true);
        setError('');

        try {
            const response = await authAxios.post(
                `/v1/metadata/interfaces/${interfaceId}/generate_candidates/`,
                {
                    requirements: requirements || 'Generate a standard CRUD interface for all classes.',
                    model,
                }
            );

            setCandidates(response.data.candidates || []);
            setShowGenerateModal(false);
            setShowCandidatesModal(true);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to generate candidates');
        } finally {
            setIsGenerating(false);
        }
    };

    // Select candidate
    const handleSelectCandidate = async () => {
        if (selectedCandidate === null) return;

        setIsSelecting(true);
        setError('');

        try {
            await authAxios.post(
                `/v1/metadata/interfaces/${interfaceId}/select_candidate/`,
                { candidate_index: selectedCandidate }
            );

            setShowCandidatesModal(false);
            setCandidates([]);
            setSelectedCandidate(null);
            onUpdate();
            fetchRefinementStatus();
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to select candidate');
        } finally {
            setIsSelecting(false);
        }
    };

    // Refine interface
    const handleRefine = async () => {
        if (!refinementPrompt.trim()) return;

        setIsRefining(true);
        setError('');

        try {
            await authAxios.post(
                `/v1/metadata/interfaces/${interfaceId}/refine/`,
                {
                    refinement_prompt: refinementPrompt,
                    model,
                }
            );

            setShowRefineModal(false);
            setRefinementPrompt('');
            onUpdate();
            fetchRefinementStatus();
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to refine interface');
        } finally {
            setIsRefining(false);
        }
    };

    // Open refine modal
    const openRefineModal = () => {
        fetchRefinementStatus();
        setShowRefineModal(true);
    };

    return (
        <>
            {/* Action Buttons */}
            <div className="flex gap-2">
                <button
                    onClick={() => setShowGenerateModal(true)}
                    className="flex items-center gap-2 bg-purple-500 text-white px-4 py-2 rounded-md hover:bg-purple-600"
                >
                    <Sparkles size={18} />
                    AI Generate
                </button>
                <button
                    onClick={openRefineModal}
                    className="flex items-center gap-2 bg-orange-500 text-white px-4 py-2 rounded-md hover:bg-orange-600"
                >
                    <RefreshCw size={18} />
                    Refine
                </button>
            </div>

            {/* Generate Modal */}
            <Modal open={showGenerateModal} onClose={() => setShowGenerateModal(false)}>
                <ModalDialog sx={{ width: 500 }}>
                    <div className="flex justify-between items-center pb-2">
                        <Typography level="h4">
                            <Sparkles className="inline mr-2" size={20} />
                            AI Generate Interface
                        </Typography>
                        <ModalClose sx={{ position: 'relative', top: 0, right: 0 }} />
                    </div>
                    <Divider />

                    <div className="py-4 space-y-4">
                        <div>
                            <Typography level="body-sm" sx={{ mb: 1 }}>
                                Requirements (optional)
                            </Typography>
                            <Textarea
                                placeholder="E.g., Generate a shop interface with product browsing and order management..."
                                value={requirements}
                                onChange={(e) => setRequirements(e.target.value)}
                                minRows={3}
                            />
                        </div>

                        <div>
                            <Typography level="body-sm" sx={{ mb: 1 }}>
                                Model
                            </Typography>
                            <Select value={model} onChange={(_, v) => v && setModel(v)}>
                                <Option value="llama-3.3-70b-versatile">Llama 3.3 70B (Groq)</Option>
                                <Option value="gpt-4o">GPT-4o (OpenAI)</Option>
                            </Select>
                        </div>

                        {error && (
                            <div className="text-red-500 text-sm flex items-center gap-1">
                                <AlertCircle size={16} />
                                {error}
                            </div>
                        )}
                    </div>

                    <Divider />
                    <div className="flex justify-end gap-2 pt-2">
                        <Button
                            variant="outlined"
                            color="neutral"
                            onClick={() => setShowGenerateModal(false)}
                        >
                            Cancel
                        </Button>
                        <Button
                            variant="solid"
                            color="primary"
                            onClick={handleGenerate}
                            loading={isGenerating}
                            startDecorator={<Sparkles size={16} />}
                        >
                            Generate Candidates
                        </Button>
                    </div>
                </ModalDialog>
            </Modal>

            {/* Candidates Selection Modal */}
            <Modal open={showCandidatesModal} onClose={() => setShowCandidatesModal(false)}>
                <ModalDialog sx={{ width: '90vw', maxWidth: 1200, maxHeight: '90vh', overflow: 'auto' }}>
                    <div className="flex justify-between items-center pb-2">
                        <Typography level="h4">Select UI Candidate</Typography>
                        <ModalClose sx={{ position: 'relative', top: 0, right: 0 }} />
                    </div>
                    <Divider />

                    <div className="py-4 grid grid-cols-3 gap-4">
                        {candidates.map((c) => (
                            <Card
                                key={c.candidate_index}
                                variant={selectedCandidate === c.candidate_index ? 'solid' : 'outlined'}
                                color={selectedCandidate === c.candidate_index ? 'primary' : 'neutral'}
                                sx={{ cursor: 'pointer', overflow: 'hidden' }}
                                onClick={() => setSelectedCandidate(c.candidate_index)}
                            >
                                <div className="text-center">
                                    <div className="flex justify-between items-center">
                                        <Typography level="title-lg">{c.style_name}</Typography>
                                        {c.html_preview && (
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    setExpandedPreview(expandedPreview === c.candidate_index ? null : c.candidate_index);
                                                }}
                                                className="p-1 hover:bg-gray-200 rounded"
                                                title="Expand preview"
                                            >
                                                {expandedPreview === c.candidate_index ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
                                            </button>
                                        )}
                                    </div>
                                    <div className="mt-2 flex justify-center gap-2">
                                        <Chip size="sm" variant="soft">
                                            {c.num_pages} pages
                                        </Chip>
                                        <Chip size="sm" variant="soft">
                                            {c.num_sections} sections
                                        </Chip>
                                        {c.styling?.selectedStyle && (
                                            <Chip size="sm" variant="soft" color="primary">
                                                {c.styling.selectedStyle}
                                            </Chip>
                                        )}
                                    </div>
                                    
                                    {/* HTML Preview in iframe */}
                                    {c.html_preview && (
                                        <div className="mt-3 border rounded overflow-hidden" style={{ height: expandedPreview === c.candidate_index ? 400 : 200 }}>
                                            <iframe
                                                srcDoc={c.html_preview}
                                                style={{ 
                                                    width: '200%', 
                                                    height: expandedPreview === c.candidate_index ? '800px' : '400px',
                                                    border: 'none',
                                                    transform: 'scale(0.5)',
                                                    transformOrigin: 'top left',
                                                }}
                                                title={`Preview ${c.style_name}`}
                                                sandbox="allow-same-origin"
                                            />
                                        </div>
                                    )}
                                    
                                    {/* Color swatches fallback */}
                                    {!c.html_preview && (
                                        <div className="mt-3 flex justify-center gap-1">
                                            <div
                                                className="w-6 h-6 rounded border"
                                                style={{ backgroundColor: c.styling?.backgroundColor || '#fff' }}
                                                title="Background"
                                            />
                                            <div
                                                className="w-6 h-6 rounded border"
                                                style={{ backgroundColor: c.styling?.accentColor || '#ccc' }}
                                                title="Accent"
                                            />
                                            <div
                                                className="w-6 h-6 rounded border"
                                                style={{ backgroundColor: c.styling?.textColor || '#000' }}
                                                title="Text"
                                            />
                                        </div>
                                    )}
                                </div>
                            </Card>
                        ))}
                    </div>

                    {error && (
                        <div className="text-red-500 text-sm flex items-center gap-1">
                            <AlertCircle size={16} />
                            {error}
                        </div>
                    )}

                    <Divider />
                    <div className="flex justify-end gap-2 pt-2">
                        <Button
                            variant="outlined"
                            color="neutral"
                            onClick={() => setShowCandidatesModal(false)}
                        >
                            Cancel
                        </Button>
                        <Button
                            variant="solid"
                            color="primary"
                            onClick={handleSelectCandidate}
                            loading={isSelecting}
                            disabled={selectedCandidate === null}
                            startDecorator={<Check size={16} />}
                        >
                            Apply Selected
                        </Button>
                    </div>
                </ModalDialog>
            </Modal>

            {/* Refine Modal */}
            <Modal open={showRefineModal} onClose={() => setShowRefineModal(false)}>
                <ModalDialog sx={{ width: 500 }}>
                    <div className="flex justify-between items-center pb-2">
                        <Typography level="h4">
                            <RefreshCw className="inline mr-2" size={20} />
                            Refine Interface
                        </Typography>
                        <ModalClose sx={{ position: 'relative', top: 0, right: 0 }} />
                    </div>
                    <Divider />

                    <div className="py-4 space-y-4">
                        {refinementStatus && (
                            <div className="flex items-center gap-2">
                                <Chip
                                    color={refinementStatus.can_refine ? 'success' : 'danger'}
                                    variant="soft"
                                >
                                    {refinementStatus.refinements_remaining} refinements remaining
                                </Chip>
                                {!refinementStatus.can_refine && (
                                    <Typography level="body-sm" color="danger">
                                        Maximum reached. Edit code manually.
                                    </Typography>
                                )}
                            </div>
                        )}

                        <div>
                            <Typography level="body-sm" sx={{ mb: 1 }}>
                                What would you like to change?
                            </Typography>
                            <Textarea
                                placeholder="E.g., Change the navigation bar to blue, put order details on the right side, use dark theme..."
                                value={refinementPrompt}
                                onChange={(e) => setRefinementPrompt(e.target.value)}
                                minRows={3}
                                disabled={refinementStatus?.can_refine === false}
                            />
                        </div>

                        <div>
                            <Typography level="body-sm" sx={{ mb: 1 }}>
                                Model
                            </Typography>
                            <Select
                                value={model}
                                onChange={(_, v) => v && setModel(v)}
                                disabled={refinementStatus?.can_refine === false}
                            >
                                <Option value="llama-3.3-70b-versatile">Llama 3.3 70B (Groq)</Option>
                                <Option value="gpt-4o">GPT-4o (OpenAI)</Option>
                            </Select>
                        </div>

                        {error && (
                            <div className="text-red-500 text-sm flex items-center gap-1">
                                <AlertCircle size={16} />
                                {error}
                            </div>
                        )}
                    </div>

                    <Divider />
                    <div className="flex justify-end gap-2 pt-2">
                        <Button
                            variant="outlined"
                            color="neutral"
                            onClick={() => setShowRefineModal(false)}
                        >
                            Cancel
                        </Button>
                        <Button
                            variant="solid"
                            color="warning"
                            onClick={handleRefine}
                            loading={isRefining}
                            disabled={!refinementPrompt.trim() || refinementStatus?.can_refine === false}
                            startDecorator={<RefreshCw size={16} />}
                        >
                            Refine
                        </Button>
                    </div>
                </ModalDialog>
            </Modal>
        </>
    );
};

export default AIGeneration;
