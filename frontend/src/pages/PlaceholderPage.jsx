import React from 'react';
import { Construction } from 'lucide-react';

export default function PlaceholderPage({ title, moduleCode }) {
  return (
    <div className="p-6 flex-1 flex flex-col items-center justify-center text-center">
      <div className="bg-gray-800/60 p-4 rounded-2xl text-sky-400 mb-4 border border-gray-700/50">
        <Construction size={36} />
      </div>
      <h2 className="text-lg font-bold text-white mb-1">{title} Module Placeholder</h2>
      <p className="text-xs text-gray-400 max-w-sm">
        This section is scheduled for implementation in <strong>{moduleCode}</strong> phase per project specifications.
      </p>
    </div>
  );
}
