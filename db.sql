-- =====================================
-- DATABASE CREATION
-- =====================================
CREATE DATABASE IF NOT EXISTS project_db;
USE project_db;

-- =====================================
-- STUDENTS TABLE
-- =====================================
CREATE TABLE students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    leader VARCHAR(100),
    member1 VARCHAR(100),
    member2 VARCHAR(100),
    member3 VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    password VARCHAR(100),
    category VARCHAR(50)
);

-- =====================================
-- FACULTY TABLE
-- =====================================
CREATE TABLE faculty (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    password VARCHAR(100)
);

INSERT INTO faculty (name, email, password) VALUES
('Sharma', 'sharma@gmail.com', '123'),
('Mehta', 'mehta@gmail.com', '123');

-- =====================================
-- PROJECTS TABLE
-- =====================================
CREATE TABLE projects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200),
    description TEXT,
    category VARCHAR(50),
    faculty_id INT,
    FOREIGN KEY (faculty_id) REFERENCES faculty(id)
        ON DELETE SET NULL
);

-- =====================================
-- ADMIN TABLE
-- =====================================
CREATE TABLE admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    password VARCHAR(100)
);

INSERT INTO admin (username, email, password)
VALUES ('Admin', 'admin@gmail.com', 'admin123');

-- =====================================
-- ALLOTMENTS TABLE (UPDATED)
-- =====================================
CREATE TABLE allotments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    project_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (student_id) REFERENCES students(id)
        ON DELETE CASCADE,

    FOREIGN KEY (project_id) REFERENCES projects(id)
        ON DELETE CASCADE,

    UNIQUE (student_id),
    UNIQUE (project_id)
);

-- =====================================
-- SUBMISSIONS TABLE
-- =====================================
CREATE TABLE submissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    project_id INT,
    file VARCHAR(255),
    summary TEXT,
    keywords VARCHAR(255),
    plagiarism VARCHAR(20),

    FOREIGN KEY (student_id) REFERENCES students(id)
        ON DELETE CASCADE,

    FOREIGN KEY (project_id) REFERENCES projects(id)
        ON DELETE CASCADE
);

-- =====================================
-- MARKS TABLE
-- =====================================
CREATE TABLE marks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    submission_id INT,
    member_name VARCHAR(100),
    marks INT,

    FOREIGN KEY (submission_id) REFERENCES submissions(id)
        ON DELETE CASCADE
);
