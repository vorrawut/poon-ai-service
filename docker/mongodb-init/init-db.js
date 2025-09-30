// MongoDB initialization script for Poon AI Service
// This script creates the database, user, and indexes

// First authenticate as admin
db = db.getSiblingDB('admin');
db.auth('admin', 'password123');

// Switch to the spending_db database
db = db.getSiblingDB('spending_db');

// Create a user for the application
db.createUser({
  user: 'poon_user',
  pwd: 'poon_password',
  roles: [
    {
      role: 'readWrite',
      db: 'spending_db'
    }
  ]
});

// Create the spending_entries collection
db.createCollection('spending_entries');

// Create indexes for better performance
db.spending_entries.createIndex({ "entry_id": 1 }, { unique: true });
db.spending_entries.createIndex({ "category": 1 });
db.spending_entries.createIndex({ "merchant": 1 });
db.spending_entries.createIndex({ "transaction_date": 1 });
db.spending_entries.createIndex({ "created_at": 1 });
db.spending_entries.createIndex({ "transaction_date": 1, "category": 1 });

// Create the AI training data collection
db.createCollection('ai_training_data');

// Create indexes for AI training data
db.ai_training_data.createIndex({ "id": 1 }, { unique: true });
db.ai_training_data.createIndex({ "status": 1 });
db.ai_training_data.createIndex({ "language": 1 });
db.ai_training_data.createIndex({ "accuracy_score": 1 });
db.ai_training_data.createIndex({ "ai_confidence": 1 });
db.ai_training_data.createIndex({ "feedback_provided": 1 });
db.ai_training_data.createIndex({ "created_at": 1 });
db.ai_training_data.createIndex({ "updated_at": 1 });
db.ai_training_data.createIndex({ "user_id": 1 });
db.ai_training_data.createIndex({ "session_id": 1 });
db.ai_training_data.createIndex({ "model_version": 1 });

// Compound indexes for common queries
db.ai_training_data.createIndex({ "status": 1, "created_at": -1 });
db.ai_training_data.createIndex({ "language": 1, "status": 1 });
db.ai_training_data.createIndex({ "accuracy_score": 1, "created_at": -1 });
db.ai_training_data.createIndex({ "feedback_provided": 1, "status": 1 });

// Text index for similarity search
db.ai_training_data.createIndex({ "input_text": "text" });

print('MongoDB initialization completed successfully with AI training collections');
