-- Migration: Fix contexts table to use composite key (msisdn, flow_id)

-- Step 1: Set flow_id for all NULL records with the active flow
UPDATE contexts
SET flow_id = (SELECT id FROM flows WHERE is_active = true LIMIT 1)
WHERE flow_id IS NULL;

-- Step 2: If still NULL (no active flow), use the first flow
UPDATE contexts
SET flow_id = (SELECT id FROM flows ORDER BY id LIMIT 1)
WHERE flow_id IS NULL;

-- Step 3: Delete records without flow_id (if no flows exist)
DELETE FROM contexts WHERE flow_id IS NULL;

-- Step 4: Drop old unique index on msisdn only
DROP INDEX IF EXISTS contexts_msisdn_idx;

-- Step 5: Drop one of the duplicate foreign keys
ALTER TABLE contexts DROP CONSTRAINT IF EXISTS fk_contexts_flow_id;

-- Step 6: Make flow_id NOT NULL
ALTER TABLE contexts ALTER COLUMN flow_id SET NOT NULL;

-- Step 7: Add composite primary key
ALTER TABLE contexts ADD CONSTRAINT contexts_pkey PRIMARY KEY (msisdn, flow_id);
