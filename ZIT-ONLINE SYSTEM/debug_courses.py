"""Debug script to test the index route and see what courses are being queried."""
from app import app, Course

with app.app_context():
    # Test the query that the index() route uses
    courses = Course.query.order_by(Course.created_at.desc()).limit(6).all()
    print(f"Courses fetched: {len(courses)}")
    for course in courses:
        print(f"  - {course.id}: {course.title} (${course.price})")
    
    # Also check all courses
    all_courses = Course.query.all()
    print(f"\nTotal courses in DB: {len(all_courses)}")
