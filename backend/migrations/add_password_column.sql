-- Check if password column already exists
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 
    FROM information_schema.columns 
    WHERE table_name='users' AND column_name='password'
  ) THEN
    -- Add password column if it doesn't exist
    ALTER TABLE users ADD COLUMN password VARCHAR(255);
    RAISE NOTICE 'Password column added successfully';
  ELSE
    RAISE NOTICE 'Password column already exists';
  END IF;
END $$;
