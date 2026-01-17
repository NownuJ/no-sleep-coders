'use client'

interface TopBarProps {
    handleOnClick: (name:string) => void
}

export default function TopBar({handleOnClick}: TopBarProps) {
    return (
        <nav className="w-full flex items-center justify-center gap-8 px-6 py-4 bg-white border-b border-gray-200 shadow-sm sticky top-0 z-50">
            <p 
                onClick={() => handleOnClick("CheatSheet")}
                className="text-gray-600 font-medium hover:text-blue-600 cursor-pointer transition-colors duration-200"
            >
                CheatSheet Generator
            </p>
            
            <div className="h-4 w-px bg-gray-300 hidden sm:block"></div> {/* Optional divider */}

            <p 
                onClick={() => handleOnClick("Notes")}
                className="text-gray-600 font-medium hover:text-blue-600 cursor-pointer transition-colors duration-200"
            >
                Notes Summariser
            </p>
        </nav>
    )
}