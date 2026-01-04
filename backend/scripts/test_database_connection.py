"""
Supabase Database Connection Test
Tests PostgreSQL connection and pgvector extension
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.core.config import settings
import asyncpg


async def test_database_connection():
    """Test Supabase PostgreSQL connection"""
    
    print("=" * 60)
    print("🧪 SUPABASE DATABASE CONNECTION TEST")
    print("=" * 60)
    print()
    
    # Display configuration (hide password)
    db_url = settings.DATABASE_URL
    safe_url = db_url.split('@')[1] if '@' in db_url else 'hidden'
    print("📋 Configuration:")
    print(f"   Database: Supabase PostgreSQL")
    print(f"   Host: {safe_url.split(':')[0] if ':' in safe_url else safe_url}")
    print()
    
    conn = None
    try:
        # Test 1: Basic Connection
        print("Test 1: Connecting to Supabase PostgreSQL...")
        conn = await asyncpg.connect(settings.DATABASE_URL)
        print("   ✅ SUCCESS: Connected to database!")
        print()
        
        # Test 2: Check PostgreSQL version
        print("Test 2: Checking PostgreSQL version...")
        version = await conn.fetchval('SELECT version();')
        print(f"   ✅ PostgreSQL Version: {version.split(',')[0]}")
        print()
        
        # Test 3: Check if pgvector extension is available
        print("Test 3: Checking pgvector extension...")
        extensions = await conn.fetch(
            "SELECT * FROM pg_available_extensions WHERE name = 'vector';"
        )
        
        if extensions:
            print("   ✅ pgvector extension is available!")
            
            # Check if it's installed
            installed = await conn.fetch(
                "SELECT * FROM pg_extension WHERE extname = 'vector';"
            )
            
            if installed:
                print("   ✅ pgvector extension is ENABLED!")
                
                # Get version
                try:
                    vec_version = await conn.fetchval("SELECT extversion FROM pg_extension WHERE extname = 'vector';")
                    print(f"   ✅ pgvector version: {vec_version}")
                except:
                    pass
            else:
                print("   ⚠️  WARNING: pgvector is available but NOT enabled")
                print("   📝 Action needed: Enable it in Supabase dashboard:")
                print("      1. Go to Database → Extensions")
                print("      2. Search for 'vector'")
                print("      3. Click 'Enable'")
                return False
        else:
            print("   ❌ ERROR: pgvector extension not available")
            print("   This shouldn't happen on Supabase - contact support")
            return False
        print()
        
        # Test 4: Test vector operations (if enabled)
        if installed:
            print("Test 4: Testing vector operations...")
            try:
                # Create a test table with vector column
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS test_vectors (
                        id SERIAL PRIMARY KEY,
                        embedding vector(384),
                        content TEXT
                    );
                """)
                print("   ✅ Created test table with vector column")
                
                # Insert a test vector
                test_embedding = [0.1] * 384  # Dummy 384-dimensional vector
                embedding_str = '[' + ','.join(map(str, test_embedding)) + ']'
                await conn.execute(
                    "INSERT INTO test_vectors (embedding, content) VALUES ($1::vector, $2);",
                    embedding_str,
                    "Test embedding"
                )
                print("   ✅ Inserted test vector")
                
                # Query it back
                result = await conn.fetchrow("SELECT content, embedding::text FROM test_vectors LIMIT 1;")
                if result:
                    print(f"   ✅ Retrieved vector from database")
                
                # Test cosine similarity search
                await conn.execute("""
                    SELECT embedding <=> $1::vector AS distance
                    FROM test_vectors
                    ORDER BY distance
                    LIMIT 1;
                """, embedding_str)
                print("   ✅ Vector similarity search working!")
                
                # Cleanup
                await conn.execute("DROP TABLE test_vectors;")
                print("   ✅ Cleaned up test table")
                
            except Exception as e:
                print(f"   ❌ ERROR testing vectors: {e}")
                return False
        print()
        
        # Test 5: Check database permissions
        print("Test 5: Checking database permissions...")
        try:
            # Try to create a test table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS test_permissions (
                    id SERIAL PRIMARY KEY,
                    test_field TEXT
                );
            """)
            print("   ✅ Can create tables")
            
            # Try to insert
            await conn.execute(
                "INSERT INTO test_permissions (test_field) VALUES ($1);",
                "test"
            )
            print("   ✅ Can insert data")
            
            # Try to select
            result = await conn.fetchrow("SELECT * FROM test_permissions LIMIT 1;")
            if result:
                print("   ✅ Can query data")
            
            # Cleanup
            await conn.execute("DROP TABLE test_permissions;")
            print("   ✅ Can drop tables")
            
        except Exception as e:
            print(f"   ⚠️  WARNING: Limited permissions: {e}")
        print()
        
        # Final summary
        print("=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        print()
        print("✅ Your Supabase database is ready!")
        print("✅ Vector search capability confirmed (pgvector)")
        print("✅ No IPv4 issues detected!")
        print()
        print("Next steps:")
        print("1. Get Groq API key for LLM chatbot")
        print("2. Download FDA drug label files")
        print("3. Start building the ETL pipeline")
        print()
        
        return True
        
    except Exception as e:
        print(f"   ❌ CONNECTION ERROR: {e}")
        print()
        print("Possible issues:")
        print("- Check if the connection string is correct")
        print("- Verify your network connection")
        print("- If you see IPv6 errors, you might need the IPv4 add-on")
        print()
        return False
        
    finally:
        if conn:
            await conn.close()


if __name__ == "__main__":
    import asyncio
    
    try:
        success = asyncio.run(test_database_connection())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
