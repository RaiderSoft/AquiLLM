// src/components/ThemeSelector.js
import React, { useState, useEffect } from 'react';

const ThemeSelector: React.FC = () => {
  const [themeSettings, setThemeSettings] = useState({
    color_scheme: 'light',
    font_family: 'latin_modern_roman'
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch current settings on mount.
  useEffect(() => {
    fetch('/api/user-settings/', {
      credentials: 'include', // ensure cookies are sent
    })
      .then(res => res.json())
      .then(data => {
        setThemeSettings(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching user settings:', err);
        setError(err);
        setLoading(false);
      });
  }, []);

// Update state when user selects a new value
const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const { name, value } = e.target;
    setThemeSettings((prev) => ({ ...prev, [name]: value }));
};

  // Submit the changes to the server.
interface SubmitResponse {
    color_scheme: string;
    font_family: string;
}

const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    fetch('/api/user-settings/', {
        method: 'POST', // alternatively, you can use PUT or PATCH
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(themeSettings)
    })
        .then(res => res.json())
        .then((data: SubmitResponse) => {
            alert("Settings updated!");
            // Optionally apply theme changes immediately:
            applyTheme(data);
        })
        .catch((err: Error) => console.error('Error updating settings:', err));
};

  // This helper function applies the chosen theme to the page.
  const applyTheme = ({ color_scheme, font_family }: { color_scheme: string; font_family: string }) => {
    // Remove any previously set theme classes (if using utility classes to indicate theme).
    document.body.classList.remove('theme-light', 'theme-dark', 'theme-blue');
    document.body.classList.add(`theme-${color_scheme}`);

    // If you want to change the font globally, you could update a CSS variable or
    // attach a class to <html> or <body> that Tailwind uses to control typography.
    document.body.classList.remove('font-latin_modern_roman', 'font-sans_serif');
    document.body.classList.add(`font-${font_family}`);
  };

  if (loading) return <div>Loading settings...</div>;
  if (error) return <div>Error loading settings.</div>;

  return (
    <div className="p-4">
      <h2 className="mb-4 text-xl font-bold">Select Your Theme</h2>
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label htmlFor="color_scheme" className="block mb-1">
            Color Scheme:
          </label>
          <select
            id="color_scheme"
            name="color_scheme"
            value={themeSettings.color_scheme}
            onChange={handleChange}
            className="border p-2 rounded"
          >
            <option value="light">Light</option>
            <option value="dark">Dark</option>
            <option value="blue">Blue</option>
          </select>
        </div>
        <div className="mb-4">
          <label htmlFor="font_family" className="block mb-1">
            Font Family:
          </label>
          <select
            id="font_family"
            name="font_family"
            value={themeSettings.font_family}
            onChange={handleChange}
            className="border p-2 rounded"
          >
            <option value="latin_modern_roman">Latin Modern Roman (Serif)</option>
            <option value="sans_serif">Sans-serif</option>
          </select>
        </div>
        <button type="submit" className="bg-accent-default text-white py-2 px-4 rounded">
          Save Settings
        </button>
      </form>
    </div>
  );
};

export default ThemeSelector;
