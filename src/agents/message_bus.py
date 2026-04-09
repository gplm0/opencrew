"""Message Bus - Inter-agent communication system"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import json


class MessageType(str, Enum):
    """Types of messages between agents"""
    TASK_ASSIGN = "task_assign"
    TASK_COMPLETE = "task_complete"
    TASK_FAILED = "task_failed"
    PROGRESS_UPDATE = "progress_update"
    BLOCKER = "blocker"
    BLOCKER_RESOLVED = "blocker_resolved"
    STATUS_REQUEST = "status_request"
    STATUS_RESPONSE = "status_response"
    HELP_REQUEST = "help_request"
    HELP_RESPONSE = "help_response"
    RESULT = "result"
    VISION_REQUEST = "vision_request"
    VISION_RESPONSE = "vision_response"
    AGENT_SPAWN = "agent_spawn"
    AGENT_DESPAWN = "agent_despawn"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    LOG = "log"


@dataclass
class Message:
    """A message between agents"""
    type: MessageType
    sender: str
    recipient: str  # "broadcast" for all agents
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    reply_to: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "sender": self.sender,
            "recipient": self.recipient,
            "content": self.content,
            "metadata": self.metadata,
            "message_id": self.message_id,
            "timestamp": self.timestamp.isoformat(),
            "reply_to": self.reply_to,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        return cls(
            type=MessageType(data["type"]),
            sender=data["sender"],
            recipient=data["recipient"],
            content=data["content"],
            metadata=data.get("metadata", {}),
            message_id=data.get("message_id", str(uuid.uuid4())),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            reply_to=data.get("reply_to"),
        )

    def reply(self, type: MessageType, content: str, metadata: Optional[Dict] = None) -> "Message":
        """Create a reply message to this message"""
        return Message(
            type=type,
            sender=self.recipient,
            recipient=self.sender,
            content=content,
            metadata=metadata or {},
            reply_to=self.message_id,
        )


class MessageBus:
    """Async pub/sub message bus for inter-agent communication"""

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._agent_channels: Dict[str, List[Callable]] = {}
        self._message_log: List[Message] = []
        self._max_log_size = 10000
        self._lock = asyncio.Lock()

    async def subscribe(self, message_type: MessageType, callback: Callable):
        """Subscribe to a specific message type"""
        async with self._lock:
            if message_type.value not in self._subscribers:
                self._subscribers[message_type.value] = []
            self._subscribers[message_type.value].append(callback)

    async def unsubscribe(self, message_type: MessageType, callback: Callable):
        """Unsubscribe from a message type"""
        async with self._lock:
            if message_type.value in self._subscribers:
                self._subscribers[message_type.value] = [
                    cb for cb in self._subscribers[message_type.value] if cb != callback
                ]

    async def register_agent(self, agent_id: str, callback: Callable):
        """Register an agent to receive direct messages"""
        async with self._lock:
            if agent_id not in self._agent_channels:
                self._agent_channels[agent_id] = []
            self._agent_channels[agent_id].append(callback)

    async def unregister_agent(self, agent_id: str, callback: Callable):
        """Unregister an agent"""
        async with self._lock:
            if agent_id in self._agent_channels:
                self._agent_channels[agent_id] = [
                    cb for cb in self._agent_channels[agent_id] if cb != callback
                ]

    async def publish(self, message: Message):
        """Publish a message to the bus"""
        async with self._lock:
            # Log message
            self._message_log.append(message)
            if len(self._message_log) > self._max_log_size:
                self._message_log = self._message_log[-self._max_log_size:]

        # Notify type subscribers
        subscribers = self._subscribers.get(message.type.value, [])
        for callback in subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(message)
                else:
                    callback(message)
            except Exception as e:
                print(f"[MessageBus] Error in subscriber: {e}")

        # Notify direct recipients
        if message.recipient != "broadcast":
            agent_callbacks = self._agent_channels.get(message.recipient, [])
            for callback in agent_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(message)
                    else:
                        callback(message)
                except Exception as e:
                    print(f"[MessageBus] Error delivering to agent {message.recipient}: {e}")

    async def send_to(self, recipient: str, sender: str, message_type: MessageType,
                      content: str, metadata: Optional[Dict] = None):
        """Send a direct message to an agent"""
        msg = Message(
            type=message_type,
            sender=sender,
            recipient=recipient,
            content=content,
            metadata=metadata or {},
        )
        await self.publish(msg)
        return msg

    async def broadcast(self, sender: str, message_type: MessageType,
                        content: str, metadata: Optional[Dict] = None):
        """Broadcast a message to all agents"""
        msg = Message(
            type=message_type,
            sender=sender,
            recipient="broadcast",
            content=content,
            metadata=metadata or {},
        )
        await self.publish(msg)
        return msg

    def get_messages(self, limit: int = 100, agent_id: Optional[str] = None) -> List[Message]:
        """Get recent messages, optionally filtered by agent"""
        messages = self._message_log[-limit:]
        if agent_id:
            messages = [
                m for m in messages
                if m.sender == agent_id or m.recipient == agent_id or m.recipient == "broadcast"
            ]
        return messages

    def get_message_log(self) -> List[Message]:
        """Get full message log"""
        return self._message_log.copy()

    async def clear(self):
        """Clear all subscriptions and messages"""
        async with self._lock:
            self._subscribers.clear()
            self._agent_channels.clear()
            self._message_log.clear()
