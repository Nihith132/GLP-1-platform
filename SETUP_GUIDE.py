"""
Quick Setup Guide for GLP-1 Platform
Follow these steps in order
"""

# ===== STEP 1: INSTALL PYTHON DEPENDENCIES =====
print("Step 1: Install Python dependencies")
print("Command: pip install -r backend/requirements.txt")
print()

# ===== STEP 2: SETUP AWS S3 =====
print("Step 2: Setup AWS S3")
print("1. Go to https://aws.amazon.com/")
print("2. Sign in and go to S3 service")
print("3. Create a bucket named: glp1-raw-labels")
print("4. Go to IAM → Users → Create user")
print("5. Attach policy: AmazonS3FullAccess")
print("6. Create access key → Copy ACCESS_KEY and SECRET_KEY")
print()

# ===== STEP 3: SETUP SUPABASE (PostgreSQL) =====
print("Step 3: Setup Supabase (Free PostgreSQL)")
print("1. Go to https://supabase.com/")
print("2. Create account and new project")
print("3. Go to Settings → Database")
print("4. Copy the 'Connection String' (URI format)")
print("   Example: postgresql://postgres:[password]@db.xxx.supabase.co:5432/postgres")
print()

# ===== STEP 4: SETUP PINECONE =====
print("Step 4: Setup Pinecone (Vector Database)")
print("1. Go to https://app.pinecone.io/")
print("2. Sign up for free tier")
print("3. Create new index:")
print("   - Name: glp1-embeddings")
print("   - Dimensions: 384 (for all-MiniLM-L6-v2 model)")
print("   - Metric: cosine")
print("   - Environment: gcp-starter (free)")
print("4. Copy API key from dashboard")
print()

# ===== STEP 5: SETUP GROQ =====
print("Step 5: Setup Groq (LLM for RAG)")
print("1. Go to https://console.groq.com/")
print("2. Sign up (free tier available)")
print("3. Create API key")
print("4. Copy the key")
print()

# ===== STEP 6: CONFIGURE ENVIRONMENT =====
print("Step 6: Configure .env file")
print("1. Copy .env.example to .env")
print("2. Fill in all the credentials from above steps")
print()

# ===== STEP 7: DOWNLOAD FDA FILES =====
print("Step 7: Download FDA Drug Label Files")
print("1. Go to https://dailymed.nlm.nih.gov/")
print("2. Search for each drug:")
drugs = [
    "Ozempic (semaglutide)",
    "Mounjaro (tirzepatide)",
    "Wegovy (semaglutide)",
    "Saxenda (liraglutide)",
    "Victoza (liraglutide)",
    "Trulicity (dulaglutide)",
    "Bydureon (exenatide)",
    "Byetta (exenatide)",
    "Rybelsus (semaglutide)",
    "Adlyxin (lixisenatide)"
]
for i, drug in enumerate(drugs, 1):
    print(f"   {i}. {drug}")
print("3. For each drug, click 'Download SPL' and save the .zip file")
print("4. Save all files to: data/raw/")
print()

print("=" * 60)
print("Once all steps are complete, you're ready to run the ETL pipeline!")
print("=" * 60)
