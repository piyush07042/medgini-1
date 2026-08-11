import { Component, ErrorInfo, ReactNode } from 'react';
import { AlertOctagon, RefreshCw } from 'lucide-react';

interface Props {
  children?: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-4 text-center">
          <div className="flex max-w-md flex-col items-center justify-center rounded-3xl border border-slate-200 bg-white p-8 shadow-xl">
            <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-rose-50 text-rose-500 ring-8 ring-rose-50/50">
              <AlertOctagon className="h-10 w-10" />
            </div>
            <h1 className="mb-2 text-2xl font-bold text-slate-900">Something went wrong</h1>
            <p className="mb-6 text-sm text-slate-500">
              An unexpected error occurred in the application interface. Our team has been notified.
            </p>
            {this.state.error && (
              <div className="mb-6 w-full overflow-auto rounded-xl bg-slate-100 p-4 text-left text-xs text-slate-600">
                <code className="break-all">{this.state.error.message}</code>
              </div>
            )}
            <button
              onClick={this.handleReset}
              className="group flex w-full items-center justify-center gap-2 rounded-2xl bg-slate-900 px-5 py-3.5 text-sm font-semibold text-white transition-all hover:bg-slate-800 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2"
            >
              <RefreshCw className="h-4 w-4 transition-transform group-hover:rotate-180" />
              Reload Application
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
