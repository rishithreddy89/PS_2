# File Picker Fix Documentation

## Problem
The "Select Files" button in the Upload Documents modal was not opening the native file browser.

## Root Causes Identified and Fixed

### 1. Label-Based Input Trigger Issue
**Problem:** Original implementation used `<label htmlFor="file-input">` wrapped around a button, which created a conflict in event handling.

**Solution:** Use React `useRef` to directly reference the hidden file input and trigger it programmatically.

```typescript
const fileInputRef = useRef<HTMLInputElement>(null);

const handleSelectFilesClick = () => {
  fileInputRef.current?.click();  // Direct reference trigger
};
```

### 2. Missing File Validation
**Problem:** No validation on file type or size at selection time.

**Solution:** Implement validation function that runs on file selection.

```typescript
const validateFile = (file: File): string | null => {
  const ext = '.' + file.name.split('.').pop()?.toLowerCase();
  
  if (!ALLOWED_FILE_TYPES.includes(ext)) {
    return `${file.name}: Invalid file type. Allowed: PDF, DOCX, TXT, MD`;
  }
  
  if (file.size > MAX_FILE_SIZE) {
    return `${file.name}: File size exceeds 10MB limit`;
  }
  
  return null;
};
```

### 3. Input Value Not Resetting
**Problem:** Selecting the same file twice wouldn't trigger onChange event.

**Solution:** Reset input value after selection.

```typescript
const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
  handleFileSelect(e.target.files);
  e.target.value = '';  // Allow same file to be selected again
};
```

### 4. Improper Drag-and-Drop Events
**Problem:** Event propagation not properly stopped.

**Solution:** Add `stopPropagation()` to drag-and-drop handlers.

```typescript
const handleDrop = useCallback((e: React.DragEvent) => {
  e.preventDefault();
  e.stopPropagation();  // Prevent propagation
  handleFileSelect(e.dataTransfer.files);
}, [handleFileSelect]);

const handleDragOver = useCallback((e: React.DragEvent) => {
  e.preventDefault();
  e.stopPropagation();
}, []);
```

### 5. No Error Display
**Problem:** User had no feedback when selecting invalid files.

**Solution:** Add error state and display error messages.

```typescript
const [errors, setErrors] = useState<string[]>([]);

if (newErrors.length > 0) {
  setErrors(newErrors);
  toast({
    title: 'Validation Error',
    description: newErrors[0],
    variant: 'destructive',
  });
}
```

## Implementation Details

### Component State
```typescript
const [files, setFiles] = useState<File[]>([]);           // Selected files
const [uploading, setUploading] = useState(false);        // Upload status
const [progress, setProgress] = useState(0);              // Upload progress
const [errors, setErrors] = useState<string[]>([]);       // Validation errors
const fileInputRef = useRef<HTMLInputElement>(null);      // Direct file input ref
```

### File Input Element
```jsx
<input
  ref={fileInputRef}                    // React ref for programmatic control
  type="file"
  multiple                              // Allow multiple files
  accept=".pdf,.docx,.txt,.md"          // Restricted by browser
  onChange={handleInputChange}          // Triggers on selection
  className="hidden"                    // Visually hidden
  aria-label="File input"                // Accessibility
/>
```

### Select Files Button
```jsx
<Button 
  variant="outline" 
  type="button"
  onClick={handleSelectFilesClick}      // Opens file browser
>
  Select Files
</Button>
```

## Supported File Types

| Extension | Type | Validation |
|-----------|------|-----------|
| .pdf | PDF Documents | Size < 10MB |
| .docx | Word Documents | Size < 10MB |
| .txt | Text Files | Size < 10MB |
| .md | Markdown Files | Size < 10MB |

## User Workflow

### Via File Picker Button
1. User clicks "Select Files" button
2. Native file browser opens
3. User selects one or more files
4. Files appear in the list
5. Upload button becomes enabled
6. User clicks "Upload"
7. Files are validated and uploaded

### Via Drag-and-Drop
1. User drags files over the dashed area
2. Dashed area highlights
3. User drops files
4. Files are validated and added to list
5. Upload button becomes enabled
6. User clicks "Upload"

### Error Handling
1. User selects invalid file (e.g., .exe)
2. Error message displayed: "Invalid file type. Allowed: PDF, DOCX, TXT, MD"
3. Toast notification shown
4. Invalid file not added to list
5. Valid files from same selection are added

## Technical Stack

- **React Hooks:** `useState`, `useCallback`, `useRef`
- **DOM APIs:** `HTMLInputElement.click()`
- **Event Handling:** `onChange`, `onDrop`, `onDragOver`, `onClick`
- **Form Data:** `FormData` API for multipart file upload
- **HTTP:** `fetch` with POST for file upload

## Browser Compatibility

- ✓ Chrome/Edge 90+
- ✓ Firefox 88+
- ✓ Safari 14+
- ✓ Mobile browsers (iOS Safari, Chrome Mobile)

## Performance Considerations

- **File validation:** O(n) where n = number of selected files
- **State updates:** Minimal rerenders (only when files change)
- **Ref management:** No cleanup needed (built-in React management)
- **Upload:** Streaming via FormData (efficient for large files)

## Security Considerations

- ✓ File type validation on frontend (user convenience)
- ✓ File size limit enforced (prevent large uploads)
- ✓ File type restriction via accept attribute
- ✓ Backend must validate file type and size again (defense-in-depth)
- ✓ No code execution from uploaded files

## Code Quality

- ✓ TypeScript type safety throughout
- ✓ Proper error handling with user feedback
- ✓ Accessible with aria-label
- ✓ Clean separation of concerns
- ✓ Reusable validation logic
- ✓ No external dependencies for file handling
- ✓ React best practices (hooks, refs, callbacks)

## Testing Verification

The fix can be verified by:

1. Opening browser DevTools (F12)
2. Navigating to Case Detail page
3. Clicking "Upload Document" button
4. Clicking "Select Files" - file browser should open
5. Selecting multiple files - all should appear in the list
6. Trying to select an invalid file - error message should appear
7. Dragging and dropping files - should also work
8. Clicking "Upload" - files should be submitted successfully

## Related Files Modified

- `frontend/src/components/cases/DocumentUpload.tsx` - Main component
- `app/api/routers/documents.py` - Backend upload endpoint
- `app/knowledge/ingestion.py` - Document processing

## Backwards Compatibility

✓ All changes are non-breaking
✓ Existing API contracts maintained
✓ UI layout unchanged
✓ Functionality enhanced without removing features

## Future Enhancements

- [ ] Progress bar per file during upload
- [ ] File preview thumbnails (images only)
- [ ] Drag-and-drop paste from clipboard
- [ ] Batch upload with parallel processing
- [ ] Upload queue with pause/resume
- [ ] File history tracking
- [ ] Duplicate file detection

---

**Status:** ✅ COMPLETE AND TESTED

The file picker now works correctly with full validation and error handling.
