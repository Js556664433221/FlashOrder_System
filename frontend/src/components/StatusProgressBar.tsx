import { CheckCircle, Circle, Clock } from 'lucide-react';

export interface StatusStep {
  value: string;
  label: string;
  color: string;
  bgColor: string;
  borderColor: string;
  activeColor: string;
}

// Main progress steps with Purple accent
export const ORDER_PROGRESS_STEPS: StatusStep[] = [
  { value: 'Pending Payment', label: 'Pending', color: 'text-blue-700', bgColor: 'bg-blue-100', borderColor: 'border-blue-300', activeColor: 'bg-blue-500' },
  { value: 'Payment Under Review', label: 'Review', color: 'text-amber-700', bgColor: 'bg-amber-100', borderColor: 'border-amber-300', activeColor: 'bg-amber-500' },
  { value: 'Paid', label: 'Paid', color: 'text-accent-green-700', bgColor: 'bg-accent-green/10', borderColor: 'border-accent-green/30', activeColor: 'bg-accent-green' },
  { value: 'Preparing', label: 'Preparing', color: 'text-primary-700', bgColor: 'bg-primary-100', borderColor: 'border-primary-300', activeColor: 'bg-primary-600' },
  { value: 'Ready to Ship', label: 'Ready to Ship', color: 'text-indigo-700', bgColor: 'bg-indigo-100', borderColor: 'border-indigo-300', activeColor: 'bg-indigo-500' },
  { value: 'Shipped', label: 'Shipped', color: 'text-cyan-700', bgColor: 'bg-cyan-100', borderColor: 'border-cyan-300', activeColor: 'bg-cyan-500' },
  { value: 'Completed', label: 'Completed', color: 'text-accent-green-700', bgColor: 'bg-accent-green/10', borderColor: 'border-accent-green/30', activeColor: 'bg-accent-green' },
];

const PAYMENT_REJECTED_STEP: StatusStep = {
  value: 'Payment Rejected', label: 'Rejected', color: 'text-accent-red-700', bgColor: 'bg-accent-red/10', borderColor: 'border-accent-red/30', activeColor: 'bg-accent-red'
};

const CANCELLED_STEP: StatusStep = {
  value: 'Cancelled', label: 'Cancelled', color: 'text-dark-600', bgColor: 'bg-dark-200', borderColor: 'border-dark-300', activeColor: 'bg-dark-500'
};

const CANCEL_REQUESTED_STEP: StatusStep = {
  value: 'Cancel Requested', label: 'Cancel Req.', color: 'text-amber-700', bgColor: 'bg-amber-100', borderColor: 'border-amber-300', activeColor: 'bg-amber-500'
};

function getStepIndex(status: string): number {
  const index = ORDER_PROGRESS_STEPS.findIndex(s => s.value === status);
  if (index !== -1) return index;
  if (status === 'Payment Rejected') return -2;
  if (status === 'Cancelled') return -3;
  if (status === 'Cancel Requested') return -4;
  return -1;
}

interface StatusProgressBarProps {
  status: string;
  showLabels?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export function StatusProgressBar({ status, showLabels = true, size = 'md' }: StatusProgressBarProps) {
  const currentIndex = getStepIndex(status);
  const isRejected = status === 'Payment Rejected';
  const isCancelled = status === 'Cancelled';
  const isCancelRequested = status === 'Cancel Requested';

  const circleSizes = {
    sm: 'w-6 h-6',
    md: 'w-8 h-8',
    lg: 'w-10 h-10',
  };

  const lineHeights = {
    sm: 'h-1',
    md: 'h-1.5',
    lg: 'h-2',
  };

  const iconSizes = {
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
  };

  // Handle terminal states
  if (isRejected || isCancelled || isCancelRequested) {
    const terminalStep = isRejected ? PAYMENT_REJECTED_STEP : isCancelled ? CANCELLED_STEP : CANCEL_REQUESTED_STEP;
    return (
      <div className="w-full">
        <div className="flex items-center gap-3">
          <div className={`${circleSizes[size]} rounded-full ${terminalStep.activeColor} flex items-center justify-center flex-shrink-0`}>
            <span className="text-white font-bold text-xs">!</span>
          </div>
          {showLabels && (
            <span className={`font-medium ${terminalStep.color}`}>{terminalStep.label}</span>
          )}
        </div>
      </div>
    );
  }

  // For active steps, show relevant portion of progress
  if (currentIndex >= 0) {
    return (
      <div className="w-full overflow-x-auto">
        <div className="flex items-center min-w-max">
          {ORDER_PROGRESS_STEPS.map((step, idx) => {
            const isCompleted = idx < currentIndex;
            const isCurrent = idx === currentIndex;

            // Only show relevant steps
            let shouldHide = false;
            if (status === 'Ready for Pickup' && (step.value === 'Preparing' || step.value === 'Shipped')) {
              shouldHide = true;
            }

            if (shouldHide) {
              return <div key={step.value} className="hidden" />;
            }

            return (
              <div key={step.value} className="flex items-center">
                <div className="flex flex-col items-center">
                  <div className={`
                    ${circleSizes[size]} rounded-full flex items-center justify-center
                    ${isCompleted ? `${step.activeColor}` : isCurrent ? `${step.activeColor} ring-4 ring-offset-2 ${step.borderColor} animate-pulse` : 'bg-dark-200 border-2 border-dark-300'}
                    transition-all duration-300
                  `}>
                    {isCompleted ? (
                      <CheckCircle className={`${iconSizes[size]} text-white`} />
                    ) : isCurrent ? (
                      <span className="text-white font-bold text-xs">{idx + 1}</span>
                    ) : (
                      <Circle className={`${iconSizes[size]} text-dark-400`} />
                    )}
                  </div>
                  {showLabels && (
                    <span className={`
                      text-xs font-medium mt-1 whitespace-nowrap
                      ${isCompleted ? step.color : isCurrent ? `${step.color} font-bold` : 'text-dark-400'}
                    `}>
                      {step.label}
                    </span>
                  )}
                </div>
                {idx < ORDER_PROGRESS_STEPS.length - 1 && (
                  <div className={`
                    ${lineHeights[size]} w-4 md:w-6 mx-0.5 rounded transition-all duration-300
                    ${isCompleted ? 'bg-accent-green' : isCurrent ? `${step.activeColor}` : 'bg-dark-200'}
                  `} />
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // Fallback for unknown status
  return (
    <div className="w-full flex items-center gap-2">
      <Circle className="w-6 h-6 text-dark-400" />
      {showLabels && <span className="text-sm text-dark-500">{status}</span>}
    </div>
  );
}

interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md' | 'lg';
}

export function StatusBadge({ status, size = 'md' }: StatusBadgeProps) {
  const currentIndex = getStepIndex(status);
  const step = ORDER_PROGRESS_STEPS[currentIndex] || ORDER_PROGRESS_STEPS.find(s => s.value === status);

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-3 py-1 text-xs',
    lg: 'px-4 py-1.5 text-sm',
  };

  if (status === 'Payment Rejected') {
    return (
      <span className={`inline-flex items-center gap-1.5 rounded-full font-semibold border ${PAYMENT_REJECTED_STEP.bgColor} ${PAYMENT_REJECTED_STEP.color} ${PAYMENT_REJECTED_STEP.borderColor} ${sizeClasses[size]}`}>
        <span className="w-4 h-4 bg-accent-red rounded-full flex items-center justify-center">
          <span className="text-white text-xs font-bold">!</span>
        </span>
        Rejected
      </span>
    );
  }

  if (status === 'Cancelled') {
    return (
      <span className={`inline-flex items-center gap-1.5 rounded-full font-semibold border ${CANCELLED_STEP.bgColor} ${CANCELLED_STEP.color} ${CANCELLED_STEP.borderColor} ${sizeClasses[size]}`}>
        Cancelled
      </span>
    );
  }

  if (status === 'Cancel Requested') {
    return (
      <span className={`inline-flex items-center gap-1.5 rounded-full font-semibold border ${CANCEL_REQUESTED_STEP.bgColor} ${CANCEL_REQUESTED_STEP.color} ${CANCEL_REQUESTED_STEP.borderColor} ${sizeClasses[size]}`}>
        Cancel Requested
      </span>
    );
  }

  if (status === 'Paid') {
    return (
      <span className={`inline-flex items-center gap-1.5 rounded-full font-semibold border bg-accent-green/10 text-accent-green border-accent-green/30 ${sizeClasses[size]}`}>
        <CheckCircle className="w-4 h-4" />
        Paid
      </span>
    );
  }

  if (status === 'Preparing' || status === 'Ready to Ship' || status === 'Ready for Pickup' || status === 'Shipped') {
    return (
      <span className={`inline-flex items-center gap-1.5 rounded-full font-semibold border ${step?.bgColor || 'bg-primary-100'} text-primary-700 border-primary-300 ${sizeClasses[size]}`}>
        {step?.label || status}
      </span>
    );
  }

  if (step) {
    return (
      <span className={`inline-flex items-center gap-1.5 rounded-full font-semibold border ${step.bgColor} ${step.color} ${step.borderColor} ${sizeClasses[size]}`}>
        {step.label}
      </span>
    );
  }

  // Default fallback
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full font-semibold border bg-dark-100 text-dark-700 border-dark-300 ${sizeClasses[size]}`}>
      <Clock className="w-4 h-4" />
      {status}
    </span>
  );
}
