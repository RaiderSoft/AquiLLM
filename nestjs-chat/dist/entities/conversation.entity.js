"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.LLMTool = exports.ToolChoiceType = exports.MessageRole = void 0;
var MessageRole;
(function (MessageRole) {
    MessageRole["USER"] = "user";
    MessageRole["ASSISTANT"] = "assistant";
    MessageRole["TOOL"] = "tool";
})(MessageRole || (exports.MessageRole = MessageRole = {}));
var ToolChoiceType;
(function (ToolChoiceType) {
    ToolChoiceType["AUTO"] = "auto";
    ToolChoiceType["ANY"] = "any";
    ToolChoiceType["TOOL"] = "tool";
})(ToolChoiceType || (exports.ToolChoiceType = ToolChoiceType = {}));
class LLMTool {
    constructor(definition, for_whom) {
        this.llm_definition = definition;
        this.for_whom = for_whom;
    }
    get name() {
        return this.llm_definition.name;
    }
}
exports.LLMTool = LLMTool;
//# sourceMappingURL=conversation.entity.js.map