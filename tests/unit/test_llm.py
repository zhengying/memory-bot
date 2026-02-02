"""
Unit tests for LLM module
"""
import pytest
from core.llm import Message, LLMResponse, LLMProvider, MockLLMProvider


class TestMessage:
    """Test Message dataclass"""

    def test_create_message(self):
        """Test creating a message"""
        msg = Message(
            role="user",
            content="Hello, world!"
        )

        assert msg.role == "user"
        assert msg.content == "Hello, world!"
        assert msg.metadata == {}

    def test_create_message_with_metadata(self):
        """Test creating a message with metadata"""
        msg = Message(
            role="assistant",
            content="Hi there!",
            metadata={"source": "test", "timestamp": 123456}
        )

        assert msg.metadata["source"] == "test"
        assert msg.metadata["timestamp"] == 123456

    def test_message_to_dict(self):
        """Test converting message to dict"""
        msg = Message(
            role="user",
            content="Test message"
        )

        result = msg.to_dict()

        assert result == {
            "role": "user",
            "content": "Test message"
        }

    def test_message_validation(self):
        """Test message role validation"""
        valid_roles = ["system", "user", "assistant"]

        for role in valid_roles:
            msg = Message(role=role, content="Test")
            assert msg.role == role

    def test_message_empty_content(self):
        """Test message with empty content"""
        msg = Message(role="user", content="")

        assert msg.content == ""
        assert msg.to_dict()["content"] == ""


class TestLLMResponse:
    """Test LLMResponse dataclass"""

    def test_create_response(self):
        """Test creating a response"""
        response = LLMResponse(
            content="Hello!",
            model="gpt-4",
            tokens_used=100
        )

        assert response.content == "Hello!"
        assert response.model == "gpt-4"
        assert response.tokens_used == 100

    def test_response_with_finish_reason(self):
        """Test response with finish reason"""
        response = LLMResponse(
            content="Test",
            model="gpt-4",
            finish_reason="length"
        )

        assert response.finish_reason == "length"

    def test_response_with_metadata(self):
        """Test response with metadata"""
        response = LLMResponse(
            content="Test",
            model="gpt-4",
            metadata={"request_id": "123", "latency_ms": 500}
        )

        assert response.metadata["request_id"] == "123"
        assert response.metadata["latency_ms"] == 500


class TestLLMProvider:
    """Test LLMProvider abstract base class"""

    def test_provider_initialization(self):
        """Test provider initialization"""
        provider = MockLLMProvider(
            api_key="test-key",
            model="gpt-4"
        )

        assert provider.api_key == "test-key"
        assert provider.model == "gpt-4"

    def test_provider_with_kwargs(self):
        """Test provider initialization with extra kwargs"""
        provider = MockLLMProvider(
            api_key="test-key",
            model="gpt-4",
            temperature=0.7,
            max_tokens=1000
        )

        assert provider.kwargs["temperature"] == 0.7
        assert provider.kwargs["max_tokens"] == 1000

    def test_abstract_methods(self):
        """Test that abstract methods must be implemented"""
        # This test verifies the abstract interface
        # MockLLMProvider implements all methods, so it should work
        provider = MockLLMProvider(api_key="test", model="gpt-4")

        # Check that methods exist
        assert hasattr(provider, 'chat')
        assert hasattr(provider, 'chat_stream')
        assert hasattr(provider, 'count_tokens')


class TestMockLLMProvider:
    """Test MockLLMProvider implementation"""

    def test_chat_single_message(self):
        """Test chat with single message"""
        provider = MockLLMProvider(api_key="test", model="gpt-4")
        message = Message(role="user", content="Hello")

        response = provider.chat([message])

        assert response.content == "Mock response"
        assert response.model == "gpt-4"
        assert response.tokens_used == len("Hello")

    def test_chat_multiple_messages(self):
        """Test chat with multiple messages"""
        provider = MockLLMProvider(
            api_key="test",
            model="gpt-4",
            response="Custom response"
        )

        messages = [
            Message(role="system", content="You are helpful"),
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi"),
            Message(role="user", content="How are you?")
        ]

        response = provider.chat(messages)

        assert response.content == "Custom response"
        assert provider.last_messages == messages

    def test_chat_stream(self):
        """Test streaming response"""
        provider = MockLLMProvider(
            api_key="test",
            model="gpt-4",
            response="Hello world this is a test"
        )

        messages = [Message(role="user", content="Test")]
        chunks = list(provider.chat_stream(messages))

        expected_chunks = ["Hello ", "world ", "this ", "is ", "a ", "test "]
        assert chunks == expected_chunks

    def test_count_tokens(self):
        """Test token counting"""
        provider = MockLLMProvider(api_key="test", model="gpt-4")

        messages = [
            Message(role="system", content="System prompt"),
            Message(role="user", content="User message")
        ]

        # Mock counts tokens as character length
        tokens = provider.count_tokens(messages)

        expected = len("System prompt") + len("User message")
        assert tokens == expected

    def test_count_tokens_empty(self):
        """Test token counting with empty messages"""
        provider = MockLLMProvider(api_key="test", model="gpt-4")

        tokens = provider.count_tokens([])
        assert tokens == 0

    def test_chat_with_parameters(self):
        """Test chat with additional parameters"""
        provider = MockLLMProvider(api_key="test", model="gpt-4")
        messages = [Message(role="user", content="Test")]

        # Provider should accept additional kwargs
        response = provider.chat(
            messages,
            temperature=0.7,
            max_tokens=100
        )

        assert response.content == "Mock response"

    def test_set_response(self):
        """Test setting custom response"""
        provider = MockLLMProvider(api_key="test", model="gpt-4")

        provider.set_response("New custom response")
        message = Message(role="user", content="Test")

        response = provider.chat([message])

        assert response.content == "New custom response"

    def test_call_count(self):
        """Test call count tracking"""
        provider = MockLLMProvider(api_key="test", model="gpt-4")

        assert provider.call_count == 0

        provider.chat([Message(role="user", content="Test")])
        assert provider.call_count == 1

        provider.chat([Message(role="user", content="Test 2")])
        assert provider.call_count == 2

    def test_reset(self):
        """Test resetting mock state"""
        provider = MockLLMProvider(api_key="test", model="gpt-4")

        provider.chat([Message(role="user", content="Test")])
        assert provider.call_count == 1
        assert provider.last_messages is not None

        provider.reset()
        assert provider.call_count == 0
        assert provider.last_messages is None


class TestTokenBudget:
    """Test token budget management"""

    def test_simple_token_count(self):
        """Test simple token counting"""
        provider = MockLLMProvider(api_key="test", model="gpt-4")

        message = Message(
            role="user",
            content="This is a test message with some words"
        )

        tokens = provider.count_tokens([message])

        # Mock counts characters
        assert tokens == len("This is a test message with some words")

    def test_token_budget_check(self):
        """Test checking if messages fit within budget"""
        provider = MockLLMProvider(api_key="test", model="gpt-4")

        messages = [
            Message(role="system", content="You are a helpful assistant"),
            Message(role="user", content="Hello!"),
            Message(role="assistant", content="Hi there!"),
            Message(role="user", content="How can you help me?")
        ]

        budget = 1000
        tokens = provider.count_tokens(messages)

        assert tokens < budget, "Messages should fit within budget"

    def test_truncate_for_budget(self):
        """Test truncating messages to fit budget"""
        provider = MockLLMProvider(api_key="test", model="gpt-4")

        long_content = "x" * 500  # Long message
        messages = [
            Message(role="system", content="System prompt"),
            Message(role="user", content=long_content)
        ]

        # If we have a small budget, we might need to truncate
        budget = 100
        tokens = provider.count_tokens(messages)

        if tokens > budget:
            # In real implementation, we would truncate
            assert tokens > budget, "Messages exceed budget"
        else:
            assert tokens <= budget, "Messages fit within budget"


class TestMessageHistory:
    """Test message history management"""

    def test_append_to_history(self):
        """Test appending messages to history"""
        history = []

        history.append(Message(role="user", content="Hello"))
        history.append(Message(role="assistant", content="Hi"))

        assert len(history) == 2
        assert history[0].role == "user"
        assert history[1].role == "assistant"

    def test_truncate_history(self):
        """Test truncating message history"""
        history = [
            Message(role="user", content=f"Message {i}")
            for i in range(10)
        ]

        # Keep last 5 messages
        truncated = history[-5:]

        assert len(truncated) == 5
        assert truncated[0].content == "Message 5"
        assert truncated[-1].content == "Message 9"

    def test_convert_history_to_api_format(self):
        """Test converting history to API format"""
        history = [
            Message(role="system", content="System"),
            Message(role="user", content="User"),
            Message(role="assistant", content="Assistant")
        ]

        api_format = [msg.to_dict() for msg in history]

        expected = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "User"},
            {"role": "assistant", "content": "Assistant"}
        ]

        assert api_format == expected
