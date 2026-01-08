import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/Card';
import { Badge } from '../ui/Badge';
import type { Drug } from '@/types';
import { Calendar, Building2, CheckCircle2, XCircle } from 'lucide-react';

interface DrugCardProps {
  drug: Drug;
  onClick?: () => void;
  isSelected?: boolean;
}

export function DrugCard({ drug, onClick, isSelected }: DrugCardProps) {
  return (
    <Card
      className={`cursor-pointer transition-all hover:shadow-md ${
        isSelected ? 'ring-2 ring-primary' : ''
      }`}
      onClick={onClick}
    >
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg">{drug.name}</CardTitle>
            <CardDescription className="mt-1">
              <span className="flex items-center gap-1 text-xs">
                <Building2 className="h-3 w-3" />
                {drug.manufacturer || 'Unknown Manufacturer'}
              </span>
            </CardDescription>
          </div>
          {drug.version_check_enabled ? (
            <Badge variant="success" className="flex items-center gap-1">
              <CheckCircle2 className="h-3 w-3" />
              Monitored
            </Badge>
          ) : (
            <Badge variant="secondary" className="flex items-center gap-1">
              <XCircle className="h-3 w-3" />
              Not Monitored
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2 text-sm text-muted-foreground">
          <div className="flex items-center justify-between">
            <span>Version:</span>
            <span className="font-mono font-semibold">{drug.version}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              Last Updated:
            </span>
            <span className="font-medium">
              {new Date(drug.last_updated).toLocaleDateString()}
            </span>
          </div>
          {drug.last_version_check && (
            <div className="flex items-center justify-between text-xs">
              <span>Last Check:</span>
              <span>
                {new Date(drug.last_version_check).toLocaleDateString()}
              </span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
