import { Lightbulb } from 'lucide-react';

interface SummaryDisplayProps {
  summary: string;
  insights: string[];
  isLoading?: boolean;
}

export function SummaryDisplay({ summary, insights, isLoading }: SummaryDisplayProps) {
  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-4 bg-gray-200 rounded w-3/4"></div>
        <div className="h-4 bg-gray-200 rounded w-full"></div>
        <div className="h-4 bg-gray-200 rounded w-5/6"></div>
        <div className="h-4 bg-gray-200 rounded w-2/3"></div>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="text-center text-gray-500 py-8">
        <p>Select a document to view its summary</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-800 mb-2">Summary</h3>
        <p className="text-gray-600 leading-relaxed">{summary}</p>
      </div>

      {insights.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
            <Lightbulb className="h-5 w-5 text-yellow-500" />
            Key Insights
          </h3>
          <ul className="space-y-2">
            {insights.map((insight, index) => (
              <li
                key={index}
                className="flex items-start gap-2 p-3 bg-yellow-50 rounded-lg border border-yellow-100"
              >
                <span className="flex-shrink-0 w-6 h-6 bg-yellow-200 text-yellow-700 rounded-full flex items-center justify-center text-sm font-medium">
                  {index + 1}
                </span>
                <span className="text-gray-700">{insight}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

