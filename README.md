# NestJS Chat Server

A NestJS implementation of the Django chat functionality with WebSocket support and Claude AI integration.

## Features

- WebSocket-based real-time chat
- Claude AI integration via Anthropic SDK
- Tool calling support (with dummy implementations)
- Simple HTML frontend for testing
- TypeScript implementation

## Setup

0. Navigate to directory
   ```
   cd nestjs-chat
   ```

2. Install dependencies:
```bash
npm install
```

2. Copy environment file and configure:
```bash
cp .env.example .env
```

3. Add your Anthropic API key to `.env`:
```
ANTHROPIC_API_KEY=your_api_key_here
```

## Running the Application

### Development mode:
```bash
npm run start:dev
```

### Production build:
```bash
npm run build
npm start
```

The server will start on port 3001 by default.

## Testing

Open your browser to `http://localhost:3001/index.html` to access the test frontend.

The frontend allows you to:
- Connect to the WebSocket server
- Send messages to the AI assistant
- View the conversation history
- Test real-time updates

## API

### WebSocket Events

#### Client to Server:
- `chat_action` - Send user messages or rate messages

#### Server to Client:
- `conversation` - Receive updated conversation data
- `error` - Receive error messages

### Message Format

**Append Message:**
```json
{
  "action": "append",
  "collections": [1, 2, 3],
  "message": {
    "content": "Hello, assistant!",
    "role": "user"
  }
}
```

**Rate Message:**
```json
{
  "action": "rate",
  "uuid": "message-uuid",
  "rating": 5
}
```

## Architecture

- `src/main.ts` - Application entry point
- `src/app.module.ts` - Main application module
- `src/gateways/chat.gateway.ts` - WebSocket gateway (translated from Django consumers.py)
- `src/services/llm.service.ts` - LLM integration service (translated from Django llm.py)
- `src/entities/` - TypeScript interfaces and entities
- `src/dto/` - Data transfer objects for validation
- `public/index.html` - Simple test frontend

## Notes

- Tool functions are currently dummy implementations
- No persistent database storage (conversations stored in memory)
- Authentication is simplified for testing
 
