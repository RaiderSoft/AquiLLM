// Folder component
function Folder({ folder }) {
    console.log('Rendering folder:', folder);
    const handleClick = () => {
        window.location.href = `/collection/${folder.id}/`;
    };

    return (
        <div 
            onClick={handleClick}
            className="bg-white shadow-sm hover:shadow-md rounded p-4 mb-4 cursor-pointer transition-shadow duration-200"
        >
            <div className="flex justify-between items-center">
                <div className="flex items-center">
                    <svg className="w-6 h-6 mr-3 text-deep-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                    </svg>
                    <h2 className="text-xl font-bold text-deep-primary">{folder.name}</h2>
                </div>
                <div className="flex items-center">
                    <span className="text-deep-primary">{folder.document_count} document{folder.document_count !== 1 ? 's' : ''}</span>
                    <span className="ml-4 text-sm text-deep-secondary">Your role: {folder.permission}</span>
                </div>
            </div>
        </div>
    );
}

// New Folder Form component
function NewFolderForm({ onFolderCreated }) {
    const [name, setName] = React.useState('');
    const [isSubmitting, setIsSubmitting] = React.useState(false);
    const [error, setError] = React.useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!name.trim()) return;

        setIsSubmitting(true);
        setError(null);

        try {
            const response = await fetch('/get_collections_json/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({ name: name.trim() })
            });

            const contentType = response.headers.get('content-type');
            if (!response.ok) {
                if (contentType && contentType.includes('application/json')) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Failed to create folder');
                } else {
                    throw new Error('Failed to create folder');
                }
            }

            const newFolder = await response.json();
            setName('');
            if (onFolderCreated) {
                onFolderCreated(newFolder);
            }
        } catch (err) {
            setError(err.message || 'Failed to create folder. Please try again.');
            console.error('Error creating folder:', err);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="mt-8 bg-white shadow-sm rounded p-6 border border-lighter-primary">
            <h2 className="text-2xl font-bold mb-6 text-deep-primary">New Folder</h2>
            <form onSubmit={handleSubmit}>
                <div className="mb-4">
                    <input 
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        className="w-full p-3 border border-lighter-primary rounded focus:outline-none focus:border-deep-primary focus:ring-1 focus:ring-deep-primary"
                        placeholder="Enter folder name"
                        disabled={isSubmitting}
                    />
                </div>
                {error && (
                    <div className="mb-4 text-red-600 text-sm">{error}</div>
                )}
                <button 
                    type="submit"
                    disabled={isSubmitting || !name.trim()}
                    className={`w-full p-3 text-white rounded transition-colors duration-200 ${
                        isSubmitting || !name.trim() 
                            ? 'bg-gray-400 cursor-not-allowed' 
                            : 'bg-deep-primary hover:bg-deep-secondary'
                    }`}
                >
                    {isSubmitting ? 'Creating...' : 'Create Folder'}
                </button>
            </form>
        </div>
    );
}

// Main FolderList component
function FolderList() {
    console.log('FolderList component mounting');
    const [folders, setFolders] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState(null);

    const fetchFolders = async () => {
        console.log('Fetching folders...');
        try {
            const response = await fetch('/get_collections_json/', {
                credentials: 'same-origin',
                headers: {
                    'Accept': 'application/json'
                }
            });
            console.log('Response:', response);
            
            const contentType = response.headers.get('content-type');
            if (!response.ok) {
                if (contentType && contentType.includes('application/json')) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Failed to fetch folders');
                } else {
                    const text = await response.text();
                    console.error('Response text:', text);
                    throw new Error('Failed to fetch folders');
                }
            }

            if (!contentType || !contentType.includes('application/json')) {
                throw new Error('Received non-JSON response');
            }

            const data = await response.json();
            console.log('Received folders:', data);
            setFolders(data);
            setLoading(false);
        } catch (error) {
            console.error('Error fetching folders:', error);
            setError(error.message || 'Failed to load folders');
            setLoading(false);
        }
    };

    React.useEffect(() => {
        fetchFolders();
    }, []);

    console.log('Current state:', { loading, error, folders });

    const handleFolderCreated = (newFolder) => {
        setFolders(prevFolders => [...prevFolders, newFolder]);
    };

    if (loading) {
        console.log('Rendering loading state');
        return (
            <div className="flex justify-center items-center min-h-[200px]">
                <div className="text-lg text-deep-primary">Loading folders...</div>
            </div>
        );
    }

    if (error) {
        console.log('Rendering error state');
        return (
            <div className="text-red-600 p-4 rounded bg-red-50 border border-red-200">
                {error}
            </div>
        );
    }

    console.log('Rendering folder list');
    return (
        <div className="max-w-4xl mx-auto">
            <h1 className="text-3xl font-bold mb-8 text-deep-primary">Folders</h1>
            {folders.length === 0 ? (
                <div className="text-center py-12 bg-white rounded shadow-sm">
                    <p className="text-deep-primary mb-4">No folders yet</p>
                    <p className="text-sm text-deep-secondary">Create a folder to get started</p>
                </div>
            ) : (
                <div className="space-y-4">
                    {folders.map(folder => (
                        <Folder key={folder.id} folder={folder} />
                    ))}
                </div>
            )}
            <NewFolderForm onFolderCreated={handleFolderCreated} />
        </div>
    );
}

// Make sure React is mounted
console.log('Script loaded, attempting to render...');
const rootElement = document.getElementById('folders-root');
console.log('Root element:', rootElement);

ReactDOM.render(
    <FolderList />,
    rootElement
); 