export declare class AppendMessageDto {
    action: 'append';
    collections: number[];
    message: {
        content: string;
        role: 'user';
    };
}
export declare class RateMessageDto {
    action: 'rate';
    uuid: string;
    rating: number;
}
export type ChatActionDto = AppendMessageDto | RateMessageDto;
