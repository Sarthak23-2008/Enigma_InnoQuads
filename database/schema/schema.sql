-- SafeBite database schema (PostgreSQL). Generated from backend/app/models (SQLAlchemy).
-- The app creates these tables automatically on startup; this file is for reference / manual setup.

CREATE TABLE consultation_providers (
	provider_id SERIAL NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	specialty VARCHAR(120) NOT NULL, 
	rate VARCHAR(60) NOT NULL, 
	contact VARCHAR(200) NOT NULL, 
	available BOOLEAN NOT NULL, 
	is_sample BOOLEAN NOT NULL, 
	PRIMARY KEY (provider_id)
);

CREATE TABLE foods (
	food_id SERIAL NOT NULL, 
	external_id VARCHAR(32), 
	name VARCHAR(200) NOT NULL, 
	category VARCHAR(60) NOT NULL, 
	ingredients JSON NOT NULL, 
	nutrition_data JSON NOT NULL, 
	source VARCHAR(60) NOT NULL, 
	is_packaged BOOLEAN NOT NULL, 
	meta JSON NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (food_id), 
	UNIQUE (external_id)
);
CREATE INDEX ix_foods_name ON foods (name);
CREATE INDEX ix_foods_category ON foods (category);

CREATE TABLE ingredient_mapping (
	mapping_id SERIAL NOT NULL, 
	standard_name VARCHAR(120) NOT NULL, 
	category VARCHAR(60) NOT NULL, 
	aliases JSON NOT NULL, 
	allergen_group VARCHAR(60), 
	intolerance_group JSON NOT NULL, 
	dietary_tags JSON NOT NULL, 
	PRIMARY KEY (mapping_id)
);
CREATE UNIQUE INDEX ix_ingredient_mapping_standard_name ON ingredient_mapping (standard_name);

CREATE TABLE users (
	user_id SERIAL NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	token_version INTEGER NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	onboarding_complete BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (user_id)
);
CREATE UNIQUE INDEX ix_users_email ON users (email);

CREATE TABLE diet_insights (
	insight_id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	period VARCHAR(10) NOT NULL, 
	metric VARCHAR(40) NOT NULL, 
	value FLOAT, 
	severity VARCHAR(12) NOT NULL, 
	message TEXT NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (insight_id), 
	FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE CASCADE
);
CREATE INDEX ix_diet_insights_user_id ON diet_insights (user_id);

CREATE TABLE dietary_profiles (
	profile_id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	allergies JSON NOT NULL, 
	intolerances JSON NOT NULL, 
	dietary_preferences JSON NOT NULL, 
	health_conditions JSON NOT NULL, 
	goals JSON NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (profile_id), 
	FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE CASCADE
);
CREATE UNIQUE INDEX ix_dietary_profiles_user_id ON dietary_profiles (user_id);

CREATE TABLE goals (
	goal_id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	goal_type VARCHAR(40) NOT NULL, 
	target FLOAT, 
	active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (goal_id), 
	FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE CASCADE
);
CREATE INDEX ix_goals_user_id ON goals (user_id);

CREATE TABLE notification_outbox (
	outbox_id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	channel VARCHAR(20) NOT NULL, 
	subject VARCHAR(200) NOT NULL, 
	body TEXT NOT NULL, 
	provider VARCHAR(20) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (outbox_id), 
	FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE CASCADE
);
CREATE INDEX ix_notification_outbox_user_id ON notification_outbox (user_id);

CREATE TABLE notification_settings (
	notification_id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	weekly_reports BOOLEAN NOT NULL, 
	biweekly_reports BOOLEAN NOT NULL, 
	monthly_reports BOOLEAN NOT NULL, 
	push_enabled BOOLEAN NOT NULL, 
	email_enabled BOOLEAN NOT NULL, 
	last_sent JSON NOT NULL, 
	PRIMARY KEY (notification_id), 
	FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE CASCADE
);
CREATE UNIQUE INDEX ix_notification_settings_user_id ON notification_settings (user_id);

CREATE TABLE scan_results (
	scan_id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	food_id INTEGER, 
	food_name VARCHAR(200) NOT NULL, 
	input_method VARCHAR(20) NOT NULL, 
	image_path VARCHAR(255), 
	raw_ocr_text TEXT, 
	raw_ingredients JSON NOT NULL, 
	normalized_ingredients JSON NOT NULL, 
	extracted_nutrition JSON NOT NULL, 
	allergen_statements JSON NOT NULL, 
	risk_level VARCHAR(10) NOT NULL, 
	detected_conflicts JSON NOT NULL, 
	explanation TEXT NOT NULL, 
	warnings JSON NOT NULL, 
	confidence FLOAT NOT NULL, 
	ocr_confidence FLOAT, 
	data_certainty VARCHAR(12) NOT NULL, 
	alternatives JSON NOT NULL, 
	meta JSON NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (scan_id), 
	FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE CASCADE, 
	FOREIGN KEY(food_id) REFERENCES foods (food_id) ON DELETE SET NULL
);
CREATE INDEX ix_scan_results_created_at ON scan_results (created_at);
CREATE INDEX ix_scan_results_user_id ON scan_results (user_id);
CREATE INDEX ix_scan_results_risk_level ON scan_results (risk_level);

CREATE TABLE user_settings (
	setting_id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	default_input_method VARCHAR(20) NOT NULL, 
	ocr_language VARCHAR(20) NOT NULL, 
	auto_log BOOLEAN NOT NULL, 
	text_size VARCHAR(10) NOT NULL, 
	high_contrast BOOLEAN NOT NULL, 
	voice_assistance BOOLEAN NOT NULL, 
	PRIMARY KEY (setting_id), 
	FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE CASCADE
);
CREATE UNIQUE INDEX ix_user_settings_user_id ON user_settings (user_id);

CREATE TABLE food_logs (
	log_id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	food_id INTEGER, 
	scan_id INTEGER, 
	food_name VARCHAR(200) NOT NULL, 
	category VARCHAR(60), 
	meal_type VARCHAR(20) NOT NULL, 
	quantity FLOAT NOT NULL, 
	calories FLOAT, 
	protein FLOAT, 
	carbohydrates FLOAT, 
	fat FLOAT, 
	sugar FLOAT, 
	fiber FLOAT, 
	sodium FLOAT, 
	potassium FLOAT, 
	risk_level VARCHAR(10), 
	is_processed BOOLEAN NOT NULL, 
	is_fruit_veg BOOLEAN NOT NULL, 
	added_sugar_likely BOOLEAN NOT NULL, 
	is_unpackaged BOOLEAN NOT NULL, 
	input_method VARCHAR(20) NOT NULL, 
	is_demo BOOLEAN NOT NULL, 
	consumed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (log_id), 
	FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE CASCADE, 
	FOREIGN KEY(food_id) REFERENCES foods (food_id) ON DELETE SET NULL, 
	FOREIGN KEY(scan_id) REFERENCES scan_results (scan_id) ON DELETE SET NULL
);
CREATE INDEX ix_food_logs_user_id ON food_logs (user_id);
CREATE INDEX ix_food_logs_user_consumed ON food_logs (user_id, consumed_at);

CREATE TABLE symptom_logs (
	symptom_id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	food_log_id INTEGER NOT NULL, 
	severity VARCHAR(10) NOT NULL, 
	symptom VARCHAR(200) NOT NULL, 
	notes TEXT NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (symptom_id), 
	CONSTRAINT uq_symptom_per_log UNIQUE (food_log_id), 
	FOREIGN KEY(user_id) REFERENCES users (user_id) ON DELETE CASCADE, 
	FOREIGN KEY(food_log_id) REFERENCES food_logs (log_id) ON DELETE CASCADE
);
CREATE INDEX ix_symptom_logs_food_log_id ON symptom_logs (food_log_id);
CREATE INDEX ix_symptom_logs_user_id ON symptom_logs (user_id);
