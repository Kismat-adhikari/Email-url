#!/usr/bin/env python3
"""
Manual Admin Setup for Supabase
Creates admin tables manually using Supabase client
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv
import logging
import bcrypt

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_supabase_client():
    """Get Supabase client"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env file")
    
    return create_client(url, key)

def create_admin_tables():
    """Create admin tables manually"""
    try:
        supabase = get_supabase_client()
        logger.info("Setting up admin system manually...")
        
        # Check if admin_users table exists by trying to query it
        try:
            result = supabase.table('admin_users').select('id').limit(1).execute()
            logger.info("✅ Admin tables already exist!")
            
            # Check if default admin exists
            admin_result = supabase.table('admin_users').select('email, role').eq('email', 'admin@emailvalidator.com').execute()
            if admin_result.data:
                admin = admin_result.data[0]
                logger.info(f"✅ Default admin user found: {admin['email']} ({admin['role']})")
                logger.info("🔑 Login: admin@emailvalidator.com / admin123")
                return True
            else:
                logger.info("Creating default admin user...")
                create_default_admin(supabase)
                return True
                
        except Exception as e:
            logger.info("Admin tables don't exist yet. This is expected for first setup.")
            logger.info("Please create the admin tables manually in Supabase SQL Editor:")
            
            print("\n" + "="*70)
            print("MANUAL SETUP INSTRUCTIONS")
            print("="*70)
            print("\n1. Go to your Supabase project dashboard")
            print("2. Navigate to SQL Editor")
            print("3. Create a new query and paste the following SQL:")
            print("\n" + "-"*50)
            
            # Print the essential SQL for manual creation
            sql_commands = [
                """
-- 1. Create admin_users table
CREATE TABLE IF NOT EXISTS admin_users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'admin' CHECK (role IN ('super_admin', 'admin', 'moderator')),
    permissions JSONB DEFAULT '[]',
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES admin_users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);""",
                """
-- 2. Create admin_sessions table
CREATE TABLE IF NOT EXISTS admin_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    admin_id UUID REFERENCES admin_users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);""",
                """
-- 3. Create admin_activity_logs table
CREATE TABLE IF NOT EXISTS admin_activity_logs (
    id SERIAL PRIMARY KEY,
    admin_id UUID REFERENCES admin_users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);""",
                """
-- 4. Create system_metrics table
CREATE TABLE IF NOT EXISTS system_metrics (
    id SERIAL PRIMARY KEY,
    metric_type VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    value DECIMAL(15,4) NOT NULL,
    unit VARCHAR(20),
    metadata JSONB,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);""",
                """
-- 5. Add admin fields to users table (if not exists)
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_suspended BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS suspended_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS suspended_by UUID REFERENCES admin_users(id) ON DELETE SET NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS suspension_reason TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS admin_notes TEXT;""",
                """
-- 6. Create indexes
CREATE INDEX IF NOT EXISTS idx_admin_users_email ON admin_users(email);
CREATE INDEX IF NOT EXISTS idx_admin_users_role ON admin_users(role);
CREATE INDEX IF NOT EXISTS idx_admin_sessions_admin_id ON admin_sessions(admin_id);
CREATE INDEX IF NOT EXISTS idx_admin_activity_admin_id ON admin_activity_logs(admin_id);""",
                """
-- 7. Create dashboard view
CREATE OR REPLACE VIEW admin_dashboard_stats AS
SELECT 
    (SELECT COUNT(*) FROM users) as total_users,
    (SELECT COUNT(*) FROM users WHERE created_at >= CURRENT_DATE) as users_today,
    (SELECT COUNT(*) FROM users WHERE created_at >= CURRENT_DATE - INTERVAL '7 days') as users_this_week,
    (SELECT COUNT(*) FROM users WHERE subscription_tier = 'free') as free_users,
    (SELECT COUNT(*) FROM users WHERE subscription_tier != 'free') as paid_users,
    (SELECT COUNT(*) FROM users WHERE is_suspended = true) as suspended_users,
    (SELECT COUNT(*) FROM email_validations) as total_validations,
    (SELECT COUNT(*) FROM email_validations WHERE validated_at >= CURRENT_DATE) as validations_today,
    (SELECT COUNT(*) FROM email_validations WHERE valid = true) as valid_emails,
    (SELECT COUNT(*) FROM email_validations WHERE valid = false) as invalid_emails,
    (SELECT COUNT(*) FROM admin_activity_logs WHERE created_at >= CURRENT_DATE) as admin_actions_today,
    (SELECT COUNT(DISTINCT admin_id) FROM admin_sessions WHERE is_active = true) as active_admins;""",
                """
-- 8. Insert default admin user (password: admin123)
INSERT INTO admin_users (
    email, 
    password_hash, 
    role, 
    first_name, 
    last_name, 
    permissions
) VALUES (
    'admin@emailvalidator.com',
    '$2b$12$LQv3c1yqBwEHFl5aysHdsOecr0Cz/qt6NzHElYos.RSUuu9OVShxC',
    'super_admin',
    'Super',
    'Admin',
    '["*"]'::jsonb
) ON CONFLICT (email) DO NOTHING;"""
            ]
            
            for i, cmd in enumerate(sql_commands, 1):
                print(f"\n-- Command {i}:")
                print(cmd.strip())
            
            print("\n" + "-"*50)
            print("\n4. Run each command one by one")
            print("5. After successful execution, run this script again")
            print("\n" + "="*70)
            
            return False
            
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        return False

def create_default_admin(supabase):
    """Create default admin user"""
    try:
        # Hash the default password
        password = "admin123"
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Insert admin user
        result = supabase.table('admin_users').insert({
            'email': 'admin@emailvalidator.com',
            'password_hash': password_hash,
            'role': 'super_admin',
            'first_name': 'Super',
            'last_name': 'Admin',
            'permissions': ['*']
        }).execute()
        
        if result.data:
            logger.info("✅ Default admin user created successfully!")
            logger.info("🔑 Login: admin@emailvalidator.com / admin123")
            logger.info("⚠️  IMPORTANT: Change the password after first login!")
            return True
        else:
            logger.error("❌ Failed to create default admin user")
            return False
            
    except Exception as e:
        logger.error(f"Failed to create admin user: {e}")
        return False

if __name__ == '__main__':
    print("🛡️  Setting up Admin Control System...")
    print("=" * 50)
    
    success = create_admin_tables()
    
    if success:
        print("\n✅ Admin system setup completed!")
        print("\n🚀 Next steps:")
        print("1. Start the Flask backend: python app_anon_history.py")
        print("2. Start the React frontend: cd frontend && npm start")
        print("3. Access admin panel: http://localhost:3000/admin/login")
        print("4. Login with: admin@emailvalidator.com / admin123")
        print("5. CHANGE THE DEFAULT PASSWORD!")
    else:
        print("\n⚠️  Manual setup required. Follow the instructions above.")