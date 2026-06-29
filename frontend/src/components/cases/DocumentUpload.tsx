import { useState, useCallback, useRef } from 'react';
import { Upload, X, FileText, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/hooks/use-toast';
import { documentsApi } from '@/services/api';

interface DocumentUploadProps {
  caseId: string;
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const ALLOWED_FILE_TYPES = ['.pdf', '.docx', '.txt'];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export function DocumentUpload({ caseId, open, onClose, onSuccess }: DocumentUploadProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [errors, setErrors] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  const validateFile = (file: File): string | null => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    
    if (!ALLOWED_FILE_TYPES.includes(ext)) {
      return `${file.name}: Invalid file type. Allowed: PDF, DOCX, TXT`;
    }
    
    if (file.size > MAX_FILE_SIZE) {
      return `${file.name}: File size exceeds 10MB limit`;
    }
    
    return null;
  };

  const handleFileSelect = useCallback((selectedFiles: FileList | null) => {
    if (!selectedFiles) return;
    
    const newFiles: File[] = [];
    const newErrors: string[] = [];
    
    Array.from(selectedFiles).forEach(file => {
      const error = validateFile(file);
      if (error) {
        newErrors.push(error);
      } else {
        newFiles.push(file);
      }
    });
    
    if (newErrors.length > 0) {
      setErrors(newErrors);
      toast({
        title: 'Validation Error',
        description: newErrors[0],
        variant: 'destructive',
      });
    }
    
    if (newFiles.length > 0) {
      setFiles(prev => [...prev, ...newFiles]);
      setErrors([]);
    }
  }, [toast]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleFileSelect(e.target.files);
    e.target.value = '';
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    handleFileSelect(e.dataTransfer.files);
  }, [handleFileSelect]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const uploadFiles = async () => {
    if (files.length === 0) return;

    setUploading(true);
    setProgress(0);

    const formData = new FormData();
    files.forEach(file => formData.append('files', file));

    try {
      const response = await documentsApi.upload(caseId, formData, (pct) => {
        setProgress(pct);
      });

      const result = response.data;
      
      // Log processing status
      result.documents?.forEach((doc: any) => {
        if (doc.status === 'failed') {
          console.error(`Document ${doc.filename} failed:`, doc);
        }
      });
      
      toast({
        title: 'Upload complete',
        description: `Uploaded ${result.count} document(s). Processing...`,
        variant: 'success',
      });

      setFiles([]);
      setErrors([]);
      onSuccess();
      onClose();
    } catch {
      // Error handled by API interceptor
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  const handleSelectFilesClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Upload Documents</DialogTitle>
        </DialogHeader>

        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          className="border-2 border-dashed rounded-lg p-8 text-center hover:border-primary transition-colors"
        >
          <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
          <p className="text-sm text-muted-foreground mb-2">
            Drag and drop files here, or click to select
          </p>
          <p className="text-xs text-muted-foreground mb-4">
            Supported: PDF, DOCX, TXT (max 10MB)
          </p>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.docx,.txt"
            onChange={handleInputChange}
            className="hidden"
            aria-label="File input"
          />
          <Button 
            variant="outline" 
            type="button"
            onClick={handleSelectFilesClick}
          >
            Select Files
          </Button>
        </div>

        {errors.length > 0 && (
          <div className="bg-destructive/10 border border-destructive/20 rounded p-3">
            {errors.map((error, idx) => (
              <p key={idx} className="text-sm text-destructive">{error}</p>
            ))}
          </div>
        )}

        {files.length > 0 && (
          <div className="space-y-2 max-h-60 overflow-auto">
            <p className="text-sm font-medium">Selected Files ({files.length})</p>
            {files.map((file, index) => (
              <div key={index} className="flex items-center justify-between p-2 bg-muted rounded">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  <span className="text-sm">{file.name}</span>
                  <span className="text-xs text-muted-foreground">
                    ({(file.size / 1024).toFixed(1)} KB)
                  </span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeFile(index)}
                  disabled={uploading}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        )}

        {uploading && (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">Uploading... {progress}%</span>
            </div>
            <Progress value={progress} />
          </div>
        )}

        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onClose} disabled={uploading}>
            Cancel
          </Button>
          <Button onClick={uploadFiles} disabled={files.length === 0 || uploading}>
            {uploading ? 'Uploading...' : `Upload ${files.length} file(s)`}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
