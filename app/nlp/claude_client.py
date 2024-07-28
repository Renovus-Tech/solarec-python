import os

from claude import claude_client, claude_wrapper

from app.nlp.llm_client import LLMClient


class ClaudeAIClient(LLMClient):
    ''' Claude Language Model '''

    def __init__(self):
        initial_prompt = os.environ.get("CLAUDE_INITIAL_PROMPT")
        session_key = os.environ.get("CLAUDE_SESSION_KEY")

        client = claude_client.ClaudeClient(session_key)
        organizations = client.get_organizations()
        self.claude = claude_wrapper.ClaudeWrapper(client, organization_uuid=organizations[0]['uuid'])

        self.conversation_data = self.claude.start_new_conversation("Claude Conversation", initial_prompt)
        self.conversation_uuid = self.conversation_data['uuid']

    def generate_text(self, prompt):
        ''' Generate text based on the prompt'''
        return self.claude.send_message(prompt, conversation_uuid=self.conversation_uuid)
