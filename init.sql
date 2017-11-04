PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE pingers (
	id INTEGER NOT NULL, 
	username VARCHAR(255), 
	chat_id VARCHAR(255), 
	"match" VARCHAR(255), 
	PRIMARY KEY (id)
);
CREATE TABLE w_phrases (
	"match" VARCHAR(255) NOT NULL, 
	PRIMARY KEY ("match")
);
CREATE TABLE ping_exclude (
	"match" VARCHAR(255) NOT NULL, 
	PRIMARY KEY ("match")
);
CREATE TABLE answers (
	"match" VARCHAR(255) NOT NULL, 
	string VARCHAR(255), 
	PRIMARY KEY ("match")
);
CREATE TABLE ping_phrases (
	phrase VARCHAR(255) NOT NULL, 
	PRIMARY KEY (phrase)
);
CREATE TABLE locations (
	username VARCHAR(255) NOT NULL, 
	city VARCHAR(255), 
	PRIMARY KEY (username)
);
CREATE TABLE google (
	"match" VARCHAR(255) NOT NULL, 
	PRIMARY KEY ("match")
);
CREATE TABLE google_ignore (
	"ignore" VARCHAR(255) NOT NULL, 
	PRIMARY KEY ("ignore")
);
COMMIT;
