import React, { useRef, useState } from "react";
import { Upload, X } from "lucide-react";

type FileUploadProps = {
  accept?: string;
  disabled?: boolean;
  file?: File | null;
  onFileChange?: (file: File | null) => void;
  label?: string;
};

const ProjectFileUpload: React.FC<FileUploadProps> = ({
  accept,
  disabled = false,
  file = null,
  onFileChange,
  label = "Upload file",
}) => {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const acceptedTypes = (accept ?? "")
    .split(",")
    .map((type) => type.trim().toLowerCase())
    .filter(Boolean);

  const isValidFile = (nextFile: File) => {
    if (acceptedTypes.length === 0) {
      return true;
    }

    const fileName = nextFile.name.toLowerCase();
    const mimeType = nextFile.type.toLowerCase();

    return acceptedTypes.some((type) => {
      if (type.startsWith(".")) {
        return fileName.endsWith(type);
      }

      if (type.endsWith("/*")) {
        const baseType = type.slice(0, -2);
        return mimeType.startsWith(`${baseType}/`);
      }

      return mimeType === type;
    });
  };

  const handleOpen = () => {
    if (!disabled) {
      inputRef.current?.click();
    }
  };

  const handleSelectFile = (nextFile: File | null) => {
    if (!nextFile) {
      return;
    }

    if (!isValidFile(nextFile)) {
      setError(`Only supported file types are allowed: ${accept}`);
      return;
    }

    setError(null);
    onFileChange?.(nextFile);
  };

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const nextFile = event.target.files?.[0] ?? null;
    handleSelectFile(nextFile);
    event.target.value = "";
  };

  const handleRemove = () => {
    setError(null);
    onFileChange?.(null);
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    if (!disabled) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);

    if (disabled) {
      return;
    }

    const nextFile = event.dataTransfer.files?.[0] ?? null;
    handleSelectFile(nextFile);
  };

  return (
    <div className="flex w-full flex-col gap-3">
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        disabled={disabled}
        onChange={handleChange}
        className="hidden"
      />

      <div
        onClick={handleOpen}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`flex w-full cursor-pointer flex-col items-center justify-center gap-2 rounded-md border border-dashed p-6 ${
          isDragging
            ? "border-stone-500 bg-stone-100"
            : "border-stone-300 bg-stone-50"
        } ${disabled ? "cursor-not-allowed opacity-50" : "hover:bg-stone-100"}`}
      >
        <Upload size={20} />
        <span className="text-sm font-medium">{label}</span>
        <span className="text-xs text-stone-500">
          Drag and drop a file or click to browse
        </span>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {file && (
        <div className="flex items-center justify-between rounded-md bg-stone-100 px-3 py-2">
          <div className="min-w-0">
            <p className="truncate text-sm font-medium">{file.name}</p>
            <p className="text-xs text-stone-500">
              {(file.size / 1024).toFixed(1)} KB
            </p>
          </div>

          <button
            type="button"
            onClick={handleRemove}
            className="rounded-md p-1 hover:bg-stone-200"
          >
            <X size={16} />
          </button>
        </div>
      )}
    </div>
  );
};

export default ProjectFileUpload;