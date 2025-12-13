-- Create shared_results table for cross-user sharing functionality
-- Run this in your Supabase SQL editor

CREATE TABLE IF NOT EXISTS shared_results (
    id BIGSERIAL PRIMARY KEY,
    share_id TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    results JSONB NOT NULL DEFAULT '[]',
    domain_statistics JSONB,
    shared_by TEXT DEFAULT 'Anonymous User',
    is_public BOOLEAN DEFAULT true,
    view_count INTEGER DEFAULT 0,
    last_viewed_at TIMESTAMPTZ
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_shared_results_share_id ON shared_results(share_id);
CREATE INDEX IF NOT EXISTS idx_shared_results_expires_at ON shared_results(expires_at);
CREATE INDEX IF NOT EXISTS idx_shared_results_created_at ON shared_results(created_at);

-- Enable Row Level Security (optional, for additional security)
ALTER TABLE shared_results ENABLE ROW LEVEL SECURITY;

-- Create policy to allow public read access (anyone can view shared results)
CREATE POLICY "Allow public read access to shared results" ON shared_results
    FOR SELECT USING (is_public = true);

-- Create policy to allow anyone to insert shared results
CREATE POLICY "Allow public insert of shared results" ON shared_results
    FOR INSERT WITH CHECK (true);

-- Create policy to allow cleanup of expired results
CREATE POLICY "Allow cleanup of expired results" ON shared_results
    FOR DELETE USING (expires_at < NOW());

-- Grant necessary permissions
GRANT SELECT, INSERT, DELETE ON shared_results TO anon;
GRANT SELECT, INSERT, DELETE ON shared_results TO authenticated;
GRANT USAGE ON SEQUENCE shared_results_id_seq TO anon;
GRANT USAGE ON SEQUENCE shared_results_id_seq TO authenticated;

-- Optional: Create a function to automatically clean up expired shares
CREATE OR REPLACE FUNCTION cleanup_expired_shares()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM shared_results WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Optional: Create a scheduled job to run cleanup daily (requires pg_cron extension)
-- SELECT cron.schedule('cleanup-expired-shares', '0 2 * * *', 'SELECT cleanup_expired_shares();');

COMMENT ON TABLE shared_results IS 'Stores shared batch validation results for cross-user sharing';
COMMENT ON COLUMN shared_results.share_id IS 'Unique identifier for the shared link';
COMMENT ON COLUMN shared_results.expires_at IS 'When this shared result expires (7 days from creation)';
COMMENT ON COLUMN shared_results.metadata IS 'Batch validation metadata (counts, processing time, etc.)';
COMMENT ON COLUMN shared_results.results IS 'Array of individual email validation results';
COMMENT ON COLUMN shared_results.domain_statistics IS 'Domain analysis and statistics';
COMMENT ON COLUMN shared_results.shared_by IS 'Name of user who created the share (or Anonymous)';
COMMENT ON COLUMN shared_results.is_public IS 'Whether this share is publicly accessible';
COMMENT ON COLUMN shared_results.view_count IS 'Number of times this share has been viewed';
COMMENT ON COLUMN shared_results.last_viewed_at IS 'Last time this share was accessed';