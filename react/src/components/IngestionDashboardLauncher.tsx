import React, { useState } from 'react';
import IngestionDashboard from './IngestionDashboard';
import { IngestionDashboardLauncherProps } from '../types';
import { X } from 'lucide-react';

interface IngestionDashboardModalProps {
  wsUrl: string;
  onClose: () => void;
}

const IngestionDashboardModal: React.FC<IngestionDashboardModalProps> = ({ wsUrl, onClose }) => {
  return (
    <div className="fixed bottom-0 left-1/2 max-w-2xl right-0 z-50 flex items-end justify-center pointer-events-auto">
      {/* Modal container styled as a bottom sheet */}
      <div
        className="relative bg-lighter-primary w-full rounded-t-lg shadow-lg"
        style={{ height: '33vh' }}
      >
        {/* Header */}
        <div className="flex justify-between items-center border-b px-4 py-2">
          <h2 className="text-lg font-bold">Ingestion Dashboard</h2>
          <button onClick={onClose} className="text-gray-600 hover:text-gray-800">
            <X />
          </button>
        </div>
        {/* Content */}
        <div className="p-4 overflow-y-auto h-full">
          <IngestionDashboard wsUrl={wsUrl} />
        </div>
      </div>
    </div>
  );
};

const IngestionDashboardLauncher: React.FC<IngestionDashboardLauncherProps> = ({ wsUrl }) => {
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <>
      {/* Clickable div that toggles the modal's visibility */}
      <div onClick={() => setModalOpen(!modalOpen)} className="cursor-pointer">
        Ingestion Monitor
      </div>

      {/* The modal is always in the DOM; its visibility is controlled by the 'hidden' class */}
      <div className={`${modalOpen ? '' : 'hidden'}`}>
        <IngestionDashboardModal wsUrl={wsUrl} onClose={() => setModalOpen(false)} />
      </div>
    </>
  );
};

export default IngestionDashboardLauncher;
