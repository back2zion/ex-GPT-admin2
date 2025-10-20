-- Create approval workflow tables

-- Document Change Requests
CREATE TABLE IF NOT EXISTS document_change_requests (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    legacy_id VARCHAR(100),
    change_type VARCHAR(20) NOT NULL CHECK (change_type IN ('new', 'modified', 'deleted')),
    old_data JSONB,
    new_data JSONB,
    diff_summary TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'completed')),
    requester_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    approved_at VARCHAR(50),
    applied_at VARCHAR(50),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_change_requests_status ON document_change_requests(status);
CREATE INDEX idx_change_requests_document_id ON document_change_requests(document_id);

-- Approval Steps
CREATE TABLE IF NOT EXISTS approval_steps (
    id SERIAL PRIMARY KEY,
    change_request_id INTEGER NOT NULL REFERENCES document_change_requests(id) ON DELETE CASCADE,
    level INTEGER NOT NULL,
    approver_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    approver_name VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'skipped')),
    approved_at VARCHAR(50),
    comment TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_approval_steps_request_id ON approval_steps(change_request_id);
CREATE INDEX idx_approval_steps_approver_id ON approval_steps(approver_id);
CREATE INDEX idx_approval_steps_status ON approval_steps(status);
