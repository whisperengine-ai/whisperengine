# Database Connection Pool & Transaction Audit
**Date**: October 21, 2025  
**Purpose**: Review database connection pooling and transaction handling for correctness

## Issues Found

### 🔴 CRITICAL: Missing ROLLBACK in catch blocks

Multiple API routes use transactions (BEGIN/COMMIT) but fail to ROLLBACK on error, which can:
- Leave connections in an inconsistent state
- Cause connection pool exhaustion
- Create data inconsistencies
- Block other transactions

**Affected Files**:
1. `/app/api/characters/[id]/background/route.ts` - PUT method
2. `/app/api/characters/[id]/interests/route.ts` - POST method  
3. `/app/api/characters/[id]/communication-patterns/route.ts` - POST method
4. `/app/api/characters/[id]/speech-patterns/route.ts` - POST method
5. `/app/api/characters/[id]/response-style/route.ts` - PUT method

### 🔴 CRITICAL: Client not released on error

Some routes don't release the database client in finally blocks, leading to:
- Connection pool exhaustion
- Memory leaks
- Application hanging under load

### 🟡 WARNING: Multiple Pool instances

Each API route file creates its own Pool instance:
```typescript
const pool = new Pool(getDatabaseConfig())
```

**Issue**: This creates multiple connection pools instead of one shared pool
**Impact**: 
- Inefficient resource usage
- More database connections than necessary
- Harder to tune connection pool settings

---

## Current Patterns

### Pattern 1: DatabaseAdapter (CORRECT ✅)
```typescript
async updateCharacter(id: number, characterData: Partial<Character>): Promise<Character | null> {
  const client = await this.pool.connect();
  try {
    await client.query('BEGIN');
    // ... operations ...
    await client.query('COMMIT');
    return result;
  } catch (error) {
    await client.query('ROLLBACK');  // ✅ CORRECT
    throw error;
  } finally {
    client.release();  // ✅ CORRECT
  }
}
```

### Pattern 2: API Routes (INCORRECT ❌)
```typescript
export async function PUT(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const client = await pool.connect()
    await client.query('BEGIN')
    // ... operations ...
    await client.query('COMMIT')
    client.release()  // ❌ Only on success path
    return NextResponse.json(result)
  } catch (error) {
    // ❌ NO ROLLBACK!
    // ❌ Client not released!
    return NextResponse.json({ error: 'Failed' }, { status: 500 })
  }
}
```

---

## Correct Transaction Pattern

```typescript
export async function PUT(request: NextRequest, { params }: { params: { id: string } }) {
  const resolvedParams = await params
  const characterId = parseInt(resolvedParams.id)
  
  let client;
  try {
    const body = await request.json()
    const { entries } = body
    
    client = await pool.connect()
    await client.query('BEGIN')
    
    // ... database operations ...
    
    await client.query('COMMIT')
    return NextResponse.json(result)
    
  } catch (error) {
    // ✅ ROLLBACK on error
    if (client) {
      try {
        await client.query('ROLLBACK')
      } catch (rollbackError) {
        console.error('Error rolling back transaction:', rollbackError)
      }
    }
    console.error('Error:', error)
    return NextResponse.json({ error: 'Failed' }, { status: 500 })
    
  } finally {
    // ✅ ALWAYS release client
    if (client) {
      client.release()
    }
  }
}
```

---

## Files Requiring Fixes

### High Priority (Transaction + Error Handling)

1. **`/app/api/characters/[id]/background/route.ts`**
   - PUT method: Missing ROLLBACK and finally block
   - GET method: No transaction, but should use try/finally
   - POST method: No transaction, but should use try/finally

2. **`/app/api/characters/[id]/interests/route.ts`**
   - POST method: Missing ROLLBACK and finally block

3. **`/app/api/characters/[id]/communication-patterns/route.ts`**
   - POST method: Missing ROLLBACK and finally block

4. **`/app/api/characters/[id]/speech-patterns/route.ts`**
   - POST method: Missing ROLLBACK and finally block

5. **`/app/api/characters/[id]/response-style/route.ts`**
   - PUT method: Missing ROLLBACK and finally block

---

## Recommended Architecture Changes

### Option 1: Shared Pool Singleton (RECOMMENDED)

Create a single shared pool instance:

```typescript
// src/lib/db-pool.ts
import { Pool } from 'pg'
import { getDatabaseConfig } from './db'

let pool: Pool | null = null

export function getPool(): Pool {
  if (!pool) {
    pool = new Pool({
      ...getDatabaseConfig(),
      max: 20,              // Maximum pool size
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 2000,
    })
    
    pool.on('error', (err) => {
      console.error('Unexpected pool error:', err)
    })
  }
  return pool
}

export async function closePool(): Promise<void> {
  if (pool) {
    await pool.end()
    pool = null
  }
}
```

Then in API routes:
```typescript
import { getPool } from '@/lib/db-pool'

const pool = getPool()  // Reuses same instance across all routes
```

### Option 2: Helper Function for Transactions

```typescript
// src/lib/db-transaction.ts
import { Pool, PoolClient } from 'pg'

export async function withTransaction<T>(
  pool: Pool,
  callback: (client: PoolClient) => Promise<T>
): Promise<T> {
  const client = await pool.connect()
  
  try {
    await client.query('BEGIN')
    const result = await callback(client)
    await client.query('COMMIT')
    return result
  } catch (error) {
    try {
      await client.query('ROLLBACK')
    } catch (rollbackError) {
      console.error('Error rolling back transaction:', rollbackError)
    }
    throw error
  } finally {
    client.release()
  }
}
```

Usage:
```typescript
export async function PUT(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const body = await request.json()
    const characterId = parseInt((await params).id)
    
    const result = await withTransaction(pool, async (client) => {
      // All operations here are in a transaction
      await client.query('DELETE FROM character_background WHERE character_id = $1', [characterId])
      
      const insertedEntries = []
      for (const entry of body.entries) {
        const result = await client.query(/* ... */)
        insertedEntries.push(result.rows[0])
      }
      
      return insertedEntries
    })
    
    return NextResponse.json(result)
  } catch (error) {
    console.error('Error:', error)
    return NextResponse.json({ error: 'Failed' }, { status: 500 })
  }
}
```

---

## Pool Configuration Recommendations

```typescript
const poolConfig = {
  // Connection settings
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || '5432'),
  database: process.env.POSTGRES_DB || 'whisperengine',
  user: process.env.POSTGRES_USER || 'whisperengine',
  password: process.env.POSTGRES_PASSWORD,
  
  // Pool settings
  max: 20,                      // Max connections (tune based on load)
  min: 2,                       // Min idle connections
  idleTimeoutMillis: 30000,     // Close idle connections after 30s
  connectionTimeoutMillis: 2000, // Fail fast if can't get connection
  
  // Application name for monitoring
  application_name: 'cdl-web-ui',
  
  // Statement timeout (prevent long-running queries)
  statement_timeout: 10000,     // 10 seconds
  
  // Keep alive
  keepAlive: true,
  keepAliveInitialDelayMillis: 10000,
}
```

---

## Testing Checklist

After applying fixes:

- [ ] Test successful transaction (should commit)
- [ ] Test failed transaction (should rollback)
- [ ] Test connection pool under load (no exhaustion)
- [ ] Monitor for connection leaks
- [ ] Check database for zombie connections
- [ ] Verify error handling doesn't leave hanging transactions

### Query to check active connections:
```sql
SELECT 
  pid,
  usename,
  application_name,
  client_addr,
  state,
  state_change,
  query
FROM pg_stat_activity
WHERE datname = 'whisperengine'
ORDER BY state_change DESC;
```

---

## Priority Order

1. **🔴 URGENT**: Fix missing ROLLBACK in all transaction routes
2. **🔴 URGENT**: Add finally blocks to release clients
3. **🟡 HIGH**: Implement shared pool singleton
4. **🟡 HIGH**: Add pool configuration and monitoring
5. **🟢 MEDIUM**: Implement transaction helper function
6. **🟢 LOW**: Add connection pool metrics/logging

---

## Files Summary

| File | Has Transaction | ROLLBACK | Finally | Status |
|------|----------------|----------|---------|--------|
| `db.ts` (DatabaseAdapter) | ✅ | ✅ | ✅ | ✅ CORRECT |
| `background/route.ts` | ✅ | ❌ | ❌ | 🔴 BROKEN |
| `interests/route.ts` | ✅ | ❌ | ❌ | 🔴 BROKEN |
| `communication-patterns/route.ts` | ✅ | ❌ | ❌ | 🔴 BROKEN |
| `speech-patterns/route.ts` | ✅ | ❌ | ❌ | 🔴 BROKEN |
| `response-style/route.ts` | ✅ | ❌ | ❌ | 🔴 BROKEN |

---

## Estimated Impact

**Current Risk Level**: 🔴 **HIGH**

- Under normal load: Likely working (auto-rollback on connection close)
- Under high load: Connection pool exhaustion likely
- On errors: Potential data inconsistencies
- Memory: Slow connection leaks over time

**After Fixes**: 🟢 **LOW**

- Proper transaction handling
- No connection leaks
- Predictable behavior under load
- Better error recovery
