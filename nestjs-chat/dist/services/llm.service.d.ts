import { Conversation, LLMResponse, AssistantMessage, ToolMessage } from '../entities/conversation.entity';
export declare abstract class LLMInterface {
    protected baseArgs: Record<string, any>;
    protected client: any;
    abstract getMessage(args: any): Promise<LLMResponse>;
    abstract tokenCount(conversation: Conversation, newMessage?: string): Promise<number>;
    callTool(message: AssistantMessage): Promise<ToolMessage>;
    private executeTool;
    complete(conversation: Conversation, maxTokens: number): Promise<[Conversation, 'changed' | 'unchanged']>;
    spin(conversation: Conversation, maxFuncCalls: number, sendFunc: (convo: Conversation) => Promise<void>, maxTokens: number): Promise<void>;
    private generateUUID;
}
export declare class ClaudeInterface extends LLMInterface {
    protected baseArgs: {
        model: string;
    };
    constructor();
    getMessage(args: any): Promise<LLMResponse>;
    tokenCount(conversation: Conversation, newMessage?: string): Promise<number>;
}
