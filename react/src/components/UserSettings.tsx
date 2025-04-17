// src/components/ThemeSelector.js
import React, { useState, useEffect } from 'react';
import { getCookie } from '../utils/csrf';

const UserSettings: React.FC = () => {
  const [themeSettings, setThemeSettings] = useState({
    color_scheme: 'aquillm_default_dark',
    font_family: 'verdana'
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch current settings on mount.
  useEffect(() => {
    fetch('/api/user-settings/', {
      credentials: 'include', // ensure cookies are sent
      headers: { 'Accept': 'application/json' } // force a JSON response
    })
      .then(res => res.json())
      .then(data => {
        console.log('Fetched settings:', data); // Check the structure!
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
      method: 'POST', 
      headers: { 
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
      credentials: 'include',
      body: JSON.stringify(themeSettings)
    })
      .then(res => res.json())
      .then((data: SubmitResponse) => {
        alert("Settings updated!");
        applyTheme(data);
      })
      .catch((err: Error) => console.error('Error updating settings:', err));
};

  // This helper function applies the chosen theme to the page.
  const applyTheme = ({ color_scheme, font_family }: { color_scheme: string; font_family: string }) => {
    // Remove any previously set theme classes (if using utility classes to indicate theme).
    document.body.classList.remove('theme-aquillm_default_dark', 'theme-aquillm_default_light', 'theme-aquillm_default_light_accessible_chat', 'theme-aquillm_default_dark_accessible_chat', 'theme-high_contrast');
    document.body.classList.add(`theme-${color_scheme}`);

    // If you want to change the font globally, you could update a CSS variable or
    // attach a class to <html> or <body> that Tailwind uses to control typography.
    document.body.classList.remove('font-latin_modern_roman', 'font-sans_serif', 'font-lexend', 'font-comicsans', 'font-opendyslexic', 'font-timesnewroman', 'font-verdana');
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
            <option value="aquillm_default_dark">Aquillm Default Dark</option>
            <option value="aquillm_default_light">Aquillm Default Light</option>
            <option value="aquillm_default_dark_accessible_chat">Aquillm Default Dark - Accessible Chat</option>
            <option value="aquillm_default_light_accessible_chat">Aquillm Default Light - Accessible Chat</option>
            <option value="high_contrast">High Contrast</option>
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
            <option value="sans_serif">Sans-serif (Default)</option>
            <option value="verdana">Verdana</option>
            <option value="timesnewroman">Times New Roman</option>
            <option value="opendyslexic">Open Dyslexic</option>
            <option value="lexend">Lexend</option>
            <option value="comicsans">Comic Sans</option>
          </select>
        </div>
        <button type="submit" className="bg-accent text-slight_muted_white py-2 px-4 rounded">
          Save Settings
        </button>
      </form>
    </div>
  );
};

export default UserSettings;
