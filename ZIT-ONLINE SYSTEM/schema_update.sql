-- Add announcements table
CREATE TABLE IF NOT EXISTS announcements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    instructor_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses (id),
    FOREIGN KEY (instructor_id) REFERENCES users (id)
);

-- Add progress tracking table
CREATE TABLE IF NOT EXISTS course_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    module_id INTEGER NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES users (id),
    FOREIGN KEY (course_id) REFERENCES courses (id),
    FOREIGN KEY (module_id) REFERENCES modules (id)
);

-- Add grades table
CREATE TABLE IF NOT EXISTS grades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    module_id INTEGER,
    grade FLOAT,
    feedback TEXT,
    graded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES users (id),
    FOREIGN KEY (course_id) REFERENCES courses (id),
    FOREIGN KEY (module_id) REFERENCES modules (id)
);