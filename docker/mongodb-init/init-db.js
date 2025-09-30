// MongoDB initialization script for Poon AI Service
// This script creates the database, user, and indexes

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

print('MongoDB initialization completed successfully');
