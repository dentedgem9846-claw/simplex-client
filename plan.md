# SimpleX Chat Python Client Library — Implementation Plan

## Library Architecture Overview

The library wraps the SimpleX Chat CLI WebSocket API in a typed, async-first Python client.

```
┌─────────────────────────────────────────────────┐
│                  Application                    │
├─────────────────────────────────────────────────┤
│  SimplexClient (client.py)                      │
│    - async context manager                      │
│    - send_command(cmd) with corrId correlation  │
│    - on_event() callback registration           │
│    - high-level API methods                     │
├─────────────────────────────────────────────────┤
│  Commands (commands.py)                         │
│    - Command string builders                    │
├─────────────────────────────────────────────────┤
│  Events (events.py)                             │
│    - Event type discriminated unions            │
├─────────────────────────────────────────────────┤
│  Types (types.py)                               │
│    - Pydantic models for all API types          │
├─────────────────────────────────────────────────┤
│  Exceptions (exceptions.py)                     │
│    - SimplexError, ConnectionError              │
├─────────────────────────────────────────────────┤
│  websockets (transport)                         │
└─────────────────────────────────────────────────┘
```

### Key Design Decisions

- **corrId correlation**: Monotonic integer counter, stored in a dict mapping corrId → asyncio.Future. Response dispatch loop resolves the matching future.
- **Event dispatch**: Callbacks registered via `on_event(event_type, callback)`. Unknown events are logged and ignored.
- **Reconnection**: Exponential backoff with jitter (1s → 30s cap).
- **Pydantic models**: All types use `model_config = ConfigDict(extra="ignore")` to tolerate unknown fields (as required by the API spec).
- **Discriminated unions**: Use Pydantic's `Discriminator` with `type` field tags.

## Commands to Implement

### User/Profile
- `ShowActiveUser` → `/user`
- `CreateActiveUser` → `/_create user <json>`
- `ListUsers` → `/users`
- `APISetActiveUser` → `/_user <userId>`
- `APIDeleteUser` → `/_delete user <userId> del_smp=on|off`
- `APIUpdateProfile` → `/_profile <userId> <json>`

### Address
- `APICreateMyAddress` → `/_address <userId>`
- `APIDeleteMyAddress` → `/_delete_address <userId>`
- `APIShowMyAddress` → `/_show_address <userId>`
- `APISetProfileAddress` → `/_profile_address <userId> on|off`
- `APISetAddressSettings` → `/_address_settings <userId> <json>`

### Connection
- `APIAddContact` → `/_connect <userId>`
- `APIConnect` → `/_connect <userId> <link>`
- `APIConnectPlan` → `/_connect plan <userId> <link>`
- `APIAcceptContact` → `/_accept <contactReqId>`
- `APIRejectContact` → `/_reject <contactReqId>`

### Contacts/Chats
- `APIListContacts` → `/_contacts <userId>`
- `APIListGroups` → `/_groups <userId>`
- `APIDeleteChat` → `/_delete <chatRef> <mode>`
- `APISetContactPrefs` → `/_set prefs @<contactId> <json>`

### Messages
- `APISendMessages` → `/_send <chatRef> json <json>`
- `APIUpdateChatItem` → `/_update item <chatRef> <itemId> json <json>`
- `APIDeleteChatItem` → `/_delete item <chatRef> <ids> <mode>`
- `APIDeleteMemberChatItem` → `/_delete member item #<groupId> <ids>`
- `APIChatItemReaction` → `/_reaction <chatRef> <itemId> on|off <json>`

### Groups
- `APINewGroup` → `/_group <userId> <json>`
- `APIUpdateGroupProfile` → `/_group_profile #<groupId> <json>`
- `APIAddMember` → `/_add #<groupId> <contactId> <role>`
- `APIJoinGroup` → `/_join #<groupId>`
- `APIAcceptMember` → `/_accept member #<groupId> <memberId> <role>`
- `APIMembersRole` → `/_member role #<groupId> <ids> <role>`
- `APIBlockMembersForAll` → `/_block #<groupId> <ids> blocked=on|off`
- `APIRemoveMembers` → `/_remove #<groupId> <ids>`
- `APILeaveGroup` → `/_leave #<groupId>`
- `APIListMembers` → `/_members #<groupId>`

### Group Links
- `APICreateGroupLink` → `/_create link #<groupId> <role>`
- `APIGroupLinkMemberRole` → `/_set link role #<groupId> <role>`
- `APIDeleteGroupLink` → `/_delete link #<groupId>`
- `APIGetGroupLink` → `/_get link #<groupId>`

### Files
- `ReceiveFile` → `/freceive <fileId>`
- `CancelFile` → `/fcancel <fileId>`

## Events to Handle

### Contact/Connection
- `contactConnected`
- `contactUpdated`
- `contactDeletedByContact`
- `receivedContactRequest`
- `contactSndReady`
- `acceptingContactRequest`
- `contactConnecting`

### Messages
- `newChatItems`
- `chatItemReaction`
- `chatItemsDeleted`
- `chatItemUpdated`
- `chatItemsStatusesUpdated`

### Groups
- `receivedGroupInvitation`
- `userJoinedGroup`
- `groupUpdated`
- `joinedGroupMember`
- `memberRole`
- `deletedMember`
- `leftMember`
- `deletedMemberUser`
- `groupDeleted`
- `connectedToGroupMember`
- `memberAcceptedByOther`
- `memberBlockedForAll`
- `groupMemberUpdated`

### Files
- `rcvFileDescrReady`
- `rcvFileComplete`
- `sndFileCompleteXFTP`
- `rcvFileStart`
- `rcvFileSndCancelled`
- `rcvFileAccepted`
- `rcvFileError`
- `sndFileError`

### System
- `messageError`
- `chatError`
- `chatErrors`

## Types to Define

### Core
- `MsgContent` (discriminated union)
- `ComposedMessage`
- `UpdatedMessage`
- `ChatRef`
- `ChatType` (enum)
- `CIDeleteMode` (enum)
- `MsgReaction`

### Chat Items
- `AChatItem`
- `ChatItem`
- `CIMeta`
- `CIDirection`
- `CIStatus`
- `CIContent`
- `CIFile`
- `CIFileStatus`
- `CITimed`
- `CIDeleted`
- `CIQuote`
- `CIReactionCount`
- `ChatItemDeletion`

### User/Contact
- `User`
- `UserInfo`
- `NewUser`
- `Profile`
- `LocalProfile`
- `Contact`
- `UserContactRequest`
- `UserContactLink`
- `AddressSettings`
- `AutoAccept`

### Groups
- `GroupInfo`
- `GroupProfile`
- `GroupMember`
- `GroupMemberRole` (enum)
- `GroupLink`
- `GroupSummary`

### Connection
- `CreatedConnLink`
- `Connection`
- `ConnectionPlan`

### Files
- `CryptoFile`
- `FileTransferMeta`
- `RcvFileTransfer`

### Errors
- `ChatError`

## Testing Strategy

### Unit Tests
- `test_types.py` — Pydantic model parsing from JSON fixtures
- `test_commands.py` — Command string building
- `test_events.py` — Event parsing and dispatch
- `test_client.py` — Client logic with mocked WebSocket

### Integration Tests
- `test_integration.py` — Two SimpleX CLI containers exchanging messages via pytest-docker

## Implementation Order

1. `exceptions.py` — Error types
2. `types.py` — Pydantic models
3. `events.py` — Event parsing
4. `commands.py` — Command builders
5. `client.py` — WebSocket client
6. `__init__.py` — Public API
7. Unit tests
8. Integration test infrastructure (Dockerfile, docker-compose, conftest)
9. Integration tests
