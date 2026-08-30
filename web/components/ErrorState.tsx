import { AlertTriangle } from "lucide-react";

export default function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
      <AlertTriangle className="mx-auto text-red-500" size={24} />
      <div className="text-sm font-medium text-red-700 mt-2">Couldn't load data</div>
      <div className="text-xs text-red-500 mt-1 break-words">{message}</div>
      {onRetry && (
        <button onClick={onRetry} className="mt-3 text-xs font-medium text-red-700 underline">
          Try again
        </button>
      )}
    </div>
  );
}
