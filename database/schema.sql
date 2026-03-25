-- Active: 1774407993602@@127.0.0.1@3306@lab_manager
DROP DATABASE IF EXISTS lab_manager;
CREATE DATABASE lab_manager;
USE lab_manager;

CREATE TABLE ADMIN (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

CREATE TABLE LAB (
    lab_id INT AUTO_INCREMENT PRIMARY KEY,
    lab_number VARCHAR(20) NOT NULL UNIQUE
);

CREATE TABLE DEVICE (
    device_id INT AUTO_INCREMENT PRIMARY KEY,
    lab_id INT NOT NULL,
    device_number INT NOT NULL DEFAULT 1,
    status ENUM('Available', 'Issued', 'Damaged') DEFAULT 'Available',
    FOREIGN KEY (lab_id) REFERENCES LAB(lab_id)
);

CREATE TABLE STUDENT (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    student_rollnumber VARCHAR(30) NOT NULL,
    student_name VARCHAR(100) NOT NULL,
    department VARCHAR(50),
    year VARCHAR(10),
    division VARCHAR(10)
);

CREATE TABLE ISSUE_RECORD (
    issue_id INT AUTO_INCREMENT PRIMARY KEY,
    device_id INT NOT NULL,
    student_id INT NOT NULL,
    issued_by INT NOT NULL,
    issue_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    return_date DATETIME NULL,
    FOREIGN KEY (device_id) REFERENCES DEVICE(device_id),
    FOREIGN KEY (student_id) REFERENCES STUDENT(student_id),
    FOREIGN KEY (issued_by) REFERENCES ADMIN(admin_id)
);
