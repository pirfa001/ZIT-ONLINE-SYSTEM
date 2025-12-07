"""
Seed sample courses into the database for demo/testing purposes.
Run with: python seed_courses.py
"""
from app import app, db, User, Course, Module

def seed_courses():
    with app.app_context():
        # Get or create an instructor user for courses
        instructor = User.query.filter_by(email='instructor@zit.edu').first()
        if not instructor:
            instructor = User(
                full_name='Sample Instructor',
                email='instructor@zit.edu',
                role='instructor'
            )
            instructor.set_password('password123')
            db.session.add(instructor)
            db.session.commit()
            print('Created sample instructor: instructor@zit.edu')

        # Sample courses
        sample_courses = [
            {
                'title': 'Introduction to Web Development',
                'description': 'Learn the fundamentals of HTML, CSS, and JavaScript to build modern websites.',
                'price': 49.99,
                'image': 'https://via.placeholder.com/400x250?text=Web+Development'
            },
            {
                'title': 'Python for Data Science',
                'description': 'Master Python programming and data analysis with libraries like Pandas and NumPy.',
                'price': 59.99,
                'image': 'https://via.placeholder.com/400x250?text=Python+Data+Science'
            },
            {
                'title': 'Digital Marketing Essentials',
                'description': 'Discover strategies for effective social media, SEO, and content marketing.',
                'price': 39.99,
                'image': 'https://via.placeholder.com/400x250?text=Digital+Marketing'
            },
            {
                'title': 'Cloud Computing with AWS',
                'description': 'Deploy, manage, and scale applications using Amazon Web Services.',
                'price': 69.99,
                'image': 'https://via.placeholder.com/400x250?text=AWS+Cloud'
            },
            {
                'title': 'Mobile App Development',
                'description': 'Build iOS and Android apps using modern frameworks and best practices.',
                'price': 79.99,
                'image': 'https://via.placeholder.com/400x250?text=Mobile+Dev'
            },
            {
                'title': 'Artificial Intelligence Fundamentals',
                'description': 'Understand machine learning, neural networks, and AI applications.',
                'price': 89.99,
                'image': 'https://via.placeholder.com/400x250?text=AI+ML'
            }
        ]

        # Add courses if they don't exist
        for course_data in sample_courses:
            existing = Course.query.filter_by(title=course_data['title']).first()
            if not existing:
                course = Course(
                    title=course_data['title'],
                    description=course_data['description'],
                    price=course_data['price'],
                    image=course_data['image'],
                    instructor_id=instructor.id
                )
                db.session.add(course)
                print(f'Added course: {course_data["title"]}')

        db.session.commit()
        print('\n✓ Sample courses seeded successfully!')

if __name__ == '__main__':
    seed_courses()
