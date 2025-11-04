-- Migration: allowed_model (String) → allowed_models (JSONB array)
-- Purpose: Allow users (especially admins) to have access to multiple models

-- Step 1: Add new column
ALTER TABLE users ADD COLUMN IF NOT EXISTS allowed_models JSONB DEFAULT '[]'::jsonb;

-- Step 2: Migrate existing data
-- Convert single allowed_model to array format
UPDATE users
SET allowed_models = CASE
    WHEN allowed_model IS NOT NULL THEN jsonb_build_array(allowed_model)
    ELSE '[]'::jsonb
END
WHERE allowed_models = '[]'::jsonb;

-- Step 3: Grant all models to superusers
UPDATE users
SET allowed_models = '["Qwen235B", "Qwen32B"]'::jsonb
WHERE is_superuser = true AND gpt_access_granted = true;

-- Step 4: Drop old column (commented out for safety - uncomment after verification)
-- ALTER TABLE users DROP COLUMN IF EXISTS allowed_model;

-- Verification query
-- SELECT
--     id,
--     username,
--     is_superuser,
--     gpt_access_granted,
--     allowed_model,
--     allowed_models
-- FROM users
-- WHERE gpt_access_granted = true
-- LIMIT 20;
