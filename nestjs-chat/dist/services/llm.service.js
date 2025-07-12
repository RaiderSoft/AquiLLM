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
Object.defineProperty(exports, "__esModule", { value: true });
exports.ClaudeInterface = exports.LLMInterface = void 0;
const common_1 = require("@nestjs/common");
const sdk_1 = require("@anthropic-ai/sdk");
const conversation_entity_1 = require("../entities/conversation.entity");
class LLMInterface {
    constructor() {
        this.baseArgs = {};
    }
    async callTool(message) {
        const tools = message.tools;
        if (!tools) {
            throw new Error('call_tool called on a message with no tools!');
        }
        const name = message.tool_call_name;
        const input = message.tool_call_input;
        const toolsDict = Object.fromEntries(tools.map(tool => [tool.name, tool]));
        let result;
        let resultDict;
        if (!name || !(name in toolsDict)) {
            resultDict = { exception: 'Function name is not valid' };
            result = JSON.stringify(resultDict);
        }
        else {
            try {
                resultDict = await this.executeTool(name, input);
                result = JSON.stringify(resultDict);
            }
            catch (error) {
                resultDict = { exception: 'Tool call timed out' };
                result = JSON.stringify(resultDict);
            }
        }
        const tool = toolsDict[name];
        return {
            role: conversation_entity_1.MessageRole.TOOL,
            tool_name: name,
            content: result,
            arguments: input,
            result_dict: resultDict,
            for_whom: tool.for_whom,
            tools: message.tools,
            tool_choice: message.tool_choice,
            message_uuid: this.generateUUID()
        };
    }
    async executeTool(name, input) {
        switch (name) {
            case 'test_function':
                return { result: `Test function called with: ${JSON.stringify(input)}` };
            case 'vector_search':
                return { result: 'Vector search results would appear here' };
            default:
                return { exception: `Unknown tool: ${name}` };
        }
    }
    async complete(conversation, maxTokens) {
        if (conversation.messages.length < 1) {
            return [conversation, 'unchanged'];
        }
        const systemPrompt = conversation.system;
        const messagesForBot = conversation.messages.filter(message => !(message.role === conversation_entity_1.MessageRole.TOOL && message.for_whom === 'user'));
        const lastMessage = conversation.messages[conversation.messages.length - 1];
        const messageDicts = messagesForBot.map(message => ({
            role: message.role,
            content: message.content
        }));
        if (lastMessage.role === conversation_entity_1.MessageRole.TOOL && lastMessage.for_whom === 'user') {
            return [conversation, 'unchanged'];
        }
        else if (lastMessage.role === conversation_entity_1.MessageRole.ASSISTANT) {
            const assistantMsg = lastMessage;
            if (assistantMsg.tools && assistantMsg.tool_call_id) {
                const newToolMsg = await this.callTool(assistantMsg);
                return [{ ...conversation, messages: [...conversation.messages, newToolMsg] }, 'changed'];
            }
            else {
                return [conversation, 'unchanged'];
            }
        }
        else {
            let tools = {};
            if (lastMessage.tools) {
                tools = {
                    tools: lastMessage.tools.map(tool => tool.llm_definition),
                    tool_choice: lastMessage.tool_choice
                };
            }
            const sdkArgs = {
                ...this.baseArgs,
                ...tools,
                system: systemPrompt,
                messages: messageDicts,
                max_tokens: maxTokens
            };
            const response = await this.getMessage(sdkArgs);
            const newMsg = {
                role: conversation_entity_1.MessageRole.ASSISTANT,
                content: response.text || '** Empty Message, tool call **',
                stop_reason: response.stop_reason,
                tools: lastMessage.tools,
                tool_choice: lastMessage.tool_choice,
                usage: response.input_usage + response.output_usage,
                model: response.model,
                message_uuid: this.generateUUID(),
                ...response.tool_call
            };
            return [{ ...conversation, messages: [...conversation.messages, newMsg] }, 'changed'];
        }
    }
    async spin(conversation, maxFuncCalls, sendFunc, maxTokens) {
        let calls = 0;
        let currentConvo = conversation;
        while (calls < maxFuncCalls) {
            const [newConvo, changed] = await this.complete(currentConvo, maxTokens);
            currentConvo = newConvo;
            await sendFunc(currentConvo);
            if (changed === 'unchanged') {
                return;
            }
            const lastMessage = currentConvo.messages[currentConvo.messages.length - 1];
            if (lastMessage.role === conversation_entity_1.MessageRole.ASSISTANT && lastMessage.tool_call_id) {
                calls++;
            }
        }
    }
    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
            const r = Math.random() * 16 | 0;
            const v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
}
exports.LLMInterface = LLMInterface;
let ClaudeInterface = class ClaudeInterface extends LLMInterface {
    constructor() {
        super();
        this.baseArgs = { model: 'claude-3-5-sonnet-20241022' };
        const apiKey = process.env.ANTHROPIC_API_KEY;
        if (!apiKey) {
            throw new Error('ANTHROPIC_API_KEY environment variable is required');
        }
        console.log('Initializing Anthropic client with API key:', apiKey.substring(0, 10) + '...');
        this.client = new sdk_1.default({
            apiKey: apiKey,
        });
    }
    async getMessage(args) {
        const response = await this.client.messages.create(args);
        let textBlock = null;
        let toolBlock = null;
        for (const block of response.content) {
            if ('input' in block) {
                toolBlock = block;
            }
            if ('text' in block) {
                textBlock = block;
            }
        }
        const toolCall = toolBlock ? {
            tool_call_id: toolBlock.id,
            tool_call_name: toolBlock.name,
            tool_call_input: toolBlock.input,
        } : {};
        return {
            text: textBlock?.text,
            tool_call: toolCall,
            stop_reason: response.stop_reason,
            input_usage: response.usage.input_tokens,
            output_usage: response.usage.output_tokens,
            model: this.baseArgs.model
        };
    }
    async tokenCount(conversation, newMessage) {
        const messagesForBot = conversation.messages.filter(message => !(message.role === conversation_entity_1.MessageRole.TOOL && message.for_whom === 'user'));
        const messages = messagesForBot.map(message => ({
            role: message.role,
            content: message.content
        }));
        if (newMessage) {
            messages.push({ role: conversation_entity_1.MessageRole.USER, content: newMessage });
        }
        const response = await this.client.messages.countTokens({
            ...this.baseArgs,
            system: conversation.system,
            messages
        });
        return response.input_tokens;
    }
};
exports.ClaudeInterface = ClaudeInterface;
exports.ClaudeInterface = ClaudeInterface = __decorate([
    (0, common_1.Injectable)(),
    __metadata("design:paramtypes", [])
], ClaudeInterface);
//# sourceMappingURL=llm.service.js.map