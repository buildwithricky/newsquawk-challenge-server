#!/bin/sh

export PGUSER="postgres"

# Create database newsquak
psql -c "CREATE DATABASE newsquak;"

# Connect to newsquak and run table creation SQL
psql newsquak << EOF
-- Enable uuid extension if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create truths table
CREATE TABLE IF NOT EXISTS truths (
    id VARCHAR PRIMARY KEY,
    content TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    url TEXT NOT NULL,
    media_urls TEXT[] -- optional array of media URLs
);
EOF
