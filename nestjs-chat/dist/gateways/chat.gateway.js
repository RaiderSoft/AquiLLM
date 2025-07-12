"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (this && this.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};
var __param = (this && this.__param) || function (paramIndex, decorator) {
    return function (target, key) { decorator(target, key, paramIndex); }
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.ChatGateway = void 0;
const websockets_1 = require("@nestjs/websockets");
const socket_io_1 = require("socket.io");
const common_1 = require("@nestjs/common");
const llm_service_1 = require("../services/llm.service");
const conversation_entity_1 = require("../entities/conversation.entity");
const testFunction = new conversation_entity_1.LLMTool({
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
const vectorSearchTool = new conversation_entity_1.LLMTool({
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
    constructor() {
        this.collections = [];
    }
}
let ChatGateway = class ChatGateway {
    constructor() {
        this.conversations = new Map();
        this.tools = [];
        this.collectionsRef = new CollectionsRef();
        this.llmInterface = new llm_service_1.ClaudeInterface();
        this.tools = [testFunction, vectorSearchTool];
    }
    async handleConnection(client) {
        console.log(`Client connected: ${client.id}`);
        const convoId = client.handshake.query.convoId;
        const userId = client.handshake.query.userId || 'anonymous';
        if (!convoId) {
            client.emit('error', { exception: 'Invalid chat_id' });
            client.disconnect();
            return;
        }
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
        if (conversation.owner !== userId) {
            client.emit('error', { exception: 'Invalid chat_id' });
            client.disconnect();
            return;
        }
        client.data.convoId = convoId;
        client.data.userId = userId;
        const sendFunc = async (convo) => {
            const updated = this.conversations.get(convoId);
            if (updated) {
                updated.convo = convo;
                this.conversations.set(convoId, updated);
            }
            client.emit('conversation', { conversation: convo });
        };
        try {
            if (conversation.convo.messages.length > 0) {
                await this.llmInterface.spin(conversation.convo, 5, sendFunc, 2048);
            }
        }
        catch (error) {
            console.error('Error in conversation spin:', error);
            if (error.message.includes('authentication') || error.message.includes('apiKey')) {
                client.emit('error', { exception: 'Authentication error: Please check API key configuration.' });
            }
            else {
                client.emit('error', { exception: 'LLM provider is currently overloaded. Try again later.' });
            }
        }
    }
    handleDisconnect(client) {
        console.log(`Client disconnected: ${client.id}`);
    }
    async handleChatAction(data, client) {
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
        const sendFunc = async (convo) => {
            conversation.convo = convo;
            this.conversations.set(convoId, conversation);
            client.emit('conversation', { conversation: convo });
        };
        try {
            const action = data.action;
            if (action === 'append') {
                await this.handleAppendMessage(data, conversation, sendFunc);
            }
            else if (action === 'rate') {
                await this.handleRateMessage(data, conversation);
            }
            else {
                throw new Error(`Invalid action "${action}"`);
            }
        }
        catch (error) {
            console.error('Error handling chat action:', error);
            if (error.message.includes('authentication') || error.message.includes('apiKey')) {
                client.emit('error', { exception: 'Authentication error: Please check API key configuration.' });
            }
            else {
                client.emit('error', { exception: 'A server error has occurred. Try reloading the page' });
            }
        }
    }
    async handleAppendMessage(data, conversationStore, sendFunc) {
        this.collectionsRef.collections = data.collections;
        const userMessage = {
            role: conversation_entity_1.MessageRole.USER,
            content: data.message.content,
            tools: this.tools,
            tool_choice: { type: conversation_entity_1.ToolChoiceType.AUTO },
            message_uuid: this.generateUUID()
        };
        conversationStore.convo.messages.push(userMessage);
        await this.llmInterface.spin(conversationStore.convo, 5, sendFunc, 2048);
    }
    async handleRateMessage(data, conversationStore) {
        const message = conversationStore.convo.messages.find(msg => msg.message_uuid === data.uuid);
        if (message) {
            message.rating = data.rating;
        }
    }
    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
            const r = Math.random() * 16 | 0;
            const v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
};
exports.ChatGateway = ChatGateway;
__decorate([
    (0, websockets_1.SubscribeMessage)('chat_action'),
    __param(0, (0, websockets_1.MessageBody)()),
    __param(1, (0, websockets_1.ConnectedSocket)()),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [Object, socket_io_1.Socket]),
    __metadata("design:returntype", Promise)
], ChatGateway.prototype, "handleChatAction", null);
exports.ChatGateway = ChatGateway = __decorate([
    (0, websockets_1.WebSocketGateway)({
        cors: {
            origin: "*",
        },
    }),
    (0, common_1.Injectable)(),
    __metadata("design:paramtypes", [])
], ChatGateway);
//# sourceMappingURL=chat.gateway.js.map