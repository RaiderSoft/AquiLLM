import { OnGatewayConnection, OnGatewayDisconnect } from '@nestjs/websockets';
import { Socket } from 'socket.io';
export declare class ChatGateway implements OnGatewayConnection, OnGatewayDisconnect {
    private llmInterface;
    private conversations;
    private tools;
    private collectionsRef;
    constructor();
    handleConnection(client: Socket): Promise<void>;
    handleDisconnect(client: Socket): void;
    handleChatAction(data: any, client: Socket): Promise<void>;
    private handleAppendMessage;
    private handleRateMessage;
    private generateUUID;
}
