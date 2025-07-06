import React from 'react';
import { ArrowUp, ArrowDown, TrendingUp, Star, Clock, ArrowUpDown } from 'lucide-react';

// Re-defining SortOption and ColumnSort as they are specific to this component's props
type SortOption = 'score' | 'stars' | 'created' | 'name';
type SortDirection = 'asc' | 'desc';

interface ColumnSort {
  field: SortOption;
  direction: SortDirection;
}

interface SortControlsProps {
  sort: ColumnSort;
  onSortChange: (sort: ColumnSort) => void;
  title: string;
  itemCount: number;
}

export const SortControls: React.FC<SortControlsProps> = ({ sort, onSortChange, title, itemCount }) => {
  const sortOptions: { field: SortOption; label: string; icon: React.ReactNode }[] = [
    { field: 'score', label: '评分', icon: <TrendingUp className="w-4 h-4" /> },
    { field: 'stars', label: 'Stars', icon: <Star className="w-4 h-4" /> },
    { field: 'created', label: '时间', icon: <Clock className="w-4 h-4" /> },
    { field: 'name', label: '名称', icon: <ArrowUpDown className="w-4 h-4" /> },
  ];

  return (
    <div className="column-title-area">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900">
          {title}
        </h2>
        <div className="text-sm text-gray-500">
          {itemCount} 个项目
        </div>
      </div>
      
      <div className="flex flex-wrap gap-2">
        {sortOptions.map((option) => (
          <button
            key={option.field}
            onClick={() => onSortChange({ 
              field: option.field, 
              direction: sort.field === option.field && sort.direction === 'desc' ? 'asc' : 'desc'
            })}
            className={`button-clean text-sm flex items-center gap-2 ${
              sort.field === option.field ? 'active' : ''
            }`}
          >
            {option.icon}
            {option.label}
            {sort.field === option.field && (
              sort.direction === 'desc' ? 
              <ArrowDown className="w-3 h-3" /> : 
              <ArrowUp className="w-3 h-3" />
            )}
          </button>
        ))}
      </div>
    </div>
  );
}; 