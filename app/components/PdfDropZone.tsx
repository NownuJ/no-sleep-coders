'use client'

import React, { useCallback, useEffect, useState } from 'react'
import { useDropzone } from 'react-dropzone'

export default function PdfDropZone() {

  const [files, setFiles] = useState<File[]>([]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setFiles(prev => {
      const updated = [...prev, ...acceptedFiles]
      setFiles(updated);
      console.log("Files added: ");
      acceptedFiles.forEach(x => console.log(x.name));
      console.log("Current files: ");
      updated.forEach(y => console.log(y.name));
      return updated;
    })
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop,
    multiple: true,
    maxFiles: 20,
    accept: {
      'application/pdf': ['.pdf'] // Optional: Limit to PDFs only
    }
  })

  return (
    <div
      {...getRootProps()}
      className={`
        flex flex-col items-center justify-center w-full h-64 
        border-2 border-dashed rounded-xl cursor-pointer 
        transition-colors duration-200 ease-in-out
        ${isDragActive 
          ? "border-blue-500 bg-blue-50" 
          : "border-gray-300 bg-gray-50 hover:bg-gray-100 hover:border-gray-400"
        }
      `}
    >
      <input {...getInputProps({multiple: true})} />
      
      {/* Upload Icon */}
      <svg 
        className={`w-12 h-12 mb-4 ${isDragActive ? "text-blue-500" : "text-gray-400"}`} 
        fill="none" 
        viewBox="0 0 24 24" 
        stroke="currentColor"
      >
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
      </svg>

      {isDragActive ? (
        <p className="text-blue-600 font-medium">Drop the PDF here ...</p>
      ) : (
        <div className="text-center">
          <p className="text-gray-600 font-medium text-lg">
            Drag & drop your PDF here
          </p>
          <p className="text-gray-400 text-sm mt-1">
            or click to select files
          </p>
        </div>
      )}

      <ul>
        {files.map(file => (
          <li key={file.name}>{file.name}</li>
        ))}
      </ul>
    </div>
  )
}