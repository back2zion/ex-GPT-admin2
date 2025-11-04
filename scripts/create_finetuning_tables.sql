-- Fine-tuning MLOps 테이블 생성 스크립트
-- 작성일: 2025-10-30

-- Training datasets table
CREATE TABLE IF NOT EXISTS training_datasets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    format VARCHAR(50) DEFAULT 'jsonl',
    file_path TEXT NOT NULL,
    total_samples INTEGER,
    train_samples INTEGER,
    val_samples INTEGER,
    test_samples INTEGER,
    dataset_metadata JSONB,
    quality_score FLOAT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'active'
);

CREATE INDEX IF NOT EXISTS ix_training_datasets_id ON training_datasets(id);
CREATE INDEX IF NOT EXISTS ix_training_datasets_name ON training_datasets(name);

COMMENT ON TABLE training_datasets IS 'Fine-tuning용 학습 데이터셋';

-- Dataset quality logs table
CREATE TABLE IF NOT EXISTS dataset_quality_logs (
    id SERIAL PRIMARY KEY,
    dataset_id INTEGER REFERENCES training_datasets(id) ON DELETE CASCADE,
    check_type VARCHAR(100),
    passed BOOLEAN,
    issues JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_dataset_quality_logs_id ON dataset_quality_logs(id);

COMMENT ON TABLE dataset_quality_logs IS '데이터셋 품질 검증 로그';

-- Finetuning jobs table
CREATE TABLE IF NOT EXISTS finetuning_jobs (
    id SERIAL PRIMARY KEY,
    job_name VARCHAR(255) UNIQUE NOT NULL,
    base_model VARCHAR(255) NOT NULL,
    dataset_id INTEGER REFERENCES training_datasets(id),
    method VARCHAR(50) NOT NULL,
    hyperparameters JSONB NOT NULL,
    mlflow_run_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    output_dir TEXT,
    checkpoint_dir TEXT,
    logs_path TEXT,
    gpu_ids VARCHAR(50),
    error_message TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_finetuning_jobs_id ON finetuning_jobs(id);
CREATE INDEX IF NOT EXISTS ix_finetuning_jobs_job_name ON finetuning_jobs(job_name);
CREATE INDEX IF NOT EXISTS ix_finetuning_jobs_status ON finetuning_jobs(status);

COMMENT ON TABLE finetuning_jobs IS 'Fine-tuning 작업';

-- Training checkpoints table
CREATE TABLE IF NOT EXISTS training_checkpoints (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES finetuning_jobs(id) ON DELETE CASCADE,
    checkpoint_name VARCHAR(255),
    step INTEGER,
    epoch FLOAT,
    metrics JSONB,
    file_path TEXT,
    file_size_gb FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_training_checkpoints_id ON training_checkpoints(id);

COMMENT ON TABLE training_checkpoints IS 'Fine-tuning 체크포인트';

-- Model registry table
CREATE TABLE IF NOT EXISTS model_registry (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    base_model VARCHAR(255),
    finetuning_job_id INTEGER REFERENCES finetuning_jobs(id),
    model_path TEXT NOT NULL,
    model_format VARCHAR(50) DEFAULT 'huggingface',
    model_size_gb FLOAT,
    status VARCHAR(50) DEFAULT 'staging',
    deployment_config JSONB,
    mlflow_model_uri TEXT,
    description TEXT,
    tags TEXT[],
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_model_registry_id ON model_registry(id);
CREATE INDEX IF NOT EXISTS ix_model_registry_model_name ON model_registry(model_name);
CREATE INDEX IF NOT EXISTS ix_model_registry_status ON model_registry(status);

COMMENT ON TABLE model_registry IS 'Fine-tuned 모델 레지스트리';

-- Model evaluations table
CREATE TABLE IF NOT EXISTS model_evaluations (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES finetuning_jobs(id),
    checkpoint_id INTEGER REFERENCES training_checkpoints(id),
    eval_dataset_id INTEGER REFERENCES training_datasets(id),
    metrics JSONB NOT NULL,
    test_cases JSONB,
    evaluated_at TIMESTAMP DEFAULT NOW(),
    evaluator INTEGER REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS ix_model_evaluations_id ON model_evaluations(id);

COMMENT ON TABLE model_evaluations IS '모델 평가 결과';

-- Model benchmarks table
CREATE TABLE IF NOT EXISTS model_benchmarks (
    id SERIAL PRIMARY KEY,
    model_id INTEGER REFERENCES model_registry(id) ON DELETE CASCADE,
    benchmark_name VARCHAR(255),
    score FLOAT,
    details JSONB,
    benchmark_date TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_model_benchmarks_id ON model_benchmarks(id);

COMMENT ON TABLE model_benchmarks IS '모델 벤치마크 결과';

-- A/B experiments table
CREATE TABLE IF NOT EXISTS ab_experiments (
    id SERIAL PRIMARY KEY,
    experiment_name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    model_a_id INTEGER REFERENCES model_registry(id),
    model_b_id INTEGER REFERENCES model_registry(id),
    traffic_split JSONB DEFAULT '{"a": 0.5, "b": 0.5}'::jsonb,
    status VARCHAR(50) DEFAULT 'running',
    start_date TIMESTAMP DEFAULT NOW(),
    end_date TIMESTAMP,
    target_samples INTEGER DEFAULT 200,
    success_metric VARCHAR(100) DEFAULT 'user_rating',
    created_by INTEGER REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS ix_ab_experiments_id ON ab_experiments(id);
CREATE INDEX IF NOT EXISTS ix_ab_experiments_experiment_name ON ab_experiments(experiment_name);
CREATE INDEX IF NOT EXISTS ix_ab_experiments_status ON ab_experiments(status);

COMMENT ON TABLE ab_experiments IS 'A/B 테스트 실험';

-- A/B test logs table
CREATE TABLE IF NOT EXISTS ab_test_logs (
    id SERIAL PRIMARY KEY,
    experiment_id INTEGER REFERENCES ab_experiments(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),
    session_id VARCHAR(255),
    variant VARCHAR(10),
    model_id INTEGER REFERENCES model_registry(id),
    query TEXT,
    response TEXT,
    response_time_ms INTEGER,
    user_rating INTEGER,
    user_feedback TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_ab_test_logs_id ON ab_test_logs(id);
CREATE INDEX IF NOT EXISTS ix_ab_test_logs_session_id ON ab_test_logs(session_id);
CREATE INDEX IF NOT EXISTS ix_ab_test_logs_created_at ON ab_test_logs(created_at);

COMMENT ON TABLE ab_test_logs IS 'A/B 테스트 로그';

-- A/B test results table
CREATE TABLE IF NOT EXISTS ab_test_results (
    id SERIAL PRIMARY KEY,
    experiment_id INTEGER REFERENCES ab_experiments(id) ON DELETE CASCADE,
    variant VARCHAR(10),
    total_samples INTEGER,
    avg_rating FLOAT,
    avg_response_time_ms FLOAT,
    confidence_interval JSONB,
    statistical_significance BOOLEAN,
    winner BOOLEAN,
    calculated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_ab_test_results_id ON ab_test_results(id);

COMMENT ON TABLE ab_test_results IS 'A/B 테스트 결과 (통계)';

-- 완료 메시지
\echo '✅ Fine-tuning MLOps 테이블 생성 완료!'
