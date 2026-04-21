import { Loader2, CheckCircle2, XCircle } from 'lucide-react';
import { Progress } from '@/components/ui/progress';
import type { JobStatus } from '@/hooks/useJobPolling';

interface JobProgressBarProps {
  status: JobStatus | null;
  isPolling: boolean;
}

export function JobProgressBar({ status, isPolling }: JobProgressBarProps) {
  if (!status && !isPolling) {
    return null;
  }

  const getStatusIcon = () => {
    if (!status) return <Loader2 className="w-4 h-4 animate-spin text-blue-500" />;

    switch (status.status) {
      case 'pending':
        return <Loader2 className="w-4 h-4 animate-spin text-gray-400" />;
      case 'running':
        return <Loader2 className="w-4 h-4 animate-spin text-blue-500" />;
      case 'completed':
        return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return null;
    }
  };

  const getStatusText = () => {
    if (!status) return 'Инициализация...';

    switch (status.status) {
      case 'pending':
        return 'Ожидание запуска...';
      case 'running':
        if (status.total > 0) {
          const currentItem = status.current_item ? ` (${status.current_item})` : '';
          return `Обработка ${status.processed} из ${status.total}${currentItem}`;
        }
        return 'Выполнение...';
      case 'completed':
        return `Завершено! Обработано ${status.processed} из ${status.total}`;
      case 'failed':
        return `Ошибка: ${status.error || 'Неизвестная ошибка'}`;
      default:
        return '';
    }
  };

  const getProgressValue = () => {
    if (!status) return 0;
    return status.progress;
  };

  const getProgressColor = () => {
    if (!status) return '';

    switch (status.status) {
      case 'completed':
        return 'bg-green-500';
      case 'failed':
        return 'bg-red-500';
      case 'running':
        return 'bg-blue-500';
      default:
        return 'bg-gray-400';
    }
  };

  return (
    <div className="w-full space-y-2 p-4 bg-white border border-gray-200 rounded-lg shadow-sm">
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2">
          {getStatusIcon()}
          <span className="font-medium text-gray-700">{getStatusText()}</span>
        </div>
        <span className="text-gray-500">{getProgressValue()}%</span>
      </div>

      <Progress
        value={getProgressValue()}
        className="h-2"
        // @ts-ignore - custom indicator color
        indicatorClassName={getProgressColor()}
      />

      {status?.status === 'running' && status.total > 0 && (
        <div className="text-xs text-gray-500 text-right">
          {status.processed} / {status.total} записей
        </div>
      )}
    </div>
  );
}
