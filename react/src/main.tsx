import React from 'react';
import { createRoot } from 'react-dom/client';
import TestComponent from './components/TestComponent';

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
    // Add other components here
  };
  
  const Component = components[componentName];
  if (Component) {
    root.render(<Component {...props} />);
  } else {
    console.error(`Component '${componentName}' not found`);
  }
};