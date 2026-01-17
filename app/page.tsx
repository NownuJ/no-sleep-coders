'use client'

import CheatSheetGenerator from './components/CheatSheetGenerator';
import { useState } from 'react'
import TopBar from './components/TopBar'
import NotesSummariser from './components/NotesSummariser';

export default function Home() {

  const [currentPage, setCurrentPage] = useState<string>("CheatSheet");

  return (
    <div className="min-h-screen bg-gray-50 text-slate-900">
      <TopBar
        handleOnClick={setCurrentPage}
      />
      {(currentPage == "CheatSheet") ? <CheatSheetGenerator/> : <NotesSummariser/>}
    </div>
  )
}