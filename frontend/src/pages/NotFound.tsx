import { Link } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { AlertCircle } from 'lucide-react';

export function NotFound() {
  return (
    <div className="flex items-center justify-center h-[calc(100vh-8rem)]">
      <div className="text-center space-y-4">
        <AlertCircle className="h-16 w-16 text-muted-foreground mx-auto" />
        <h1 className="text-4xl font-bold">404</h1>
        <p className="text-lg text-muted-foreground">Page not found</p>
        <Link to="/dashboard">
          <Button>Go to Dashboard</Button>
        </Link>
      </div>
    </div>
  );
}
