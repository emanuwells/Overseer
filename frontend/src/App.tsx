import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { DagPage } from './pages/DagPage';
import { EnvironmentPage } from './pages/EnvironmentPage';
import { OperationsPage } from './pages/OperationsPage';
import { RunsPage } from './pages/RunsPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter basename="/ui">
        <Routes>
          <Route path="/" element={<Navigate to="/operations" replace />} />
          <Route path="/operations" element={<OperationsPage />} />
          <Route path="/runs" element={<RunsPage />} />
          <Route path="/dag" element={<DagPage />} />
          <Route path="/environment" element={<EnvironmentPage />} />
          <Route path="*" element={<Navigate to="/operations" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
