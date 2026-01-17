'use client'

import { useState } from "react";
import PdfDropZone from "./PdfDropZone"

export default function CheatSheetGenerator() {

    const [files, setFiles] = useState<File[]>([]);

    function handleOnGenerate() {
        if (files.length === 0) return;
        // Send PDF information to FastAPI
        console.log("Generating with:", files);
    }

    function handleFileChange(newFiles: File[]) {
        const updated = [...newFiles, ...files]
        setFiles(updated);
    }

    function handleOnDelete(index: number) {
        setFiles(prev => prev.filter((_, i) => i !== index));
    }
    
    return (
        <div className="w-full max-w-3xl mx-auto mt-10 px-6">
            <div className="text-center mb-8">
                <h1 className="text-3xl font-bold text-gray-800 mb-2">
                    Upload Notes
                </h1>
                <p className="text-gray-600">
                    Upload your lecture slides or notes (PDF) to generate a cheat sheet.
                </p>
            </div>
            
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                <PdfDropZone onFileChange={handleFileChange}/>

                {/* Styled List */}
                {files.length > 0 && (
                    <ul className="mt-6 space-y-3">
                        {files.map((file, index) => (
                            <li 
                                key={`${file.name}-${index}`} 
                                className="flex items-center p-3 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-700 animate-in fade-in slide-in-from-top-2 duration-200 group"
                            >
                                {/* File Icon */}
                                <svg className="w-5 h-5 text-indigo-500 mr-3 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                                
                                <span className="truncate font-medium">{file.name}</span>
                                
                                {/* Metadata & Actions Wrapper */}
                                <div className="ml-auto flex items-center gap-3">
                                    <span className="text-xs text-gray-400">
                                        {(file.size / 1024 / 1024).toFixed(2)} MB
                                    </span>

                                    {/* Remove Button */}
                                    <button
                                        onClick={() => {handleOnDelete(index)}}
                                        className="p-1.5 rounded-md text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-red-500/20"
                                        aria-label="Remove file"
                                    >
                                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                        </svg>
                                    </button>
                                </div>
                            </li>
                        ))}
                    </ul>
                )}
            </div>

            {/* Styled Button */}
            <button 
                onClick={handleOnGenerate}
                disabled={files.length === 0}
                className={`
                    w-full mt-6 py-4 px-6 rounded-xl font-bold text-white text-lg shadow-lg
                    transition-all duration-200 transform
                    ${files.length === 0 
                        ? 'bg-gray-300 cursor-not-allowed opacity-70' 
                        : 'bg-indigo-600 hover:bg-indigo-700 hover:shadow-xl active:scale-[0.99] hover:-translate-y-0.5'
                    }
                `}
            >
                Generate CheatSheet
            </button>
        </div>
    ) 
}