import { useState } from 'react';
import { Input } from '../ui/Input';
import { Search, X } from 'lucide-react';

interface SearchBarProps {
  onSearch: (query: string) => void;
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
}

export function SearchBar({ onSearch, placeholder = 'Search...', value: externalValue, onChange }: SearchBarProps) {
  const [internalQuery, setInternalQuery] = useState('');
  const query = externalValue !== undefined ? externalValue : internalQuery;
  
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    if (onChange) {
      onChange(newValue);
    } else {
      setInternalQuery(newValue);
      onSearch(newValue);
    }
  };

  const handleClear = () => {
    if (onChange) {
      onChange('');
    } else {
      setInternalQuery('');
      onSearch('');
    }
  };

  return (
    <div className="relative flex items-center">
      <Search className="absolute left-3 h-4 w-4 text-muted-foreground" />
      <Input
        type="text"
        placeholder={placeholder}
        value={query}
        onChange={handleChange}
        className="pl-10 pr-10"
      />
      {query && (
        <button
          onClick={handleClear}
          className="absolute right-3 text-muted-foreground hover:text-foreground"
          type="button"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}
