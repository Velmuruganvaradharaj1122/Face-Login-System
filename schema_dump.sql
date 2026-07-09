CREATE TABLE users (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	employee_id VARCHAR(50) NOT NULL, 
	full_name VARCHAR(100) NOT NULL, 
	email VARCHAR(100) NOT NULL, 
	face_encoding TEXT NOT NULL, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (employee_id), 
	UNIQUE (email)
);

CREATE TABLE login_logs (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	user_id INTEGER, 
	status VARCHAR(20) NOT NULL, 
	timestamp DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE TABLE `groups` (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(100) NOT NULL, 
	username VARCHAR(100) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	password_plain VARCHAR(255), 
	redirect_url VARCHAR(500), 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (username)
);

CREATE TABLE group_members (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	group_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	added_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(group_id) REFERENCES `groups` (id), 
	UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE TABLE licenses (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	product_key VARCHAR(100) NOT NULL, 
	machine_id VARCHAR(255) NOT NULL, 
	activated_at DATETIME, 
	expires_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (product_key)
);

