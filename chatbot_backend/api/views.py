from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import ChatSession, ChatMessage
from .serializers import (
    ChatSessionSerializer,
    ChatMessageSerializer,
    ChatRequestSerializer,
    ChatResponseSerializer,
)
from .openai_client import OpenAIClient, OpenAIClientError


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def health(request):
    """
    PUBLIC_INTERFACE
    Health check endpoint.

    Returns:
        200 OK with simple status message.
    """
    return Response({"message": "Server is up!"})


@swagger_auto_schema(
    method="post",
    operation_id="create_or_continue_chat",
    operation_summary="Send a user message and receive assistant reply",
    operation_description="Creates a new chat session if session_id not provided, else continues the existing one.",
    request_body=ChatRequestSerializer,
    responses={200: ChatResponseSerializer},
    tags=["chat"],
)
@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def chat(request):
    """
    PUBLIC_INTERFACE
    Chat endpoint. Accepts a user message, calls OpenAI, persists messages, and returns the assistant reply.

    Body:
        - session_id (optional UUID): existing session to continue
        - message (str): user input

    Returns:
        200 OK with session_id, reply, and message_id.
    """
    serializer = ChatRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    session_id = serializer.validated_data.get("session_id")
    message_text = serializer.validated_data["message"].strip()

    if not message_text:
        return Response({"detail": "Message cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)

    if session_id:
        session = get_object_or_404(ChatSession, id=session_id)
    else:
        session = ChatSession.objects.create(title=message_text[:40])

    # store user message
    ChatMessage.objects.create(session=session, role=ChatMessage.ROLE_USER, content=message_text)

    # Prepare messages history
    history = [{"role": m.role, "content": m.content} for m in session.messages.all()]

    try:
        client = OpenAIClient()
        reply = client.chat(history)
    except OpenAIClientError as e:
        # roll back user message? keeping for audit but informing error
        return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

    # store assistant reply
    assistant_msg = ChatMessage.objects.create(
        session=session, role=ChatMessage.ROLE_ASSISTANT, content=reply
    )

    response = ChatResponseSerializer(
        {"session_id": str(session.id), "reply": reply, "message_id": assistant_msg.id}
    ).data
    return Response(response, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method="post",
    operation_id="create_session",
    operation_summary="Create a new empty chat session",
    responses={201: ChatSessionSerializer},
    tags=["sessions"],
)
@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def create_session(request):
    """
    PUBLIC_INTERFACE
    Create a new chat session without any messages.

    Returns:
        201 Created with session details.
    """
    session = ChatSession.objects.create()
    return Response(ChatSessionSerializer(session).data, status=status.HTTP_201_CREATED)


@swagger_auto_schema(
    method="get",
    operation_id="list_sessions",
    operation_summary="List all chat sessions",
    responses={200: ChatSessionSerializer(many=True)},
    tags=["sessions"],
)
@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def list_sessions(request):
    """
    PUBLIC_INTERFACE
    List all chat sessions.

    Returns:
        200 OK with list of sessions.
    """
    qs = ChatSession.objects.all().order_by("-updated_at")
    return Response(ChatSessionSerializer(qs, many=True).data, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method="get",
    operation_id="get_session",
    operation_summary="Get a chat session by ID",
    manual_parameters=[
        openapi.Parameter("session_id", openapi.IN_PATH, type=openapi.TYPE_STRING, description="Session UUID"),
    ],
    responses={200: ChatSessionSerializer},
    tags=["sessions"],
)
@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def get_session(request, session_id):
    """
    PUBLIC_INTERFACE
    Retrieve a chat session including its messages.

    Path params:
        session_id: UUID of the session

    Returns:
        200 OK with session details.
    """
    session = get_object_or_404(ChatSession, id=session_id)
    return Response(ChatSessionSerializer(session).data, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method="delete",
    operation_id="delete_session",
    operation_summary="Delete a chat session by ID",
    manual_parameters=[
        openapi.Parameter("session_id", openapi.IN_PATH, type=openapi.TYPE_STRING, description="Session UUID"),
    ],
    responses={204: "Deleted"},
    tags=["sessions"],
)
@api_view(["DELETE"])
@permission_classes([permissions.AllowAny])
def delete_session(request, session_id):
    """
    PUBLIC_INTERFACE
    Delete a chat session and all its messages.

    Returns:
        204 No Content on success.
    """
    session = get_object_or_404(ChatSession, id=session_id)
    session.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@swagger_auto_schema(
    method="get",
    operation_id="list_messages",
    operation_summary="List messages for a session",
    manual_parameters=[
        openapi.Parameter("session_id", openapi.IN_PATH, type=openapi.TYPE_STRING, description="Session UUID"),
    ],
    responses={200: ChatMessageSerializer(many=True)},
    tags=["messages"],
)
@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def list_messages(request, session_id):
    """
    PUBLIC_INTERFACE
    List messages for a given session.

    Returns:
        200 OK with list of messages.
    """
    session = get_object_or_404(ChatSession, id=session_id)
    msgs = session.messages.all()
    return Response(ChatMessageSerializer(msgs, many=True).data, status=status.HTTP_200_OK)
