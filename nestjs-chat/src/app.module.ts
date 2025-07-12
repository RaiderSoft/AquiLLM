import { Module } from '@nestjs/common';
import { ChatGateway } from './gateways/chat.gateway';
import { ClaudeInterface } from './services/llm.service';

@Module({
  imports: [],
  controllers: [],
  providers: [ChatGateway, ClaudeInterface],
})
export class AppModule {}