# AquiLLM

<div align="center">
  <img src="aquillm/aquillm/static/images/aquila-small.svg" alt="AquiLLM Logo" width="200"/>
</div>

## Overview

AquiLLM is a powerful Retrieval-Augmented Generation (RAG) platform that transforms how organizations interact with their document collections. By combining vector search and large language models, AquiLLM provides intelligent knowledge retrieval and natural language interactions with your data.

## Features

- **Document Management**: Ingest and organize PDFs, VTT/audio files, and text documents
- **Semantic Search**: Vector-based similarity search across all your documents
- **AI-Powered Responses**: Query your documents using natural language through LLM integration
- **Collection Organization**: Structured document collections with flexible categorization
- **Collaborative Access**: Team-based permissions (view, edit, manage) for collections
- **Real-time Monitoring**: Track document ingestion progress with WebSocket updates
- **Conversation History**: Maintain context across multiple queries
- **Modern UI**: Responsive interface built with React and Tailwind CSS

## Architecture

AquiLLM is built with modern technologies for reliability and scalability:

- **Backend**: Django with Celery for asynchronous processing
- **Frontend**: React with TypeScript and Tailwind CSS
- **Database**: PostgreSQL with pgvector for vector embeddings
- **Storage**: Compatible with S3-style object storage
- **Containerization**: Docker for easy deployment
- **LLM Integration**: Support for Claude and other large language models

## Quick Start

### Environment Setup

⚠️ **IMPORTANT**: AquiLLM requires environment variables to run properly.

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your settings (especially API keys for LLMs)

### Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/AquiLLM.git
cd AquiLLM

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your configuration

# Start the development environment
docker compose up web
```

Default development credentials:
- Username: `dev`
- Password: `rickbailey`

### Production Deployment

For production deployment, use the production Docker configuration:

```bash
# Copy and configure environment variables for production
cp .env.example .env
# Edit .env with production settings (set DJANGO_DEBUG=0)

# Run with production configuration
docker compose -f docker-compose-prod.yml up -d
```

See the [deployment documentation](deployment/README.md) for complete instructions.

## Required Environment Variables

AquiLLM is configured through environment variables in a `.env` file. Key variables include:

```
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_NAME=aquillm
POSTGRES_HOST=db

# Storage
STORAGE_HOST=storage:9000
STORAGE_ACCESS_KEY=your_access_key
STORAGE_SECRET_KEY=your_secret_key

# Security
SECRET_KEY=your_secure_django_key
DJANGO_DEBUG=1  # Set to 0 for production

# OAuth (for login)
GOOGLE_OAUTH2_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH2_CLIENT_SECRET=your_google_client_secret

# LLM Integration
ANTHROPIC_API_KEY=your_anthropic_api_key
```

For a complete list of environment variables, see [.env.example](.env.example).

## Testing

Run the test suite with:

```bash
docker compose -f docker-compose-test.yml up
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

AquiLLM is licensed under [LICENSE](LICENSE). See the LICENSE file for details.