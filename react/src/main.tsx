import React from 'react';

import { createRoot } from 'react-dom/client';
import TestComponent from './components/TestComponent';
import PDFIngestionMonitor from './components/PDFIngestionMonitor';

// Type for the components mapping
type ComponentsMap = {
  [key: string]: React.ComponentType<any>;
};

// Mount function with type safety
window.mountReactComponent = (
  elementId: string,
  componentName: string,
  props: Record<string, unknown> = {}
) => {
  const element = document.getElementById(elementId);
  if (!element) {
    console.error(`Element with id '${elementId}' not found`);
    return;
  }

  const root = createRoot(element);
  
  const components: ComponentsMap = {
    TestComponent: TestComponent,
    PDFIngestionMonitor: PDFIngestionMonitor,
    // Add other components here
  };
  
  const Component = components[componentName];
  if (Component) {
    root.render(<Component {...props} />);
  } else {
    console.error(`Component '${componentName}' not found`);
  }
};

