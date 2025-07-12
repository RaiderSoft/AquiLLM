import {
  WebSocketGateway,
  SubscribeMessage,
  MessageBody,
  ConnectedSocket,
  OnGatewayConnection,
  OnGatewayDisconnect,
} from '@nestjs/websockets';
import { Socket } from 'socket.io';
import { Injectable } from '@nestjs/common';
import { ClaudeInterface } from '../services/llm.service';
import { 
  Conversation, 
  LLMMessage, 
  UserMessage, 
  MessageRole, 
  LLMTool,
  ToolChoice,
  ToolChoiceType 
} from '../entities/conversation.entity';
import { AppendMessageDto, RateMessageDto } from '../dto/chat.dto';

// Dummy tool implementations
const testFunction: LLMTool = new LLMTool({
  name: 'test_function',
  description: 'Test function that prints each string from the input.',
  input_schema: {
    type: 'object',
    properties: {
      strings: {
        type: 'array',
        items: { type: 'string' },
        description: 'A list of strings to print'
      }
    },
    required: ['strings']
  }
}, 'user');

const vectorSearchTool: LLMTool = new LLMTool({
  name: 'vector_search',
  description: 'Uses a combination of vector search, trigram search and reranking to search the documents available to the user.',
  input_schema: {
    type: 'object',
    properties: {
      search_string: {
        type: 'string',
        description: 'The string to search by. Often it helps to phrase it as a question.'
      },
      top_k: {
        type: 'integer',
        description: 'The number of results to return. Start low and increase if the desired information is not found. Go no higher than about 15.'
      }
    },
    required: ['search_string', 'top_k']
  }
}, 'assistant');

class CollectionsRef {
  collections: number[] = [];
}

interface ConversationStore {
  id: number;
  name?: string;
  convo: Conversation;
  owner: string; // user identifier
  created_at: Date;
}

@WebSocketGateway({
  cors: {
    origin: "*",
  },
})
@Injectable()
export class ChatGateway implements OnGatewayConnection, OnGatewayDisconnect {
  private llmInterface: ClaudeInterface;
  private conversations: Map<string, ConversationStore> = new Map();
  private tools: LLMTool[] = [];
  private collectionsRef = new CollectionsRef();
  
  constructor() {
    this.llmInterface = new ClaudeInterface();
    this.tools = [testFunction, vectorSearchTool];
  }

  async handleConnection(client: Socket) {
    console.log(`Client connected: ${client.id}`);
    
    // Extract conversation ID from query params or path
    const convoId = client.handshake.query.convoId as string;
    const userId = client.handshake.query.userId as string || 'anonymous';
    
    if (!convoId) {
      client.emit('error', { exception: 'Invalid chat_id' });
      client.disconnect();
      return;
    }

    // Get or create conversation
    let conversation = this.conversations.get(convoId);
    if (!conversation) {
      conversation = {
        id: parseInt(convoId),
        convo: {
          system: 'You are a helpful AI assistant. You have access to various tools to help answer questions and search documents.',
          messages: []
        },
        owner: userId,
        created_at: new Date()
      };
      this.conversations.set(convoId, conversation);
    }

    // Check ownership
    if (conversation.owner !== userId) {
      client.emit('error', { exception: 'Invalid chat_id' });
      client.disconnect();
      return;
    }

    client.data.convoId = convoId;
    client.data.userId = userId;

    const sendFunc = async (convo: Conversation) => {
      const updated = this.conversations.get(convoId);
      if (updated) {
        updated.convo = convo;
        this.conversations.set(convoId, updated);
      }
      client.emit('conversation', { conversation: convo });
    };

    try {
      // Start the conversation spin if there are messages
      if (conversation.convo.messages.length > 0) {
        await this.llmInterface.spin(conversation.convo, 5, sendFunc, 2048);
      }
    } catch (error) {
      console.error('Error in conversation spin:', error);
      if (error.message.includes('authentication') || error.message.includes('apiKey')) {
        client.emit('error', { exception: 'Authentication error: Please check API key configuration.' });
      } else {
        client.emit('error', { exception: 'LLM provider is currently overloaded. Try again later.' });
      }
    }
  }

  handleDisconnect(client: Socket) {
    console.log(`Client disconnected: ${client.id}`);
  }

  @SubscribeMessage('chat_action')
  async handleChatAction(
    @MessageBody() data: any,
    @ConnectedSocket() client: Socket,
  ) {
    const convoId = client.data.convoId;
    const userId = client.data.userId;
    
    if (!convoId || !userId) {
      client.emit('error', { exception: 'Invalid session' });
      return;
    }

    const conversation = this.conversations.get(convoId);
    if (!conversation) {
      client.emit('error', { exception: 'Conversation not found' });
      return;
    }

    const sendFunc = async (convo: Conversation) => {
      conversation.convo = convo;
      this.conversations.set(convoId, conversation);
      client.emit('conversation', { conversation: convo });
    };

    try {
      const action = data.action;
      
      if (action === 'append') {
        await this.handleAppendMessage(data as AppendMessageDto, conversation, sendFunc);
      } else if (action === 'rate') {
        await this.handleRateMessage(data as RateMessageDto, conversation);
      } else {
        throw new Error(`Invalid action "${action}"`);
      }
    } catch (error) {
      console.error('Error handling chat action:', error);
      if (error.message.includes('authentication') || error.message.includes('apiKey')) {
        client.emit('error', { exception: 'Authentication error: Please check API key configuration.' });
      } else {
        client.emit('error', { exception: 'A server error has occurred. Try reloading the page' });
      }
    }
  }

  private async handleAppendMessage(
    data: AppendMessageDto, 
    conversationStore: ConversationStore,
    sendFunc: (convo: Conversation) => Promise<void>
  ) {
    this.collectionsRef.collections = data.collections;
    
    const userMessage: UserMessage = {
      role: MessageRole.USER,
      content: data.message.content,
      tools: this.tools,
      tool_choice: { type: ToolChoiceType.AUTO },
      message_uuid: this.generateUUID()
    };

    conversationStore.convo.messages.push(userMessage);
    
    await this.llmInterface.spin(conversationStore.convo, 5, sendFunc, 2048);
  }

  private async handleRateMessage(data: RateMessageDto, conversationStore: ConversationStore) {
    const message = conversationStore.convo.messages.find(
      msg => msg.message_uuid === data.uuid
    );
    
    if (message) {
      message.rating = data.rating;
    }
  }

  private generateUUID(): string {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c == 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }
}