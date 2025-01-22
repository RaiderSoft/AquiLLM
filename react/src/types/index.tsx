export interface TestComponentProps {
  message?: string;
}

// Define the global mounting function
declare global {
  interface Window {
    mountReactComponent: (
      elementId: string,
      componentName: string,
      props?: Record<string, unknown>
    ) => void;
  }
}