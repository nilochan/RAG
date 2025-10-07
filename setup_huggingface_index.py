"""
Create Pinecone index for HuggingFace embeddings (384 dimensions)
Run this ONCE before deploying to Railway
"""
import os
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_huggingface_index():
    """Create educational-docs-hf index for HuggingFace embeddings"""

    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        print("❌ PINECONE_API_KEY not found in environment variables!")
        print("Please add it to your .env file")
        return

    try:
        # Initialize Pinecone
        pc = Pinecone(api_key=api_key)

        index_name = "educational-docs-hf"

        # Check if index already exists
        existing_indexes = pc.list_indexes()
        index_names = [idx.name for idx in existing_indexes]

        if index_name in index_names:
            print(f"✅ Index '{index_name}' already exists!")

            # Get index info
            index = pc.Index(index_name)
            stats = index.describe_index_stats()
            print(f"📊 Current stats: {stats['total_vector_count']} vectors")

            response = input("\n⚠️  Do you want to DELETE and recreate the index? (yes/no): ")
            if response.lower() != 'yes':
                print("Keeping existing index.")
                return

            print(f"🗑️  Deleting existing index '{index_name}'...")
            pc.delete_index(index_name)
            print("✅ Index deleted")

        # Create new index for HuggingFace embeddings
        print(f"\n🚀 Creating new index '{index_name}'...")
        print("📊 Dimensions: 384 (HuggingFace all-MiniLM-L6-v2)")
        print("🌍 Region: us-east-1 (Serverless)")

        pc.create_index(
            name=index_name,
            dimension=384,  # HuggingFace all-MiniLM-L6-v2 dimensions
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )

        print(f"✅ Index '{index_name}' created successfully!")
        print("\n📋 Next steps:")
        print("1. Make sure PINECONE_API_KEY is set in Railway environment variables")
        print("2. Make sure PINECONE_HOST is set in Railway (get from Pinecone dashboard)")
        print("3. Deploy your backend to Railway")
        print("4. Upload documents - they'll use FREE HuggingFace embeddings!")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nPlease check:")
        print("1. Your PINECONE_API_KEY is valid")
        print("2. You have internet connection")
        print("3. Your Pinecone account has available indexes")

if __name__ == "__main__":
    print("=" * 60)
    print("🤗 HuggingFace Embeddings Pinecone Index Setup")
    print("=" * 60)
    create_huggingface_index()
