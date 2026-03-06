# TypeScript/Node.js Audit Trail & GMP-Compliance Library Analysis

**Research Date:** 2026-03-05
**Scope:** TypeScript libraries, NestJS patterns, Prisma/TypeORM integrations, PostgreSQL approaches for GMP-compliant audit trails

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Library Comparison Matrix](#2-library-comparison-matrix)
3. [Bemi (PostgreSQL CDC-Based)](#3-bemi-postgresql-cdc-based)
4. [Prisma Audit Trail Approaches](#4-prisma-audit-trail-approaches)
5. [NestJS Audit Trail Packages](#5-nestjs-audit-trail-packages)
6. [Attest - Hash-Chained Tamper-Evident Audit Log](#6-attest---hash-chained-tamper-evident-audit-log)
7. [TypeORM Subscriber-Based Auditing](#7-typeorm-subscriber-based-auditing)
8. [PostgreSQL Triggers with ORMs: Gotchas](#8-postgresql-triggers-with-orms-gotchas)
9. [pgAudit Extension](#9-pgaudit-extension)
10. [Hash-Chain Implementation Pattern](#10-hash-chain-implementation-pattern)
11. [GMP/21 CFR Part 11 Gap Analysis](#11-gmp21-cfr-part-11-gap-analysis)
12. [Recommendations for DLE-SaaS](#12-recommendations-for-dle-saas)

---

## 1. Executive Summary

**No single TypeScript library provides a complete GMP-compliant audit trail out of the box.** The ecosystem is fragmented across:

- **CDC/WAL-based trackers** (Bemi) -- capture everything but lack tamper-evidence
- **ORM middleware/extensions** (Prisma extensions, TypeORM subscribers) -- capture app-level context but miss direct SQL
- **NestJS interceptor packages** -- capture HTTP request context but not entity-level diffs
- **Hash-chain libraries** (Attest) -- provide tamper-evidence but are not integrated with ORMs/databases

For a GMP-compliant system (21 CFR Part 11), you need to **combine multiple approaches**:
1. PostgreSQL triggers for guaranteed capture of old/new values
2. Application-level context injection (user, reason for change)
3. Hash chaining for tamper-evidence
4. Electronic signature integration

---

## 2. Library Comparison Matrix

| Feature | Bemi (CDC) | Prisma Audit Log Context (official) | @explita/prisma-audit-log | mediavine/prisma-audit-log-ext | nestjs-auditlog | @appstellar/nestjs-audit | Attest (hash-chain) |
|---|---|---|---|---|---|---|---|
| **GitHub Stars** | 389 (bemi-io), 110 (bemi-prisma) | N/A (example repo) | New | 0 (fork) | 5 | 22 | 1 |
| **Language** | TypeScript | TypeScript | TypeScript | TypeScript | TypeScript | TypeScript | TypeScript |
| **License** | SSPL-1.0 (core), LGPL-3.0 (ORM libs) | MIT | Unknown | LGPL-3.0 | MIT | MIT | Apache 2.0 |
| **Maturity** | Production (used in fintech for $15B AUM) | Example/Reference | Early | Fork of Bemi | Active | Stable | v1.0.0 (Mar 2026) |
| **Tracks old/new values** | YES (full JSON before/after) | YES (via PG trigger) | YES | YES (via CDC) | Partial (via callback) | NO | N/A (event-based) |
| **Reason for change** | Via app context | Via app context | Via context option | Via app context | Via decorator params | NO | Via event payload |
| **Hash chaining** | NO | NO | NO | NO | NO | NO | **YES (SHA-256)** |
| **Tamper-evidence** | NO | NO | NO | NO | NO | NO | **YES + external anchoring** |
| **Captures direct SQL** | **YES** (WAL-based) | YES (trigger-based) | NO (middleware) | **YES** (WAL-based) | NO | NO | N/A |
| **PostgreSQL triggers** | Not needed | **YES** (core approach) | NO | Not needed | NO | NO | NO |
| **Type safety** | Prisma types preserved | Full Prisma types | Prisma extension types | Prisma types preserved | Decorator-based | Decorator-based | REST API |
| **Self-hostable** | YES (Docker, needs Debezium+NATS) | YES (just PG) | YES | Requires Bemi cloud | YES | YES | YES (Docker) |
| **Infra complexity** | HIGH (Debezium+NATS+Worker) | LOW (just PG triggers) | LOW | HIGH | LOW | LOW | MEDIUM |

---

## 3. Bemi (PostgreSQL CDC-Based)

**Repos:** github.com/BemiHQ/bemi-io (389 stars), github.com/BemiHQ/bemi-prisma (110 stars), github.com/BemiHQ/bemi-typeorm (25 stars)

### Architecture

Bemi operates at two levels:

1. **Database Level:** Connects to PostgreSQL's Write-Ahead Log (WAL) via logical replication and implements Change Data Capture (CDC). This captures ALL changes including direct SQL, bypassing the application entirely.

2. **Application Level:** ORM extensions (Prisma, TypeORM) inject application context (user ID, endpoint, request params) into PostgreSQL session variables that get captured in the replication stream.

### Self-Hosted Components

```
PostgreSQL (wal_level=logical)
    |
    v
Debezium (Java) -- logical decoding --> NATS JetStream (Go) --> Bemi Worker (TypeScript)
                                                                       |
                                                                       v
                                                              PostgreSQL (changes table)
```

**Requirements:**
- PostgreSQL with `wal_level = logical`
- `ALTER TABLE [table] REPLICA IDENTITY FULL` for before-values
- Debezium (Java), NATS JetStream (Go), Bemi Worker (TypeScript)
- Docker recommended for self-hosting

### Changes Table Schema

```
primary_key | table  | operation | before                          | after                           | context                                    | committed_at
26          | todos  | UPDATE    | {"id":26,"task":"Sleep",        | {"id":26,"task":"Sleep",        | {"userId":"123","endpoint":"/api/todos",   | 2024-01-01T00:00:00Z
            |        |           |  "isCompleted":false}           |  "isCompleted":true}            |  "params":{"id":"26"}}                     |
```

### Prisma Integration

```typescript
import { PrismaPg, withBemiExtension } from "@bemi-db/prisma";

const adapter = PrismaPg({ connectionString: process.env.DATABASE_URL });
const prisma = withBemiExtension(new PrismaClient({ adapter }));

// Context is automatically captured from Express middleware:
app.use(
  setContext((req: Request) => ({
    userId: req.user?.id,
    endpoint: req.url,
    params: req.body,
  }))
);
```

### TypeORM Integration

```typescript
import { setContext } from "@bemi-db/typeorm";

app.use(
  setContext(AppDataSource, (req: Request) => ({
    userId: req.user?.id,
    endpoint: req.url,
    params: req.body,
  }))
);
```

### Strengths for GMP
- Captures 100% of changes (even direct SQL)
- Full before/after snapshots in JSON
- Application context (who, why, where)
- No schema modifications required
- Originally built for fintech compliance ($15B AUM)

### Weaknesses for GMP
- **No hash chaining or tamper-evidence** -- a DBA could modify the changes table
- **No "reason for change" field** -- context captures request metadata, not user-entered justification
- **No electronic signature support**
- **SSPL-1.0 license** on core (restrictive for SaaS)
- **OSS version limited** -- no partitioning, no retention management, no HA
- **High infrastructure complexity** -- Debezium (Java) + NATS (Go) + Worker (TS)

---

## 4. Prisma Audit Trail Approaches

### 4a. Official Prisma Client Extension: audit-log-context

**Repo:** github.com/prisma/prisma-client-extensions/tree/main/audit-log-context

This is Prisma's **recommended pattern** for PostgreSQL trigger-based audit logging.

#### How It Works

1. **Version tables** mirror audited tables (e.g., `ProductVersion` for `Product`)
2. **PostgreSQL triggers** fire on INSERT/UPDATE/DELETE and copy row data to version tables
3. **Prisma extension** injects user context via `SET LOCAL` session variables
4. **Triggers read context** via `current_setting('app.current_user_id', TRUE)`

#### Trigger Function

```sql
CREATE OR REPLACE FUNCTION audit_product_changes()
RETURNS TRIGGER AS $$
BEGIN
  IF (TG_OP = 'INSERT' OR TG_OP = 'UPDATE') THEN
    INSERT INTO "ProductVersion" (
      "versionOperation", "versionProductId", "versionUserId", "versionTimestamp",
      -- all product columns...
    ) VALUES (
      TG_OP, NEW.id, current_setting('app.current_user_id', TRUE)::int, NOW(),
      NEW.name, NEW.price -- ...
    );
    RETURN NEW;
  ELSIF (TG_OP = 'DELETE') THEN
    INSERT INTO "ProductVersion" (
      "versionOperation", "versionProductId", "versionUserId", "versionTimestamp",
      -- all product columns...
    ) VALUES (
      'DELETE', OLD.id, current_setting('app.current_user_id', TRUE)::int, NOW(),
      OLD.name, OLD.price -- ...
    );
    RETURN OLD;
  END IF;
END;
$$ LANGUAGE plpgsql;
```

#### Prisma Extension for Context

```typescript
const auditExtension = Prisma.defineExtension((client) => {
  return client.$extends({
    client: {
      forUser(userId: number) {
        return client.$extends({
          query: {
            $allOperations({ args, query }) {
              return client.$transaction(async (tx) => {
                await tx.$executeRawUnsafe(
                  `SET LOCAL app.current_user_id = '${userId}'`
                );
                return query(args);
              });
            },
          },
        });
      },
    },
  });
});

// Usage:
const userPrisma = prisma.forUser(currentUser.id);
await userPrisma.product.update({ where: { id: 1 }, data: { price: 99 } });
```

#### Strengths
- **Low infrastructure** -- just PostgreSQL triggers, no external services
- **Captures direct SQL** changes (trigger-based)
- **Full old/new values** via OLD.*/NEW.* in trigger
- **User context** passed via session variables
- **Full type safety** with Prisma generated types

#### Weaknesses
- **Version tables must be manually maintained** -- schema changes require trigger updates
- **Known Prisma issue:** `$transaction()` in extensions may not work as intended in all cases
- **No hash chaining, no tamper-evidence**
- **No reason-for-change field** out of the box
- **Connection pool gotcha:** `SET LOCAL` only works within a transaction; Prisma's connection pool may give different connections

### 4b. @explita/prisma-audit-log

**npm:** @explita/prisma-audit-log

```typescript
import { auditLogExtension } from "@explita/prisma-audit-log";

const prisma = new PrismaClient().$extends(
  auditLogExtension({
    include: ["User", "Product"],  // or exclude: [...]
    getContext: () => ({ userId: getCurrentUserId() }),
  })
);
```

- Automatic logging of create/update/delete
- Batch processing with fallback to single inserts
- Application-level only (cannot capture direct SQL)
- No hash chaining or tamper-evidence
- Early-stage package

### 4c. Prisma Middleware (DIY approach)

```typescript
prisma.$use(async (params, next) => {
  // LIMITATION: Cannot reliably get "before" values in middleware
  // Must do a separate findFirst before the operation
  let before = null;
  if (params.action === 'update' || params.action === 'delete') {
    before = await prisma[params.model].findFirst({ where: params.args.where });
  }

  const result = await next(params);

  await prisma.auditLog.create({
    data: {
      model: params.model,
      action: params.action,
      before: before ? JSON.stringify(before) : null,
      after: result ? JSON.stringify(result) : null,
      userId: getCurrentUserId(), // from AsyncLocalStorage
    },
  });

  return result;
});
```

**Critical limitations:**
- Extra query for each mutation (performance hit)
- **Race condition:** between the findFirst and the actual mutation, another process could modify the record
- **Nested writes not captured** -- middleware does not fire for nested create/update
- **Cannot capture direct SQL changes**

---

## 5. NestJS Audit Trail Packages

### 5a. nestjs-auditlog (thanhlcm90)

**Repo:** github.com/thanhlcm90/nestjs-auditlog (5 stars, 34 commits)

**Approach:** Decorator-based with multiple exporters.

```typescript
@Controller('users')
export class UserController {
  @Post()
  @AuditLog({
    resource: 'users',
    action: 'create',
  })
  async createUser(@Body() dto: CreateUserDto) {
    return this.userService.create(dto);
  }

  @Patch(':id')
  @AuditLogUpdate({
    resource: 'users',
  })
  async updateUser(
    @Param('id') id: string,
    @Body() dto: UpdateUserDto,
    @AuditLogDataDiff() dataDiff: (before: any) => void, // callback for before/after
  ) {
    const before = await this.userService.findOne(id);
    dataDiff(before); // register "before" state
    return this.userService.update(id, dto);
  }
}
```

**Exporters:** stdout, OpenTelemetry (gRPC/HTTP), ClickHouse
**Old/new values:** Via `@AuditLogDataDiff` callback (manual)
**Hash chaining:** None
**Tamper-evidence:** None

### 5b. @appstellar/nestjs-audit

**Repo:** github.com/appstellar-team/nestjs-audit (22 stars)

```typescript
@Get()
@Audit({
  action: Action.READ,
  getUserId: (req) => req.user.id,
  getResponseObjectId: (res) => res.id,
  entity: 'Product',
})
getData() {
  return this.productService.findAll();
}
```

**Transports:** Console, MongoDB (Mongoose), AWS SNS
**Old/new values:** Not tracked
**Focus:** Request-level audit, not entity-level change tracking

### 5c. @forlagshuset/nestjs-audit-logging

**npm:** v2.0.0, MIT, ~47 kB
**Approach:** Decorator-based with event subject support
**Old/new values:** Not tracked
**Focus:** Controller action logging with custom messages

### 5d. Custom NestJS Interceptor Pattern (recommended for GMP)

```typescript
@Injectable()
export class AuditInterceptor implements NestInterceptor {
  constructor(private auditService: AuditService) {}

  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const request = context.switchToHttp().getRequest();
    const { method, url, user, body } = request;

    // Only audit mutating operations
    if (['POST', 'PATCH', 'PUT', 'DELETE'].includes(method)) {
      return next.handle().pipe(
        tap((response) => {
          this.auditService.record({
            action: method,
            userId: user?.id,
            endpoint: url,
            requestBody: body,
            responseId: response?.id,
            timestamp: new Date(),
          });
        }),
      );
    }

    return next.handle();
  }
}
```

**Limitation:** This captures request-level context but NOT entity-level before/after values. For GMP, you need BOTH this interceptor AND database-level tracking (triggers or CDC).

---

## 6. Attest - Hash-Chained Tamper-Evident Audit Log

**Repo:** github.com/Ashish-Barmaiya/attest (1 star, 27 commits, Apache 2.0)
**Language:** TypeScript 77.4%, JavaScript 21.7%
**Released:** v1.0.0 (March 2, 2026)

### Architecture

Attest is the **only TypeScript library found that implements cryptographic hash chaining** for audit logs.

#### Hash Chain Mechanism

```
chainHash = SHA256(prevChainHash + SHA256(payload))
```

Each event's hash depends on the previous event's hash, creating a mathematical dependency chain. Any modification to a historical record invalidates all subsequent hashes.

#### External Anchoring

Periodically publishes cryptographic snapshots to external systems (e.g., Git repositories) outside the database's control. This prevents silent history rewrites even during complete database compromise.

#### Trust Model

- **Assumes** the application server and database may be compromised
- **Verification trusts** only: cryptographic hash chains + external anchor history
- **Verification does NOT trust:** the API, the database, or internally stored metadata

#### Multi-Tenant Isolation

Each project maintains independent hash chains and anchor histories. Project identity is derived exclusively from API keys.

#### API

```bash
# Ingest an audit event
curl -X POST http://localhost:3000/events \
  -H "x-api-key: <PROJECT_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "login",
    "actor": {"type": "user", "id": "u123"},
    "resource": {"type": "document", "id": "d456"},
    "metadata": {"ip": "192.168.1.1"}
  }'

# Verify chain integrity (CLI)
attest verify <PROJECT_ID> --anchors /path/to/anchors
```

### Strengths for GMP
- **True tamper-evidence** with SHA-256 hash chains
- **External anchoring** prevents even DBA tampering
- **Independent verification** process
- **Multi-tenant** with isolated chains
- **Apache 2.0** license (permissive)

### Weaknesses for GMP
- **Very new** (v1.0.0, 1 star, March 2026)
- **No ORM integration** -- standalone REST service
- **No entity-level tracking** -- it logs events, not database row changes
- **No before/after values** -- you must construct the event payload yourself
- **No electronic signature support**
- **Self-described as NOT** a general logging platform

---

## 7. TypeORM Subscriber-Based Auditing

TypeORM provides entity lifecycle hooks that can be used for audit logging.

### Subscriber Pattern

```typescript
@EventSubscriber()
export class AuditSubscriber implements EntitySubscriberInterface {

  afterInsert(event: InsertEvent<any>) {
    const entity = event.entity;
    // Log: INSERT, null -> entity
    this.logChange('INSERT', event.metadata.tableName, null, entity);
  }

  afterUpdate(event: UpdateEvent<any>) {
    const before = event.databaseEntity; // old values (loaded from DB)
    const after = event.entity;          // new values
    // Log: UPDATE, before -> after
    this.logChange('UPDATE', event.metadata.tableName, before, after);
  }

  afterRemove(event: RemoveEvent<any>) {
    const entity = event.databaseEntity;
    // Log: DELETE, entity -> null
    this.logChange('DELETE', event.metadata.tableName, entity, null);
  }

  private async logChange(op: string, table: string, before: any, after: any) {
    // IMPORTANT: Use event.manager or event.queryRunner, NOT a separate connection
    await event.manager.save(AuditLog, {
      operation: op,
      tableName: table,
      oldValues: before ? JSON.stringify(before) : null,
      newValues: after ? JSON.stringify(after) : null,
      userId: AsyncLocalStorage.getStore()?.userId, // from ALS
      timestamp: new Date(),
    });
  }
}
```

### Key Gotchas

1. **`databaseEntity` may be null** if the entity wasn't loaded with relations
2. **Subscriber fires for ALL entities** unless you implement `listenTo()` to filter
3. **No access to HTTP request context** -- must use AsyncLocalStorage or cls-hooked
4. **Nested saves may not trigger subscribers** in all cases
5. **Bulk operations** (createQueryBuilder().update()) do NOT trigger subscribers
6. **Performance:** Each update requires loading the old entity first

### Comparison with Prisma Middleware

| Aspect | TypeORM Subscribers | Prisma Middleware |
|---|---|---|
| Before values | `event.databaseEntity` (auto-loaded for updates) | Must query manually |
| Nested operations | Partially supported | Not reliably captured |
| Direct SQL/QueryBuilder | NOT captured | NOT captured |
| Type safety | Entity types available | Full generated types |
| User context | AsyncLocalStorage | AsyncLocalStorage |
| Bulk operations | NOT captured | NOT captured |

---

## 8. PostgreSQL Triggers with ORMs: Gotchas

### Critical Issues When Combining PG Triggers with Prisma

1. **Trigger errors break Prisma operations:** If a trigger raises an error, Prisma's create/update/delete will fail with cryptic errors (Issue #4656 on prisma/prisma).

2. **Context passing via SET LOCAL is fragile:**
   - `SET LOCAL` only works within a transaction
   - Prisma's connection pool may assign different connections within the same request
   - Solution: Always wrap in `$transaction()`, but this has its own issues with Prisma extensions

3. **Schema drift:** Version/audit tables must be manually updated when the source table schema changes. Prisma Migrate won't auto-generate trigger updates.

4. **Migration management:** Triggers must be created via raw SQL in Prisma migrations:
   ```
   prisma/migrations/TIMESTAMP_add_audit_triggers/migration.sql
   ```

5. **REPLICA IDENTITY FULL required for WAL-based tracking:**
   ```sql
   ALTER TABLE "Product" REPLICA IDENTITY FULL;
   ```
   Without this, DELETE operations in WAL won't include old values.

6. **Multiple triggers on same table** fire in alphabetical order -- can cause unexpected behavior.

7. **Performance:** Triggers execute within the same transaction as the write operation. Heavy audit logic in triggers increases write latency.

### Critical Issues When Combining PG Triggers with TypeORM

1. **TypeORM subscribers AND triggers can double-log** if both are active
2. **TypeORM's `synchronize: true`** may drop custom triggers during schema sync
3. **Migration files must be used** to manage trigger creation/updates

### Recommended Hybrid Approach

```
Level 1: PostgreSQL trigger (guaranteed capture, old/new values, even direct SQL)
Level 2: ORM middleware/extension (inject app context: user, reason, endpoint)
Level 3: Hash chain (tamper-evidence on the audit records themselves)
```

---

## 9. pgAudit Extension

**Website:** pgaudit.org | **Repo:** github.com/pgaudit/pgaudit

pgAudit is a PostgreSQL extension for SQL statement-level audit logging. It logs the actual SQL executed, not row-level changes.

### What It Does
- Logs SELECT, INSERT, UPDATE, DELETE, DDL statements
- Tags each statement with operation type (READ, WRITE, ROLE, DDL)
- Includes session ID and statement counter for flow reconstruction
- Can exclude query parameters from logs (PII protection)
- Per-database, per-user, per-object granularity

### What It Does NOT Do
- Does NOT capture old/new row values
- Does NOT capture application context (user identity from app layer)
- Does NOT provide hash chaining or tamper-evidence
- Is NOT a replacement for row-level audit trails

### Verdict for GMP
pgAudit is **complementary** to application-level audit trails. It answers "what SQL was executed?" while row-level triggers answer "what data changed?" Both are needed for full GMP compliance.

---

## 10. Hash-Chain Implementation Pattern

Based on analysis of the Attest library and the DEV Community implementation, here is the canonical hash-chain pattern for TypeScript audit logs:

### Data Structure

```typescript
interface AuditEntry {
  id: string;                  // UUID
  timestamp: Date;
  action: string;              // CREATE | UPDATE | DELETE
  entityType: string;          // e.g., "BatchRecord"
  entityId: string;
  userId: string;
  reason: string;              // GMP: reason for change
  oldValues: Record<string, any> | null;
  newValues: Record<string, any> | null;
  prevHash: string;            // hash of previous entry (or "GENESIS")
  entryHash: string;           // SHA-256(prevHash + SHA-256(canonicalPayload))
}
```

### Canonical JSON Serialization (Critical for Determinism)

```typescript
function canonicalStringify(obj: unknown): string {
  if (obj === null || typeof obj !== 'object') return JSON.stringify(obj);
  if (Array.isArray(obj)) return '[' + obj.map(canonicalStringify).join(',') + ']';
  const sortedKeys = Object.keys(obj as Record<string, unknown>).sort();
  const pairs = sortedKeys.map(
    (key) => JSON.stringify(key) + ':' + canonicalStringify((obj as any)[key])
  );
  return '{' + pairs.join(',') + '}';
}
```

### Hash Computation

```typescript
import { createHash } from 'crypto';

function sha256(input: string): string {
  return createHash('sha256').update(input).digest('hex');
}

function computeEntryHash(entry: Omit<AuditEntry, 'entryHash'>, prevHash: string): string {
  const payload = canonicalStringify({
    id: entry.id,
    timestamp: entry.timestamp.toISOString(),
    action: entry.action,
    entityType: entry.entityType,
    entityId: entry.entityId,
    userId: entry.userId,
    reason: entry.reason,
    oldValues: entry.oldValues,
    newValues: entry.newValues,
  });
  return sha256(prevHash + sha256(payload));
}
```

### Chain Verification (O(n))

```typescript
async function verifyChain(entries: AuditEntry[]): Promise<{
  valid: boolean;
  firstInvalidIndex: number | null;
}> {
  for (let i = 0; i < entries.length; i++) {
    const expectedPrevHash = i === 0 ? 'GENESIS' : entries[i - 1].entryHash;

    // Check linkage
    if (entries[i].prevHash !== expectedPrevHash) {
      return { valid: false, firstInvalidIndex: i };
    }

    // Check integrity
    const recomputed = computeEntryHash(entries[i], entries[i].prevHash);
    if (entries[i].entryHash !== recomputed) {
      return { valid: false, firstInvalidIndex: i };
    }
  }
  return { valid: true, firstInvalidIndex: null };
}
```

### Detected Attack Types
- **Payload modification:** Hash mismatch on altered entry
- **Deletion:** `prevHash` breaks at successor entry
- **Reordering:** Multiple entries fail linkage validation
- **Insertion:** Hash chain breaks at insertion point

---

## 11. GMP/21 CFR Part 11 Gap Analysis

### 21 CFR Part 11 Requirements vs. Available Libraries

| Requirement | Bemi | Prisma Triggers | NestJS Packages | Attest | Custom Needed? |
|---|---|---|---|---|---|
| **Secure, computer-generated audit trails** | YES | YES | YES | YES | NO |
| **Time-stamped automatically** | YES | YES | YES | YES | NO |
| **Record date/time of operator entries** | YES | YES | Partial | YES | Minimal |
| **Cannot be manually updated by users** | Partial (DBA can) | Partial (DBA can) | NO (app-level) | **YES** (hash chain) | YES for full |
| **Record identity of operator** | YES (via context) | YES (via SET LOCAL) | YES (via request) | YES (via actor) | NO |
| **Create, modify, delete tracking** | YES | YES | Partial | YES (events) | Minimal |
| **Old/new value recording** | YES | YES | Partial | NO (manual) | YES for Attest |
| **Reason for change** | NO (only request params) | NO (not built in) | NO | Via metadata | **YES** |
| **Electronic signatures** | NO | NO | NO | NO | **YES** |
| **Tamper-evidence** | NO | NO | NO | **YES** | YES for others |
| **Available for FDA review/copy** | YES (queryable) | YES (SQL) | Depends on exporter | YES (verify CLI) | Minimal |
| **Retained for record retention period** | Cloud only (OSS: no) | YES (in PG) | Depends | YES | Policy needed |

### Key Gaps to Fill Custom

1. **Reason for change UI/API** -- none of the libraries provide this; must be built into the application layer
2. **Electronic signatures** -- no TypeScript library exists for GMP-compliant e-signatures; must implement per 21 CFR Part 11 Subpart C (unique user ID + password, at minimum)
3. **Hash chaining on audit records** -- only Attest provides this, but it's not integrated with database change tracking
4. **Tamper-evident storage** -- PostgreSQL alone is not sufficient; need either hash chaining, external anchoring, or append-only storage
5. **Audit trail review interface** -- none of the libraries provide a UI for reviewing audit trails

---

## 12. Recommendations for DLE-SaaS

### Recommended Architecture: Layered Approach

```
+------------------------------------------------------------------+
|                    NestJS Application Layer                       |
|  +-----------------------+  +----------------------------------+ |
|  | AuditInterceptor      |  | Electronic Signature Service     | |
|  | - Captures user ID    |  | - Username + password validation | |
|  | - Captures endpoint   |  | - Reason for change prompt       | |
|  | - Captures reason     |  | - Signing meaning declaration    | |
|  +-----------+-----------+  +----------------------------------+ |
|              |                                                    |
|  +-----------v--------------------------------------------------+ |
|  | Prisma Client Extension                                      | |
|  | - SET LOCAL app.current_user_id = ...                        | |
|  | - SET LOCAL app.change_reason = ...                          | |
|  | - Wraps mutations in transactions                            | |
|  +--------------------------------------------------------------+ |
+------------------------------------------------------------------+
              |
+------------------------------------------------------------------+
|                    PostgreSQL Database                            |
|  +-----------------------------------------------------------+  |
|  | AFTER INSERT/UPDATE/DELETE Triggers                        |  |
|  | - Capture OLD.* and NEW.* (full row snapshots)            |  |
|  | - Read current_setting('app.current_user_id')             |  |
|  | - Read current_setting('app.change_reason')               |  |
|  | - Compute SHA-256 hash chain (prev_hash + payload)        |  |
|  | - INSERT into audit_entries (append-only)                 |  |
|  +-----------------------------------------------------------+  |
|                                                                  |
|  +-----------------------------------------------------------+  |
|  | audit_entries table (append-only, no UPDATE/DELETE grants)|  |
|  | id, entity_type, entity_id, operation,                    |  |
|  | old_values (JSONB), new_values (JSONB),                   |  |
|  | user_id, reason, electronic_signature_id,                 |  |
|  | prev_hash, entry_hash, created_at                         |  |
|  +-----------------------------------------------------------+  |
+------------------------------------------------------------------+
              |
+------------------------------------------------------------------+
|                    External Anchor (Optional)                    |
|  - Periodic hash snapshots to Git / S3 / external notary        |
|  - Enables independent verification even if DB is compromised    |
+------------------------------------------------------------------+
```

### Why This Architecture

1. **PostgreSQL triggers** guarantee capture of ALL changes (even direct SQL), with full old/new values
2. **Prisma extension** passes application context (user, reason) to triggers without external infrastructure
3. **Hash chaining in PG trigger** provides tamper-evidence at the database level with minimal performance impact
4. **NestJS interceptor** captures request context and enforces reason-for-change on mutating endpoints
5. **Append-only table** with restricted permissions prevents casual tampering
6. **External anchoring** (optional) provides ultimate tamper-evidence for regulatory audits

### Why NOT Bemi for GMP

- SSPL license is problematic for SaaS
- No tamper-evidence / hash chaining
- High infrastructure complexity (Debezium + NATS + Worker)
- OSS version explicitly not recommended for production
- Adds moving parts that themselves need GMP validation

### Implementation Priority

1. **Phase 1:** PostgreSQL audit trigger with old/new values + hash chain (pure SQL, no dependencies)
2. **Phase 2:** Prisma extension for user context and reason-for-change injection
3. **Phase 3:** NestJS AuditInterceptor + Electronic Signature service
4. **Phase 4:** External anchoring for independent verification
5. **Phase 5:** Audit trail review UI for compliance officers

### Hash Chain in PostgreSQL Trigger (Recommended Implementation)

```sql
-- Audit entries table
CREATE TABLE audit_entries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  operation TEXT NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
  old_values JSONB,
  new_values JSONB,
  user_id TEXT,
  reason TEXT,
  electronic_signature_id UUID,
  prev_hash TEXT NOT NULL,
  entry_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Make it append-only
REVOKE UPDATE, DELETE ON audit_entries FROM app_user;

-- Generic audit trigger function with hash chaining
CREATE OR REPLACE FUNCTION audit_trigger_func()
RETURNS TRIGGER AS $$
DECLARE
  v_old_values JSONB;
  v_new_values JSONB;
  v_user_id TEXT;
  v_reason TEXT;
  v_prev_hash TEXT;
  v_payload TEXT;
  v_entry_hash TEXT;
BEGIN
  -- Get application context from session variables
  v_user_id := current_setting('app.current_user_id', TRUE);
  v_reason := current_setting('app.change_reason', TRUE);

  -- Capture old/new values
  IF TG_OP = 'INSERT' THEN
    v_old_values := NULL;
    v_new_values := to_jsonb(NEW);
  ELSIF TG_OP = 'UPDATE' THEN
    v_old_values := to_jsonb(OLD);
    v_new_values := to_jsonb(NEW);
  ELSIF TG_OP = 'DELETE' THEN
    v_old_values := to_jsonb(OLD);
    v_new_values := NULL;
  END IF;

  -- Get previous hash (or GENESIS for first entry)
  SELECT entry_hash INTO v_prev_hash
  FROM audit_entries
  WHERE entity_type = TG_TABLE_NAME
  ORDER BY created_at DESC
  LIMIT 1;

  IF v_prev_hash IS NULL THEN
    v_prev_hash := 'GENESIS';
  END IF;

  -- Compute hash: SHA-256(prev_hash + SHA-256(payload))
  v_payload := concat_ws('|',
    TG_TABLE_NAME, TG_OP,
    COALESCE(v_old_values::TEXT, ''),
    COALESCE(v_new_values::TEXT, ''),
    COALESCE(v_user_id, ''),
    COALESCE(v_reason, ''),
    NOW()::TEXT
  );
  v_entry_hash := encode(
    digest(v_prev_hash || encode(digest(v_payload, 'sha256'), 'hex'), 'sha256'),
    'hex'
  );

  -- Insert audit entry
  INSERT INTO audit_entries (
    entity_type, entity_id, operation,
    old_values, new_values,
    user_id, reason,
    prev_hash, entry_hash
  ) VALUES (
    TG_TABLE_NAME,
    COALESCE(NEW.id::TEXT, OLD.id::TEXT),
    TG_OP,
    v_old_values, v_new_values,
    v_user_id, v_reason,
    v_prev_hash, v_entry_hash
  );

  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Attach to any table:
CREATE TRIGGER audit_product
  AFTER INSERT OR UPDATE OR DELETE ON "Product"
  FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
```

**Note:** Requires `pgcrypto` extension for `digest()` function:
```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

---

## Appendix A: All Repositories Analyzed

| Repository | URL | Stars | Language | License |
|---|---|---|---|---|
| BemiHQ/bemi-io | github.com/BemiHQ/bemi-io | 389 | TypeScript | SSPL-1.0 |
| BemiHQ/bemi-prisma | github.com/BemiHQ/bemi-prisma | 110 | TypeScript | LGPL-3.0 |
| BemiHQ/bemi-typeorm | github.com/BemiHQ/bemi-typeorm | 25 | TypeScript | LGPL-3.0 |
| prisma/prisma-client-extensions | github.com/prisma/prisma-client-extensions | N/A | TypeScript | MIT |
| mediavine/prisma-audit-log-extension | github.com/mediavine/prisma-audit-log-extension | 0 | TypeScript | LGPL-3.0 |
| thanhlcm90/nestjs-auditlog | github.com/thanhlcm90/nestjs-auditlog | 5 | TypeScript | MIT |
| appstellar-team/nestjs-audit | github.com/appstellar-team/nestjs-audit | 22 | TypeScript | MIT |
| Ashish-Barmaiya/attest | github.com/Ashish-Barmaiya/attest | 1 | TypeScript | Apache 2.0 |
| pgaudit/pgaudit | github.com/pgaudit/pgaudit | N/A | C | PostgreSQL |

## Appendix B: npm Packages

| Package | Version | Downloads | Purpose |
|---|---|---|---|
| @bemi-db/prisma | 1.1.0 | - | Prisma CDC audit trail |
| @bemi-db/typeorm | 1.3.0 | - | TypeORM CDC audit trail |
| @explita/prisma-audit-log | - | Low | Prisma extension audit |
| @forlagshuset/nestjs-audit-logging | 2.0.0 | Low | NestJS controller audit |
| @pavel_martinez/nestjs-auditlog | 1.6.7 | Low | NestJS OpenTelemetry audit |
| @appstellar/nestjs-audit | 1.0.0 | Low | NestJS request audit |

## Appendix C: Key Finding -- No TypeScript GMP/Pharma Boilerplate Exists

Exhaustive searching found **zero** NestJS or TypeScript boilerplates specifically built for pharmaceutical GMP compliance, 21 CFR Part 11, or regulated industry SaaS. Similarly, **no TypeScript electronic signature library** exists that targets GMP requirements. These are gaps that must be filled with custom implementation in DLE-SaaS.
