'use client'

import { useState } from "react";
import PdfDropZone from "./PdfDropZone"

export default function CheatSheetGenerator() {

    const [files, setFiles] = useState<File[]>([]);
    
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
                <PdfDropZone onFileChange={setFiles}/>
            </div>
            <ul>
                {files.map(file => (
                    <li key={file.name}>{file.name}</li>
                ))}
            </ul>
        </div>
    ) 
}