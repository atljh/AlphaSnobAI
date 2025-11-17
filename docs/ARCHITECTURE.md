# AlphaSnobAI v3.0 - Architecture Documentation

## 🎯 Architecture Overview

AlphaSnobAI v3.0 follows **Domain-Driven Design (DDD)** principles with **Clean Architecture** patterns.

```
┌─────────────────────────────────────────────────────────────────┐
│                     Presentation Layer                          │
│                  (CLI, GUI, API Endpoints)                      │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              Application Layer                             │ │
│  │         (Use Cases, Commands, Queries)                     │ │
│  │                                                             │ │
│  │  ┌───────────────────────────────────────────────────────┐ │ │
│  │  │             Domain Layer                               │ │ │
│  │  │      (Entities, Value Objects, Services)               │ │ │
│  │  │                                                         │ │ │
│  │  │  - Pure business logic                                 │ │ │
│  │  │  - No dependencies on outer layers                     │ │ │
│  │  │  - Framework agnostic                                  │ │ │
│  │  └───────────────────────────────────────────────────────┘ │ │
│  │                                                             │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  Infrastructure Layer                                          │
│  (Database, Telegram, LLM, Config, Logging)                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🏛️ Layer Responsibilities

### 1. Domain Layer (`src/alphasnob/domain/`)

**Purpose:** Pure business logic, no external dependencies

**Components:**
- **Entities** - Objects with identity (User, Message, Persona)
- **Value Objects** - Immutable objects defined by attributes (UserId, Probability, Temperature)
- **Domain Services** - Business logic that doesn't belong to entities (DecisionEngine)
- **Domain Events** - Facts about what happened (MessageReceived, MessageSent)
- **Repository Interfaces** - Ports for data access (Protocol)

**Domains:**
- `messaging/` - Messages and chats
- `users/` - User profiles and relationships
- `ai/` - LLM and personas
- `decisions/` - Response decision logic
- `learning/` - Owner style learning
- `shared/` - Shared kernel (base classes, errors)

**Rules:**
- ✅ Can import from other domain modules
- ✅ Can use Python standard library
- ❌ Cannot import from application, infrastructure, or presentation layers
- ❌ Cannot depend on frameworks (SQLAlchemy, Pydantic Settings, etc.)

### 2. Application Layer (`src/alphasnob/application/`)

**Purpose:** Use cases and application logic orchestration

**Components:**
- **Commands** - Write operations (CQRS)
- **Queries** - Read operations (CQRS)
- **Application Services** - Orchestrate multiple operations
- **DTOs** - Data transfer objects for layer communication

**Rules:**
- ✅ Can import from domain layer
- ✅ Uses domain repository interfaces (not implementations)
- ❌ Cannot import from infrastructure or presentation layers
- ❌ Cannot access database directly

**Patterns:**
- **CQRS** - Separate read and write models
- **Result Monads** - Railway-oriented programming
- **Command/Query Handlers** - Single responsibility

### 3. Infrastructure Layer (`src/alphasnob/infrastructure/`)

**Purpose:** External concerns and technical implementation

**Components:**
- **Persistence** - Database implementation (SQLAlchemy)
- **Telegram** - Telegram client wrapper
- **LLM** - LLM provider implementations
- **Config** - Configuration management
- **Logging** - Structured logging
- **DI** - Dependency injection container

**Rules:**
- ✅ Implements domain repository interfaces
- ✅ Can depend on external frameworks
- ✅ Can import from domain and application layers
- ❌ Domain layer cannot import from infrastructure

**Patterns:**
- **Repository Pattern** - Data access abstraction
- **Adapter Pattern** - External service adapters
- **Factory Pattern** - Object creation

### 4. Presentation Layer (`src/alphasnob/presentation/`)

**Purpose:** User interfaces and external APIs

**Components:**
- **CLI** - Command-line interface (Typer)
- **GUI** - Desktop application (PySide6)

**Rules:**
- ✅ Can import from all other layers
- ✅ Receives injected dependencies
- ❌ Should not contain business logic

---

## 🔀 CQRS Pattern

### Command Flow (Write Operations)

```
User Action
    ↓
Command (immutable)
    ↓
CommandHandler
    ↓
Domain Entities (business logic)
    ↓
Repository Save
    ↓
Database
```

**Example:**

```python
# Command
class ProcessIncomingMessageCommand(Command):
    message_id: int
    chat_id: int
    text: str

# Handler
class ProcessIncomingMessageCommandHandler(CommandHandler[UUID]):
    async def handle(self, command) -> Result[UUID, Exception]:
        # 1. Create domain entity
        message = Message(...)

        # 2. Apply business rules
        user_profile.record_interaction()

        # 3. Persist changes
        await self.repository.save(message)

        # 4. Return result
        return Success(message.id)
```

### Query Flow (Read Operations)

```
User Request
    ↓
Query (immutable)
    ↓
QueryHandler
    ↓
Repository Query
    ↓
Database
    ↓
DTO (Data Transfer Object)
```

**Example:**

```python
# Query
class GetMessageHistoryQuery(Query):
    chat_id: int
    limit: int = 50

# Handler
class GetMessageHistoryQueryHandler(QueryHandler[list[MessageDTO]]):
    async def handle(self, query) -> Result[list[MessageDTO], Exception]:
        # 1. Query repository
        messages = await self.repository.find_recent_in_chat(...)

        # 2. Convert to DTOs
        dtos = [MessageDTO.from_entity(msg) for msg in messages]

        # 3. Return result
        return Success(dtos)
```

---

## 🎭 Domain Models

### Entity vs Value Object

**Entity:**
- Has unique identity (UUID)
- Mutable
- Defined by ID, not attributes
- Examples: User, Message, Persona

**Value Object:**
- No identity
- Immutable (frozen=True)
- Defined by attributes
- Examples: UserId, Probability, Temperature

**Domain Service:**
- Stateless
- Operates on multiple entities
- Business logic that doesn't belong to one entity
- Example: DecisionEngine

---

## 🔌 Dependency Injection

### Container Configuration

```python
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    # Config
    config = providers.Singleton(get_settings)

    # Database
    database = providers.Singleton(
        Database,
        database_url=config.provided.paths.database
    )

    # Repositories
    user_repository = providers.Factory(
        SQLAlchemyUserProfileRepository,
        session=database.provided.session
    )

    # Domain Services
    decision_engine = providers.Singleton(
        DecisionEngine,
        base_probability=config.provided.bot.response_probability
    )

    # Application Services
    message_handling_service = providers.Factory(
        MessageHandlingService,
        user_repository=user_repository,
        decision_engine=decision_engine
    )
```

### Usage

```python
# Create container
container = Container()

# Wire dependencies
container.wire(modules=[__name__])

# Use injected dependencies
from dependency_injector.wiring import Provide, inject

@inject
async def process_message(
    service: MessageHandlingService = Provide[Container.message_handling_service]
):
    await service.handle_incoming_message(...)
```

---

## 🧪 Testing Strategy

### Unit Tests (Domain Layer)

```python
def test_user_profile_upgrade():
    # Given
    profile = UserProfile(
        user_id=UserId(123),
        relationship=Relationship(level=RelationshipLevel.STRANGER),
        trust_score=TrustScore(0.8),
        interaction_count=15,
        positive_interactions=14
    )

    # When
    upgraded = profile.try_upgrade_relationship()

    # Then
    assert upgraded is True
    assert profile.relationship.level == RelationshipLevel.ACQUAINTANCE
```

### Integration Tests (Infrastructure)

```python
@pytest.mark.integration
async def test_user_repository_save_and_load(db_session):
    # Given
    repository = SQLAlchemyUserProfileRepository(db_session)
    profile = UserProfile(...)

    # When
    await repository.save(profile)
    loaded = await repository.get_by_user_id(profile.user_id)

    # Then
    assert loaded is not None
    assert loaded.user_id == profile.user_id
```

### E2E Tests (Full Flow)

```python
@pytest.mark.e2e
async def test_complete_message_flow(container):
    # Given
    service = container.message_handling_service()

    # When
    result = await service.handle_incoming_message(
        message_id=123,
        chat_id=456,
        user_id=789,
        text="Hello bot!"
    )

    # Then
    assert result.is_success()
```

---

## 📊 Key Design Patterns

### 1. Repository Pattern

**Purpose:** Abstraction over data access

```python
# Domain interface (port)
class UserProfileRepository(Protocol):
    async def get_by_user_id(self, user_id: UserId) -> Optional[UserProfile]:
        ...

# Infrastructure implementation (adapter)
class SQLAlchemyUserProfileRepository:
    async def get_by_user_id(self, user_id: UserId) -> Optional[UserProfile]:
        # SQLAlchemy implementation
        ...
```

### 2. Factory Pattern

**Purpose:** Complex object creation

```python
class PersonaFactory:
    @staticmethod
    def create_from_yaml(path: str) -> Persona:
        data = yaml.safe_load(Path(path).read_text())
        return Persona(
            name=data["name"],
            system_prompt=data["system_prompt"],
            traits=data.get("traits", []),
            examples=data.get("examples", [])
        )
```

### 3. Strategy Pattern

**Purpose:** Interchangeable algorithms

```python
class LLMProvider(Protocol):
    async def generate(self, prompt: Prompt, temperature: Temperature) -> LLMResponse:
        ...

class ClaudeProvider:
    async def generate(self, prompt, temperature) -> LLMResponse:
        # Claude implementation
        ...

class OpenAIProvider:
    async def generate(self, prompt, temperature) -> LLMResponse:
        # OpenAI implementation
        ...
```

### 4. Observer Pattern (Domain Events)

**Purpose:** Decoupled event handling

```python
# Event
class MessageReceived(DomainEvent):
    message_id: UUID
    chat_id: int
    user_id: int

# Event handler
class MessageReceivedHandler:
    async def handle(self, event: MessageReceived):
        # Process event
        ...
```

---

## 🎯 Best Practices

### 1. Domain Layer

- ✅ Keep entities small and focused
- ✅ Use value objects for validation
- ✅ Domain services for multi-entity logic
- ✅ Rich domain models (behavior, not just data)
- ❌ No framework dependencies
- ❌ No infrastructure concerns

### 2. Application Layer

- ✅ One command/query per use case
- ✅ Use DTOs for external communication
- ✅ Return Result monads, not exceptions
- ✅ Orchestrate domain logic
- ❌ No business rules (belongs in domain)
- ❌ No direct database access

### 3. Infrastructure Layer

- ✅ Implement all repository interfaces
- ✅ Use ORM for database access
- ✅ Handle framework-specific concerns
- ✅ Create adapters for external services
- ❌ Don't leak implementation details to domain

### 4. General

- ✅ Follow SOLID principles
- ✅ Dependency rule: inner layers don't depend on outer
- ✅ Use dependency injection
- ✅ Write tests for all layers
- ✅ Use type hints everywhere (mypy strict)

---

## 📚 Further Reading

- **DDD Patterns:** Eric Evans - "Domain-Driven Design"
- **Clean Architecture:** Robert C. Martin - "Clean Architecture"
- **CQRS:** Greg Young - "CQRS Documents"
- **Hexagonal Architecture:** Alistair Cockburn

---

**Built with modern Python and DDD principles** 🎭
