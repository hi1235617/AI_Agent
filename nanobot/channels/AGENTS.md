# CHANNELS MODULE KNOWLEDGE BASE

**Generated:** Sat Apr 04 2026
**Commit:** 4edbd9e
**Branch:** dev

## OVERVIEW
Messaging channel implementations for nanobot. Supports multiple platforms including DingTalk, Feishu, Telegram, Slack, WeChat, Email, and Matrix.

## STRUCTURE
```
./nanobot/channels/
├── base.py            # BaseChannel abstract class
├── dingtalk.py        # DingTalk channel implementation
├── feishu.py          # Feishu/Lark channel implementation
├── telegram.py        # Telegram channel implementation
├── slack.py           # Slack channel implementation
├── wechat.py          # WeChat channel implementation
├── email.py           # Email channel implementation
├── matrix.py          # Matrix channel implementation
└── __init__.py
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Add new messaging channel | Create new file extending `BaseChannel` from base.py | Follow existing channel patterns |
| Fix channel-specific issues | Corresponding channel file | e.g., `feishu.py` for Feishu bugs |
| Modify shared channel logic | `base.py` | Base class with common functionality |
| Update message formatting | Channel-specific implementation files | Each channel handles markdown conversion separately |

## CONVENTIONS
- All channels extend the abstract `BaseChannel` class
- Required methods: `__init__`, `send_message`, `start_listening`
- All network operations are async/await
- Message payloads use Pydantic models for validation
- Error handling standard: raise ChannelError for platform-specific issues

## ANTI-PATTERNS
- Don't implement channel-specific business logic in the core agent
- Avoid blocking network calls in message handlers
- Never hardcode API keys or secrets in channel implementations
- Don't modify message content without proper escaping for the target platform
