import { useAppStore } from '@/store/appStore';
import { Moon, Sun } from 'lucide-react';
import { Button } from '../ui/Button';

export function DarkModeToggle() {
  const { isDarkMode, toggleDarkMode } = useAppStore();

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggleDarkMode}
      title={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {isDarkMode ? (
        <Sun className="h-5 w-5" />
      ) : (
        <Moon className="h-5 w-5" />
      )}
    </Button>
  );
}
