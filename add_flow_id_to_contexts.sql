-- Migration: Add flow_id column to contexts table

-- Step 1: Add flow_id column with a default value
ALTER TABLE contexts
ADD COLUMN flow_id INTEGER DEFAULT 1;

-- Step 2: Set flow_id based on active flow (if exists)
UPDATE contexts
SET flow_id = (SELECT id FROM flows WHERE is_active = true LIMIT 1)
WHERE flow_id = 1;

-- Step 3: Drop the old primary key
ALTER TABLE contexts
DROP CONSTRAINT contexts_pkey;

-- Step 4: Create new composite primary key
ALTER TABLE contexts
ADD CONSTRAINT contexts_pkey PRIMARY KEY (msisdn, flow_id);

-- Step 5: Make flow_id NOT NULL and remove default
ALTER TABLE contexts
ALTER COLUMN flow_id SET NOT NULL,
ALTER COLUMN flow_id DROP DEFAULT;

-- Step 6: Add foreign key to flows table
ALTER TABLE contexts
ADD CONSTRAINT contexts_flow_id_fkey
FOREIGN KEY (flow_id) REFERENCES flows(id) ON DELETE CASCADE;
