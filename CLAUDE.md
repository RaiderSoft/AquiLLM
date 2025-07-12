# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Django Backend
- **Development server**: `docker compose up web` (default user: dev/rickbailey)
- **Django management**: Run commands inside the container or use `python aquillm/manage.py <command>`
- **Database migrations**: `python aquillm/manage.py makemigrations` and `python aquillm/manage.py migrate`
- **Tests**: `pytest` (configured for Django with aquillm.settings module)
- **Type checking**: `mypy` (mypy and django-stubs installed)

### React Frontend
- **Development**: `cd react && npm run dev` (Vite dev server)
- **Build**: `cd react && npm run build` (outputs to build directory)
- **Watch mode**: `cd react && npm run watch` (continuous build)
- **Type checking**: `cd react && npm run typecheck`

### Docker Environment
- **Development**: `docker-compose.yml` 
- **Production**: `docker-compose-prod.yml`
- **Testing**: `docker-compose-test.yml`

## Architecture Overview

### Tech Stack
- **Backend**: Django 5.x with PostgreSQL, Redis, Celery
- **Frontend**: React 19 with TypeScript, Vite, Tailwind CSS
- **Vector Database**: pgvector extension for PostgreSQL
- **LLM Integration**: OpenAI, Anthropic Claude, Google Gemini, Cohere
- **Real-time**: Django Channels with WebSockets
- **Authentication**: django-allauth with Google OAuth
- **Storage**: S3-compatible storage (MinIO/AWS S3)

### Core Django Apps
- **aquillm**: Main app with models, LLM integrations, document processing
- **chat**: WebSocket-based chat functionality  
- **ingest**: Document ingestion pipeline with Celery tasks

### Key Components

#### Document Processing Pipeline
- PDF ingestion via `pypdf` with text chunking
- VTT (subtitle) file processing
- arXiv paper integration
- Vector embeddings for semantic search using pgvector
- Celery async processing for document ingestion

#### LLM Integration
- Multiple LLM provider support (OpenAI, Claude, Gemini, Cohere)
- Conversation management with message history
- RAG (Retrieval Augmented Generation) with vector similarity search
- Streaming responses via WebSockets

#### Frontend Architecture
- React components in `react/src/components/`
- TypeScript interfaces in `react/src/types/`
- Tailwind CSS for styling
- Vite for build tooling
- Real-time updates via WebSocket connections

### Database Models
- **PDFDocument/VTTDocument**: Document storage with vector embeddings
- **TextChunk**: Chunked text with embeddings for similarity search
- **Collection**: Hierarchical document organization
- **LLMConversation/WSConversation**: Chat history and context
- **EmailWhitelist**: Authentication restrictions

### Key Files
- `aquillm/models.py`: Core data models with vector search
- `aquillm/llm.py`: LLM provider abstractions
- `aquillm/chunking.py`: Text processing and embedding logic
- `aquillm/consumers.py`: WebSocket consumers for real-time features
- `react/src/components/ChatComponent.tsx`: Main chat interface

## Environment Configuration
- Django settings use environment variables for secrets
- Debug mode controlled by `DJANGO_DEBUG` env var
- Database, Redis, storage, and OAuth credentials via environment
- Docker compose files define service dependencies

## Testing
- pytest configured for Django testing
- Test database auto-created as 'test'
- Test paths: `aquillm/tests/` and `chat/tests/`

## React Development Notes
Note: The Cursor rules file mentions Vue.js patterns but the actual frontend uses React. When working with React components:
- Use TypeScript for all components
- Follow functional component patterns with hooks
- Use Tailwind CSS for styling
- Maintain mobile-first responsive design