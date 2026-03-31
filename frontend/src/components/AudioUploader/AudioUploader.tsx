/**
 * AudioUploader component: File upload interface.
 * Supports drag-and-drop and file picker, validates format and size before uploading to backend.
 */

import { useState, useRef, useCallback } from 'react'
import type { AnalyzeResponse } from '../../types'
import { uploadAudio } from '../../services/api'

interface AudioUploaderProps {
  onUploadComplete: (result: AnalyzeResponse) => void
  onError: (message: string) => void
  isProcessing?: boolean
}

const ACCEPTED_TYPES = ['audio/mpeg', 'audio/wav', 'audio/x-wav', 'audio/mp4', 'audio/m4a', 'audio/ogg']
const ACCEPTED_EXTS = ['.mp3', '.wav', '.m4a', '.ogg']
const MAX_SIZE = 10 * 1024 * 1024 // 10 MB

export default function AudioUploader({
  onUploadComplete,
  onError,
  isProcessing = false,
}: AudioUploaderProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [fileName, setFileName] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const validateAndUpload = useCallback(
    async (file: File) => {
      // Validate extension
      const ext = '.' + file.name.split('.').pop()?.toLowerCase()
      if (!ACCEPTED_EXTS.includes(ext)) {
        onError(`Unsupported format "${ext}". Please upload MP3, WAV, M4A, or OGG files.`)
        return
      }

      // Validate size
      if (file.size > MAX_SIZE) {
        onError(`File size (${(file.size / 1024 / 1024).toFixed(1)} MB) exceeds the 10 MB limit.`)
        return
      }

      setFileName(file.name)
      setUploading(true)
      try {
        const result = await uploadAudio(file)
        onUploadComplete(result)
      } catch (err) {
        onError(err instanceof Error ? err.message : 'Upload failed. Please try again.')
      } finally {
        setUploading(false)
      }
    },
    [onUploadComplete, onError],
  )

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragging(false)
      const file = e.dataTransfer.files[0]
      if (file) validateAndUpload(file)
    },
    [validateAndUpload],
  )

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (file) validateAndUpload(file)
    },
    [validateAndUpload],
  )

  const processing = isProcessing || uploading

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      style={{
        border: `2px dashed ${isDragging ? 'var(--color-primary)' : 'var(--color-border)'}`,
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--space-8)',
        textAlign: 'center',
        backgroundColor: isDragging ? 'var(--color-surface-dark)' : 'transparent',
        transition: 'all 0.2s',
        cursor: processing ? 'not-allowed' : 'pointer',
        opacity: processing ? 0.6 : 1,
      }}
      onClick={() => !processing && inputRef.current?.click()}
      role="button"
      tabIndex={0}
      aria-label="Upload audio file"
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); inputRef.current?.click() } }}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".mp3,.wav,.m4a,.ogg"
        onChange={handleFileSelect}
        style={{ display: 'none' }}
        disabled={processing}
      />

      {processing ? (
        <div>
          <p style={{ fontSize: 'var(--font-size-lg)', fontWeight: 'var(--font-weight-medium)', marginBottom: 'var(--space-2)' }}>
            {uploading ? 'Uploading & Analyzing...' : 'Processing...'}
          </p>
          {fileName && (
            <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>{fileName}</p>
          )}
        </div>
      ) : (
        <div>
          <p style={{ fontSize: 'var(--font-size-lg)', fontWeight: 'var(--font-weight-medium)', marginBottom: 'var(--space-2)' }}>
            Drop audio file here or click to browse
          </p>
          <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-1)' }}>
            Supported: MP3, WAV, M4A, OGG
          </p>
          <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
            Max file size: 10 MB
          </p>
        </div>
      )}
    </div>
  )
}
