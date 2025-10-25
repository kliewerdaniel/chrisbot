-- BOT Platform Database Initialization
-- This script creates the initial database schema for session management

-- Create database if it doesn't exist (done via environment variables)

-- Create sessions table for enhanced session persistence
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL DEFAULT 'Untitled Chat',
    messages JSONB NOT NULL DEFAULT '[]'::jsonb,
    model TEXT NOT NULL,
    prompt_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id TEXT, -- For future multi-user support
    is_deleted BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create conversation_branches table for branching support
CREATE TABLE IF NOT EXISTS conversation_branches (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,
    parent_message_id TEXT NOT NULL,
    branch_name TEXT,
    messages JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create system_prompts table for prompt management
CREATE TABLE IF NOT EXISTS system_prompts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    content TEXT NOT NULL,
    description TEXT,
    category TEXT,
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_default BOOLEAN DEFAULT FALSE,
    usage_count INTEGER DEFAULT 0,
    user_id TEXT, -- For future multi-user support
    is_deleted BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create file_uploads table for attachment tracking
CREATE TABLE IF NOT EXISTS file_uploads (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    original_name TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    storage_path TEXT,
    content_hash TEXT,
    processing_status TEXT DEFAULT 'pending',
    processing_result JSONB,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create user_preferences table for UI settings
CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    user_id TEXT, -- For future multi-user support
    preference_key TEXT NOT NULL,
    preference_value JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, preference_key)
);

-- Create analytics_events table for usage tracking
CREATE TABLE IF NOT EXISTS analytics_events (
    id SERIAL PRIMARY KEY,
    event_type TEXT NOT NULL,
    event_data JSONB DEFAULT '{}'::jsonb,
    user_id TEXT,
    session_id TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_agent TEXT,
    ip_address INET
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_updated_at ON sessions(updated_at);

CREATE INDEX IF NOT EXISTS idx_conversation_branches_session_id ON conversation_branches(session_id);
CREATE INDEX IF NOT EXISTS idx_conversation_branches_active ON conversation_branches(is_active) WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_system_prompts_category ON system_prompts(category) WHERE category IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_system_prompts_tags ON system_prompts USING GIN (tags);
CREATE INDEX IF NOT EXISTS idx_system_prompts_user_id ON system_prompts(user_id) WHERE user_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_file_uploads_session_id ON file_uploads(session_id);
CREATE INDEX IF NOT EXISTS idx_file_uploads_processing_status ON file_uploads(processing_status);
CREATE INDEX IF NOT EXISTS idx_file_uploads_expires_at ON file_uploads(expires_at) WHERE expires_at IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id) WHERE user_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_analytics_events_type_timestamp ON analytics_events(event_type, timestamp);
CREATE INDEX IF NOT EXISTS idx_analytics_events_user_id ON analytics_events(user_id) WHERE user_id IS NOT NULL;

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for automatic updated_at updates
CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_prompts_updated_at BEFORE UPDATE ON system_prompts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default system prompts
INSERT INTO system_prompts (id, name, content, description, category, is_default) VALUES
('default-assistant', 'General Assistant', 'You are a helpful AI assistant. Provide accurate, useful, and engaging responses to user queries.', 'A general-purpose AI assistant prompt', 'General', true),
('code-expert', 'Code Expert', 'You are an expert software developer. Provide detailed, accurate code examples and technical explanations. Always include comments and best practices.', 'Specialized for coding and development tasks', 'Technical', false),
('creative-writer', 'Creative Writer', 'You are a creative writing assistant. Help users develop stories, poems, and creative content with engaging and imaginative responses.', 'For creative writing and storytelling', 'Creative', false),
('data-analyst', 'Data Analyst', 'You are a data analysis expert. Help users understand data, statistics, and insights. Explain complex concepts in simple terms.', 'For data analysis and interpretation', 'Technical', false)
ON CONFLICT (id) DO NOTHING;

-- Create a view for active sessions
CREATE OR REPLACE VIEW active_sessions AS
SELECT * FROM sessions WHERE is_deleted = FALSE;

-- Create a view for recent sessions
CREATE OR REPLACE VIEW recent_sessions AS
SELECT * FROM sessions
WHERE is_deleted = FALSE
AND updated_at > CURRENT_TIMESTAMP - INTERVAL '30 days'
ORDER BY updated_at DESC;

-- Grant permissions for the application user
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO bot_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO bot_user;

-- Set up row-level security (for future multi-user support)
-- ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE system_prompts ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE file_uploads ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE analytics_events ENABLE ROW LEVEL SECURITY;

-- Create policies (examples for future implementation)
-- CREATE POLICY sessions_user_policy ON sessions
--     FOR ALL USING (user_id IS NULL OR user_id = current_user_id());

-- Comment on tables for documentation
COMMENT ON TABLE sessions IS 'User chat sessions with message history';
COMMENT ON TABLE conversation_branches IS 'Conversation branches for alternative response paths';
COMMENT ON TABLE system_prompts IS 'User-defined system prompts and templates';
COMMENT ON TABLE file_uploads IS 'Uploaded files and their processing status';
COMMENT ON TABLE user_preferences IS 'User UI and application preferences';
COMMENT ON TABLE analytics_events IS 'Usage analytics and event tracking';
