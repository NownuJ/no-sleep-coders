'use client'

import { useState } from "react";
import PdfDropZone from "./PdfDropZone"

interface GeneratedResult {
    jobId: string;
    preview: any;
}

export default function CheatSheetGenerator() {

    const [files, setFiles] = useState<File[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [progress, setProgress] = useState('');
    const [result, setResult] = useState<GeneratedResult | null>(null);

    async function handleOnGenerate() {
        if (files.length === 0) return;
        
        setIsLoading(true);
        setResult(null); // Clear previous results
        
        try {
            // Step 1: Parse
            setProgress('Uploading and parsing PDFs...');
            const formData = new FormData();
            files.forEach(file => {
                formData.append('files', file);
            });
            formData.append('doc_type', 'cheatsheet');

            const parseResponse = await fetch('http://localhost:8000/parse', {
                method: 'POST',
                body: formData,
            });

            if (!parseResponse.ok) {
                const error = await parseResponse.json();
                throw new Error(error.detail || 'Failed to parse PDFs');
            }

            const parseData = await parseResponse.json();
            const jobId = parseData.job_id;

            // Step 2: Generate
            setProgress('Generating cheatsheet with AI... (this may take a minute)');
            const generateFormData = new FormData();
            generateFormData.append('job_id', jobId);

            const generateResponse = await fetch('http://localhost:8000/generate', {
                method: 'POST',
                body: generateFormData,
            });

            if (!generateResponse.ok) {
                const error = await generateResponse.json();
                throw new Error(error.detail || 'Failed to generate cheatsheet');
            }

            const generateData = await generateResponse.json();
            
            setProgress('');
            setIsLoading(false);
            
            // Store result for download buttons
            setResult({
                jobId: jobId,
                preview: generateData.preview
            });

        } catch (error) {
            console.error('Error:', error);
            setProgress('');
            setIsLoading(false);
            alert(error instanceof Error ? error.message : 'Failed to generate cheatsheet');
        }
    }

    function handleDownload(format: 'markdown' | 'json' | 'pdf') {
        if (!result) return;
        window.open(`http://localhost:8000/download/${result.jobId}?format=${format}`, '_blank');
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

                {/* File List */}
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

            {/* Generate Button */}
            <button 
                onClick={handleOnGenerate}
                disabled={files.length === 0 || isLoading}
                className={`
                    w-full mt-6 py-4 px-6 rounded-xl font-bold text-white text-lg shadow-lg
                    transition-all duration-200 transform
                    ${files.length === 0 || isLoading
                        ? 'bg-gray-300 cursor-not-allowed opacity-70' 
                        : 'bg-indigo-600 hover:bg-indigo-700 hover:shadow-xl active:scale-[0.99] hover:-translate-y-0.5'
                    }
                `}
            >
                {isLoading ? (
                    <span className="flex items-center justify-center gap-2">
                        <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        {progress || 'Processing...'}
                    </span>
                ) : 'Generate CheatSheet'}
            </button>

            {/* Success Result */}
            {result && (
                <div className="mt-8 bg-green-50 border border-green-200 rounded-2xl p-6 animate-in fade-in slide-in-from-bottom-4 duration-300">
                    <div className="flex items-center gap-2 mb-4">
                        <svg className="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <h3 className="text-xl font-bold text-green-800">Cheatsheet Generated Successfully!</h3>
                    </div>
                    
                    <p className="text-green-700 mb-4">
                        Generated {result.preview.sections_generated} sections from {result.preview.pages_processed} pages
                    </p>

                    <div className="flex flex-wrap gap-3">
                        <button
                            onClick={() => handleDownload('markdown')}
                            className="flex-1 min-w-[140px] py-3 px-4 bg-white border-2 border-green-600 text-green-700 rounded-lg font-semibold hover:bg-green-600 hover:text-white transition-colors duration-200"
                        >
                            📄 Download Markdown
                        </button>
                        
                        <button
                            onClick={() => handleDownload('pdf')}
                            className="flex-1 min-w-[140px] py-3 px-4 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 transition-colors duration-200"
                        >
                            📑 Download PDF
                        </button>
                        
                        <button
                            onClick={() => handleDownload('json')}
                            className="flex-1 min-w-[140px] py-3 px-4 bg-white border-2 border-green-600 text-green-700 rounded-lg font-semibold hover:bg-green-600 hover:text-white transition-colors duration-200"
                        >
                            🔧 Download JSON
                        </button>
                    </div>

                    {/* Preview Section */}
                    <details className="mt-4">
                        <summary className="cursor-pointer text-green-700 font-semibold hover:text-green-800">
                            📋 Preview Content
                        </summary>
                        <div className="mt-3 p-4 bg-white rounded-lg border border-green-200 max-h-96 overflow-y-auto">
                            <pre className="text-xs text-gray-700 whitespace-pre-wrap">
                                {JSON.stringify(result.preview, null, 2)}
                            </pre>
                        </div>
                    </details>
                </div>
            )}
        </div>
    ) 
}