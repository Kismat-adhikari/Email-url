#!/usr/bin/env python3
"""
Setup Admin Schema in Supabase
Runs the admin_schema.sql file to create admin tables
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

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

def run_admin_schema():
    """Run the admin schema SQL file using Supabase RPC"""
    try:
        # Read the schema file
        with open('admin_schema.sql', 'r') as f:
            schema_sql = f.read()
        
        # Get Supabase client
        supabase = get_supabase_client()
        
        logger.info("Running admin schema setup via Supabase...")
        
        # Split the SQL into individual statements
        statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
        
        success_count = 0
        for i, statement in enumerate(statements):
            if not statement:
                continue
                
            try:
                # Use Supabase RPC to execute SQL
                result = supabase.rpc('exec_sql', {'sql': statement}).execute()
                success_count += 1
                logger.info(f"✅ Executed statement {i+1}/{len(statements)}")
            except Exception as e:
                # Some statements might fail if tables already exist, that's OK
                if 'already exists' in str(e).lower():
                    logger.info(f"⚠️  Statement {i+1} skipped (already exists): {str(e)[:100]}...")
                else:
                    logger.warning(f"❌ Statement {i+1} failed: {str(e)[:100]}...")
        
        logger.info(f"✅ Admin schema setup completed! ({success_count}/{len(statements)} statements executed)")
        
        # Try to verify admin user was created
        try:
            result = supabase.table('admin_users').select('email, role').eq('email', 'admin@emailvalidator.com').execute()
            if result.data:
                admin = result.data[0]
                logger.info(f"✅ Default admin user found: {admin['email']} ({admin['role']})")
                logger.info("🔑 Default login: admin@emailvalidator.com / admin123")
                logger.info("⚠️  IMPORTANT: Change the default password immediately!")
            else:
                logger.warning("❌ Default admin user not found - you may need to create it manually")
        except Exception as e:
            logger.warning(f"Could not verify admin user: {e}")
            
    except FileNotFoundError:
        logger.error("❌ admin_schema.sql file not found")
        return False
    except Exception as e:
        logger.error(f"❌ Schema setup failed: {e}")
        return False
    
    return True

if __name__ == '__main__':
    print("🛡️  Setting up Admin Control System...")
    print("=" * 50)
    
    success = run_admin_schema()
    
    if success:
        print("\n✅ Admin system setup completed!")
        print("\n🚀 Next steps:")
        print("1. Start the Flask backend: python app_anon_history.py")
        print("2. Start the React frontend: cd frontend && npm start")
        print("3. Access admin panel: http://localhost:3000/admin/login")
        print("4. Login with: admin@emailvalidator.com / admin123")
        print("5. CHANGE THE DEFAULT PASSWORD!")
    else:
        print("\n❌ Setup failed. Check the logs above.")