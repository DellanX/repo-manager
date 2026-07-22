# Test Directory Structure Specification

## 1. Purpose

Define a consistent test directory structure that mirrors the `src/` layout, making it easy to locate tests for any source module and ensuring coverage visibility.

## 2. Scope

### In-Scope

- Test file naming conventions.
- Test directory hierarchy rules.
- Mapping between source files and test files.

### Out-of-Scope

- Test implementation details (see `testing_strategy.md`).
- CI/CD pipeline configuration.
- Coverage tooling configuration.

## 3. Contracts

### 3.1 Directory Hierarchy

The `tests/` directory **must** mirror the `src/` directory structure:

```
src/                          tests/
├── api/                      ├── api/
│   ├── mcp.py               │   ├── test_mcp.py          # Option A: single file
│   ├── rest.py              │   ├── rest/                # Option B: directory
│   │                        │   │   ├── test_routes.py
│   │                        │   │   └── test_errors.py
│   └── websocket.py         │   └── test_websocket.py
├── core/                     ├── core/
│   ├── config.py            │   ├── test_config.py
│   └── events.py            │   └── test_events.py
├── models/                   ├── models/
│   └── schemas.py           │   └── test_schemas.py
└── services/                 └── services/
    ├── file_operations.py       ├── test_file_operations.py
    └── git_operations.py        └── git_operations/
                                     ├── test_clone.py
                                     └── test_commit.py
```

### 3.2 Test File Naming

#### Option A: Single Test File

When a source module has a manageable number of test cases, use a single test file:

| Source File | Test File |
|-------------|-----------|
| `src/api/mcp.py` | `tests/api/test_mcp.py` |
| `src/core/config.py` | `tests/core/test_config.py` |
| `src/models/schemas.py` | `tests/models/test_schemas.py` |

**Pattern:** `tests/{path}/test_{module}.py`

#### Option B: Test Directory

When a source module requires many test files (grouped by feature, spec, or concern), use a directory:

| Source File | Test Directory |
|-------------|----------------|
| `src/api/rest.py` | `tests/api/rest/` |
| `src/services/git_operations.py` | `tests/services/git_operations/` |

**Pattern:** `tests/{path}/{module}/test_{concern}.py`

Test files within the directory should be named by concern:

- `test_routes.py` - HTTP route behavior
- `test_errors.py` - error handling and mapping
- `test_validation.py` - input validation
- `test_{feature}.py` - specific feature or spec

### 3.3 Selection Criteria

Use **Option A (single file)** when:

- The source module is small or focused.
- All tests fit reasonably in one file (< 500 lines recommended).
- Test cases share common fixtures with minimal separation.

Use **Option B (directory)** when:

- The source module is large or complex.
- Tests naturally group into distinct concerns.
- Multiple contributors work on different test areas.
- The single-file approach exceeds 500 lines.

### 3.4 Shared Fixtures

| Location | Purpose |
|----------|---------|
| `tests/conftest.py` | Global fixtures (temp directories, event store reset) |
| `tests/{path}/conftest.py` | Subdirectory-scoped fixtures |
| `tests/{path}/{module}/conftest.py` | Module-scoped fixtures (Option B only) |

## 4. Invariants

1. **Mirror Rule**: Every source file in `src/` must have a corresponding test file or directory in `tests/` at the equivalent path.

2. **Prefix Rule**: All test files must be prefixed with `test_`.

3. **No Orphans**: Test files must not exist without a corresponding source file (except `conftest.py`).

4. **Single Mapping**: A source file maps to either a single test file OR a test directory, never both.

5. **Init Files**: Test directories must contain `__init__.py` files for proper pytest collection.

## 5. Failure Cases

| Violation | Detection | Resolution |
|-----------|-----------|------------|
| Missing test file for source | CI coverage check | Create test file at correct path |
| Test file at wrong path | Code review | Move to mirrored location |
| Mixed single-file and directory | Lint check | Choose one approach, migrate |
| Missing `__init__.py` | pytest collection failure | Add empty `__init__.py` |

## 6. Observability

- Coverage reports must map to source files via mirrored paths.
- Test discovery logs should show hierarchical structure.
- CI should report test counts per directory.

## 7. Security

No security implications for directory structure.

## 8. Validation

### Required Tests

- Lint rule or CI check to validate mirror structure.
- pytest collection must succeed from repository root.

### Manual Review Checklist

- [ ] New test files follow naming convention.
- [ ] Test directory mirrors source directory.
- [ ] `conftest.py` files placed at appropriate scope.
- [ ] `__init__.py` present in all test directories.

## 9. Traceability

| Capability | Requirement |
|------------|-------------|
| TST-DIR-001 | Tests mirror src directory structure |
| TST-DIR-002 | Test files prefixed with `test_` |
| TST-DIR-003 | Single-file or directory approach per module |

## 10. Migration Path

For existing flat test files (e.g., `tests/test_api_mcp.py`), migrate to the mirrored structure:

```bash
# Before (flat)
tests/test_api_mcp.py

# After (mirrored - Option A)
tests/api/test_mcp.py

# After (mirrored - Option B)
tests/api/mcp/test_tools.py
tests/api/mcp/test_errors.py
```

Migration steps:

1. Create target directory structure with `__init__.py` files.
2. Move or split test file to new location.
3. Update any absolute imports in test files.
4. Verify pytest collection and coverage mapping.
5. Remove old test file.
