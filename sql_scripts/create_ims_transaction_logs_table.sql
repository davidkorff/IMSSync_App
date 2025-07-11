-- Create ims_transaction_logs table for tracking IMS integration transactions
-- This table tracks all transactions sent from Triton to IMS

CREATE TABLE IF NOT EXISTS ims_transaction_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    transaction_type VARCHAR(50) NOT NULL,  -- 'binding', 'midterm_endorsement', 'cancellation'
    resource_type VARCHAR(50) NOT NULL,     -- 'opportunity', 'endorsement', etc.
    resource_id BIGINT NOT NULL,            -- ID of the opportunity/endorsement/etc.
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed', 'retry'
    attempt_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_attempt_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    request_data JSON,                      -- JSON data sent to IMS
    response_data JSON,                     -- Response from IMS
    error_message TEXT,                     -- Error details if failed
    ims_policy_number VARCHAR(255),         -- Policy number returned by IMS
    external_transaction_id VARCHAR(255),   -- RSG Integration transaction ID
    
    -- Indexes for performance
    INDEX idx_status (status),
    INDEX idx_resource (resource_type, resource_id),
    INDEX idx_created_at (created_at),
    INDEX idx_transaction_type (transaction_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add some sample test data (optional)
-- INSERT INTO ims_transaction_logs (transaction_type, resource_type, resource_id, status)
-- VALUES 
-- ('binding', 'opportunity', 315, 'pending'),
-- ('binding', 'opportunity', 102, 'pending');