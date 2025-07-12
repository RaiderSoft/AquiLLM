# Test Prompts to Verify Full Functionality

## 1. Basic LLM Functionality Test
**Prompt**: "Hi there! Can you tell me a bit about yourself?"
**Expected**: Claude responds with information about being an AI assistant
**Verifies**: ✅ Real Claude API calls working

## 2. Tool Calling Test (Dummy Tools)
**Prompt**: "Can you search for information about machine learning in the documents?"
**Expected**: Claude should attempt to use the vector_search tool and get a dummy response
**Verifies**: ✅ Tool calling system working with dummy implementations

## 3. Test Function Tool Test
**Prompt**: "Can you use the test function with the strings ['hello', 'world', 'test']?"
**Expected**: Claude calls test_function and returns dummy result
**Verifies**: ✅ Specific tool implementation

## 4. Document Tools Test
**Prompt**: "What documents are available? Can you show me their IDs?"
**Expected**: Claude tries document_ids tool, gets dummy response
**Verifies**: ✅ Document-related dummy tools

## 5. Conversation Memory Test
**Prompt Sequence**:
1. "My name is John and I'm working on a project about renewable energy"
2. "What did I just tell you about my project?"
**Expected**: Claude remembers the context from message 1
**Verifies**: ✅ Conversation state management

## 6. Error Handling Test
**Action**: Temporarily break the API key in .env and restart
**Expected**: Clear error message about authentication
**Verifies**: ✅ Error handling

## 7. WebSocket Features Test
**Actions**:
- Send multiple messages rapidly
- Disconnect and reconnect browser
- Rate a message (if rating UI added)
**Expected**: All work smoothly
**Verifies**: ✅ WebSocket stability

## 8. Tool Chain Test
**Prompt**: "I need to find information about neural networks. First search for it, then if you find a relevant document, get more context about it."
**Expected**: Claude attempts multiple tool calls in sequence
**Verifies**: ✅ Tool chaining and conversation spinning

## Quick Verification Commands

Test these prompts in order and verify:

1. ✅ **LLM Response**: "Hello! How are you today?"
2. ✅ **Tool Calling**: "Search for 'artificial intelligence' in the documents"
3. ✅ **Memory**: "My favorite color is blue" → "What's my favorite color?"
4. ✅ **Complex Task**: "Find information about Python programming and summarize what you find"

## Expected Behavior Summary

- **Real Claude responses**: Natural, helpful, contextual
- **Tool calls**: Attempts to use tools, gets dummy responses, continues conversation
- **Memory**: Maintains conversation context across messages
- **Errors**: Graceful error handling with user-friendly messages
- **WebSocket**: Smooth real-time communication