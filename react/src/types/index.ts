export interface TestComponentProps {
  message?: string;
}

export interface IngestionDashboardLauncherProps {
  wsUrl: string;
}

export interface IngestionMessage {
  messages?: string[];
  progress?: number;
  exception?: string;
  complete?: boolean;
}

export interface IngestionDashboardProps {
  wsUrl: string;
}

export interface PDFIngestionMonitorProps {
  documentName: string;
  documentId: string;
}

declare global {
  interface Window {
    mountReactComponent: (
      elementId: string,
      componentName: string,
      props?: Record<string, unknown>
    ) => void;
  }
}