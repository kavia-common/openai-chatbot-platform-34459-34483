from rest_framework import serializers
from .models import ChatSession, ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "role", "content", "created_at"]


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = ["id", "title", "created_at", "updated_at", "messages"]


class ChatRequestSerializer(serializers.Serializer):
    # PUBLIC_INTERFACE
    def validate(self, data):
        """Validate message input payload."""
        return data

    session_id = serializers.UUIDField(required=False, allow_null=True, help_text="Existing session ID to continue chat.")
    message = serializers.CharField(help_text="User message to send to the assistant.")


class ChatResponseSerializer(serializers.Serializer):
    # PUBLIC_INTERFACE
    def validate(self, data):
        """Validate chat response payload."""
        return data

    session_id = serializers.UUIDField(help_text="Session ID of the conversation.")
    reply = serializers.CharField(help_text="Assistant response.")
    message_id = serializers.IntegerField(help_text="Stored assistant message ID.")
