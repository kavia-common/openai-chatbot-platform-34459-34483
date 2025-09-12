from django.db import models
from django.utils import timezone
import uuid


class ChatSession(models.Model):
    """
    ChatSession represents a conversation thread.
    Optional user association can be added later if authentication is implemented.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.title or 'Session'} ({self.id})"


class ChatMessage(models.Model):
    """
    ChatMessage stores both user and assistant messages in a session.
    role: 'user' or 'assistant'
    """
    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"

    ROLE_CHOICES = (
        (ROLE_USER, "User"),
        (ROLE_ASSISTANT, "Assistant"),
    )

    id = models.BigAutoField(primary_key=True)
    session = models.ForeignKey(ChatSession, related_name="messages", on_delete=models.CASCADE)
    role = models.CharField(max_length=16, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"[{self.role}] {self.content[:30]}..."
