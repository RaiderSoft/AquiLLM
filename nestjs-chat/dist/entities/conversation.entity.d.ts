export declare enum MessageRole {
    USER = "user",
    ASSISTANT = "assistant",
    TOOL = "tool"
}
export declare enum ToolChoiceType {
    AUTO = "auto",
    ANY = "any",
    TOOL = "tool"
}
export interface ToolChoice {
    type: ToolChoiceType;
    name?: string;
}
export interface ToolResultDict {
    exception?: string;
    result?: any;
}
export interface LLMToolDefinition {
    name: string;
    description: string;
    input_schema: {
        type: string;
        properties: Record<string, any>;
        required: string[];
    };
}
export declare class LLMTool {
    llm_definition: LLMToolDefinition;
    for_whom: 'user' | 'assistant';
    constructor(definition: LLMToolDefinition, for_whom: 'user' | 'assistant');
    get name(): string;
}
export interface BaseMessage {
    role: MessageRole;
    content: string;
    tools?: LLMTool[];
    tool_choice?: ToolChoice;
    rating?: number;
    message_uuid: string;
}
export interface UserMessage extends BaseMessage {
    role: MessageRole.USER;
}
export interface ToolMessage extends BaseMessage {
    role: MessageRole.TOOL;
    tool_name: string;
    arguments?: Record<string, any>;
    for_whom: 'assistant' | 'user';
    result_dict: ToolResultDict;
}
export interface AssistantMessage extends BaseMessage {
    role: MessageRole.ASSISTANT;
    model?: string;
    stop_reason: string;
    tool_call_id?: string;
    tool_call_name?: string;
    tool_call_input?: Record<string, any>;
    usage: number;
}
export type LLMMessage = UserMessage | ToolMessage | AssistantMessage;
export interface Conversation {
    system: string;
    messages: LLMMessage[];
}
export interface LLMResponse {
    text?: string;
    tool_call?: Record<string, any>;
    stop_reason: string;
    input_usage: number;
    output_usage: number;
    model?: string;
}
