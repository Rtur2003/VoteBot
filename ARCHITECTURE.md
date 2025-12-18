# VOTRYX Architecture

## Overview

VOTRYX follows a layered architecture with clear separation of concerns. The system is designed for maintainability, testability, and extensibility.

## Architecture Principles

1. **Python-First**: All implementations use Python unless technically insufficient
2. **Separation of Concerns**: Clear boundaries between layers
3. **Dependency Inversion**: High-level modules don't depend on low-level details
4. **Single Responsibility**: Each module has one reason to change
5. **Immutability**: State objects are immutable where possible

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         UI Layer (Tkinter)                       │
│                         VotryxApp.py                             │
├─────────────────────────────────────────────────────────────────┤
│                      Application Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ StateManager │  │VotingEngine  │  │ BrowserLifecycle     │  │
│  │              │  │              │  │ Manager              │  │
│  │ - Statistics │  │ - Batch ops  │  │ - Driver lifecycle   │  │
│  │ - Observers  │  │ - Parallel   │  │ - Profile cleanup    │  │
│  │ - Log history│  │ - Backoff    │  │ - State clearing     │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                        Core Services                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │Configuration │  │  Validation  │  │  Logging Manager     │  │
│  │   Manager    │  │              │  │                      │  │
│  │              │  │ - URL check  │  │ - File logging       │  │
│  │ - Load/Save  │  │ - Ranges     │  │ - Rotation           │  │
│  │ - Defaults   │  │ - Backoff    │  │ - Formatting         │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                      Infrastructure Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ DriverManager│  │     i18n     │  │   File System        │  │
│  │              │  │              │  │                      │  │
│  │ - Chrome ops │  │ - UI strings │  │ - Config files       │  │
│  │ - Options    │  │ - Turkish    │  │ - Logs               │  │
│  │ - Stealth    │  │              │  │ - Temp profiles      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Module Responsibilities

### UI Layer

#### `VotryxApp.py`
- Tkinter widget creation and layout
- User input handling
- Visual state updates
- Event binding
- **Does NOT**: Contain business logic, driver management, or state mutation

### Application Layer

#### `StateManager` (`core/state_manager.py`)
- Centralized application state
- Immutable statistics tracking
- Observer pattern for state updates
- Log history management with filtering
- **Key Pattern**: Observer for decoupled UI updates

#### `VotingEngine` (`core/voting_engine.py`)
- Core voting business logic
- Batch operation orchestration
- Parallel worker management
- Vote session lifecycle
- Backoff and retry strategies
- **Key Pattern**: Callback-based integration

#### `BrowserLifecycleManager` (`core/browser_manager.py`)
- WebDriver lifecycle management
- Thread-safe driver registration
- Temporary profile creation/cleanup
- Browser state clearing (cookies, cache, storage)
- Automatic resource cleanup on exit
- **Key Pattern**: Resource management with context

### Core Services

#### `ConfigurationManager` (`core/config.py`)
- Configuration file discovery and loading
- Default value management
- Atomic file writes for persistence
- Path resolution (relative to base directory)
- **Key Pattern**: Defaults + override

#### `InputValidator` (`core/validation.py`)
- URL format validation
- Numeric range validation
- Path existence checks
- Backoff value validation
- User agent normalization
- **Key Pattern**: Pure functions returning (bool, error_message)

#### `LoggingManager` (`core/logging_manager.py`)
- File-based logging with rotation
- Fallback to temp directory on failure
- Structured log formatting
- Log directory management
- **Key Pattern**: Rotating file handler

### Infrastructure Layer

#### `DriverManager` (`core/driver.py`)
- Chrome WebDriver creation
- Chrome options configuration
- Version compatibility checking
- User agent selection
- Stealth patches for automation detection
- **Key Pattern**: Factory with configuration

#### `UIStrings` (`core/i18n.py`)
- Internationalized UI strings (Turkish)
- Centralized text for easier translation
- Separation of text from logic
- **Key Pattern**: Static string repository

## Data Flow

### Startup Flow
```
1. VotryxApp.__init__
   ↓
2. ConfigurationManager.load()
   ↓
3. ValidationManager validates paths
   ↓
4. LoggingManager.initialize()
   ↓
5. StateManager.initialize()
   ↓
6. UI components built
   ↓
7. StateManager observers registered
```

### Voting Flow
```
1. User clicks "Start"
   ↓
2. VotryxApp.start_bot()
   ↓
3. StateManager.set_running(True)
   ↓
4. VotingEngine.execute_batch()
   ├─> Driver created via DriverManager
   ├─> BrowserLifecycleManager.register_driver()
   ├─> VotingSession.navigate_to_target()
   ├─> VotingSession.locate_vote_button()
   ├─> VotingSession.execute_vote()
   ├─> Callbacks fired: on_success/on_error
   └─> BrowserLifecycleManager.teardown_driver()
   ↓
5. StateManager updates statistics
   ↓
6. Observers notified → UI updates
```

### State Update Flow (Observer Pattern)
```
StateManager state change
   ↓
StateManager._notify_observers()
   ↓
For each registered observer:
   ↓
observer(statistics) called
   ↓
UI updates (vote count, error count, status)
```

## Design Patterns

### 1. Observer Pattern
**Where**: StateManager → UI updates
**Why**: Decouples state management from UI
**Benefit**: UI can be replaced without touching state logic

### 2. Factory Pattern
**Where**: DriverManager creates WebDriver instances
**Why**: Encapsulates complex driver configuration
**Benefit**: Single place to manage Chrome options

### 3. Strategy Pattern
**Where**: Vote selectors (CSS, XPath)
**Why**: Multiple ways to locate vote buttons
**Benefit**: Easily add new selector strategies

### 4. Repository Pattern
**Where**: ConfigurationManager
**Why**: Abstracts configuration storage
**Benefit**: Can switch from JSON to database without changing consumers

### 5. Callback Pattern
**Where**: VotingEngine callbacks (on_success, on_error)
**Why**: Decouple voting logic from side effects
**Benefit**: Voting engine testable without UI

## Testing Strategy

### Unit Tests
- **StateManager**: State transitions, observers, immutability
- **ConfigurationManager**: Load, save, defaults, merging
- **InputValidator**: All validation rules
- **VotingEngine**: Batch logic, backoff calculations (mocked drivers)

### Integration Tests
- **DriverManager**: Real Chrome driver creation (CI only)
- **Full voting flow**: End-to-end with test target

### Test Coverage Goals
- Core modules: 90%+ coverage
- Business logic: 100% coverage
- UI layer: Manual testing (Tkinter not easily unit tested)

## Error Handling

### Principles
1. **Fail gracefully**: Never crash, log and continue
2. **User feedback**: Show errors in UI with context
3. **Retry with backoff**: Exponential backoff for transient failures
4. **Resource cleanup**: Always cleanup drivers and profiles

### Error Categories
- **Configuration errors**: Invalid settings → Show message, use defaults
- **Path errors**: Missing files → Show message, offer alternatives
- **Driver errors**: WebDriver failure → Retry with Selenium Manager
- **Voting errors**: Button not found → Screenshot, log, continue
- **Network errors**: Timeout → Backoff and retry

## Performance Considerations

### Parallel Workers
- Configurable 1-10 parallel browser windows
- ThreadPoolExecutor for concurrent voting
- Lock-protected driver registration

### Resource Management
- Temporary profiles cleaned up on exit
- Driver instances properly quit
- File logging with rotation (512KB, 3 backups)
- Log history limited to 500 entries

### Optimization Points
- Eager page loading strategy
- Optional image blocking
- Profile reuse within batch (not across)
- Batch size tunable for throughput

## Security Considerations

### Browser Automation
- Stealth patches to avoid detection
- Random user agent selection
- Incognito mode for each session
- Cache and cookie clearing between votes

### Configuration
- No secrets in config files
- Paths validated before use
- Safe file writes (atomic with tempfile)

### Dependencies
- Minimal external dependencies
- selenium for browser automation
- Python standard library for everything else

## Future Architecture Improvements

### Potential Enhancements
1. **Plugin system**: Extensible vote selectors
2. **Event bus**: Replace callbacks with pub/sub
3. **Async/await**: Use asyncio instead of threading
4. **Database**: Store vote history and statistics
5. **API server**: Web UI instead of Tkinter
6. **Docker**: Containerized deployment

### Scalability
Current design supports:
- ✅ Single machine, multiple browsers
- ❌ Distributed voting across machines (would need queue system)
- ❌ Cloud deployment (would need stateless design)

## Development Guidelines

### Adding New Features
1. Identify which layer the feature belongs to
2. Check if existing module can be extended
3. If new module needed, follow single responsibility
4. Add tests first (TDD)
5. Update this documentation

### Code Style
- Black for formatting (line length 100)
- isort for import sorting
- flake8 for linting
- mypy for type checking
- Docstrings for all public methods

### Commit Discipline
- One logical change per commit
- Clear, technical commit messages
- Format: `<scope>: <what changed>`
- Never mix refactor + feature

## Maintenance

### Regular Tasks
- Update dependencies monthly
- Review and prune logs
- Check for Chrome/ChromeDriver updates
- Monitor error rates in logs

### Monitoring
- Vote success/failure ratio
- Average voting time
- Error patterns in logs
- Driver cleanup success

---

*This architecture document is maintained alongside code changes. Update when design decisions change.*
