# BRIDGE MODULE KNOWLEDGE BASE

**Generated:** Sat Apr 04 2026
**Commit:** 4edbd9e
**Branch:** dev

## OVERVIEW
TypeScript bridge component for nanobot, providing cross-language interoperability and additional functionality not available in Python.

## STRUCTURE
```
./bridge/src/
├── index.ts           # Main entry point
├── server.ts          # Bridge server implementation
├── whatsapp.ts        # WhatsApp bridge functionality
└── types.ts           # TypeScript type definitions
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Modify bridge core functionality | `index.ts` | Main entry point and initialization |
| Update bridge server logic | `server.ts` | HTTP/WebSocket server implementation |
| Extend WhatsApp bridge | `whatsapp.ts` | WhatsApp messaging integration |
| Add new TypeScript types | `types.ts` | Shared type definitions |

## CONVENTIONS
- Uses TypeScript with ES Module syntax
- Build output goes to `dist/` directory
- Follows strict TypeScript type checking (no `any` types)
- All network operations use async/await
- Error handling uses standard Error classes with proper stack traces

## ANTI-PATTERNS
- Avoid `as any` type assertions unless absolutely necessary
- Don't commit built `dist/` files to version control
- Never hardcode API keys or secrets in source code
- Avoid blocking synchronous operations in server handlers
- Don't ignore error responses from Python core
