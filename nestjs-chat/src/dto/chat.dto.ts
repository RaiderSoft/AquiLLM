import { IsString, IsOptional, IsArray, IsNumber, IsEnum } from 'class-validator';

export class AppendMessageDto {
  @IsString()
  action: 'append';

  @IsArray()
  @IsNumber({}, { each: true })
  collections: number[];

  message: {
    content: string;
    role: 'user';
  };
}

export class RateMessageDto {
  @IsString()
  action: 'rate';

  @IsString()
  uuid: string;

  @IsNumber()
  rating: number;
}

export type ChatActionDto = AppendMessageDto | RateMessageDto;