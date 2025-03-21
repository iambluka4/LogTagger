-- Check if admin exists and update password
DO $$
DECLARE
    admin_exists BOOLEAN;
    -- This is the bcrypt hash for 'admin' - generated with appropriate salt
    admin_password_hash VARCHAR := '$2b$12$QlKth8FeVMxEOsK9VLBsHuS9uARB.C9EH/BfMOLLGiRQNtYgd2Tai';
BEGIN
    SELECT EXISTS(SELECT 1 FROM users WHERE role = 'ADMIN') INTO admin_exists;
    
    IF admin_exists THEN
        -- Update existing admin password
        UPDATE users SET password = admin_password_hash WHERE role = 'ADMIN';
        RAISE NOTICE 'Admin password reset to "admin"';
    ELSE
        -- Create new admin user
        INSERT INTO users (username, password, description, role, created_at)
        VALUES ('admin', admin_password_hash, 'Default administrator account', 'ADMIN', NOW());
        RAISE NOTICE 'Created new admin user with password "admin"';
    END IF;
END $$;
