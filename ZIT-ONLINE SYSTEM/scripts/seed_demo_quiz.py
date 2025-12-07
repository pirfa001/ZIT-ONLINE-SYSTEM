"""Seed a demo course, instructor, students, quiz, and sample answers.
Run from workspace root: `python scripts\seed_demo_quiz.py`
"""
from app import app, db, User, Course, Module, Quiz, Question, Choice, StudentAnswer, CourseProgress
from datetime import datetime

with app.app_context():
    db.create_all()

    # create instructor
    instructor = User.query.filter_by(email='demo_instructor@zit.edu').first()
    if not instructor:
        instructor = User(full_name='Demo Instructor', email='demo_instructor@zit.edu', role='instructor')
        instructor.set_password('instructor123')
        db.session.add(instructor)
        db.session.commit()

    # create students
    students = []
    for i in range(1,4):
        email = f'demo_student{i}@zit.edu'
        s = User.query.filter_by(email=email).first()
        if not s:
            s = User(full_name=f'Demo Student {i}', email=email, role='student')
            s.set_password('student123')
            db.session.add(s)
    db.session.commit()
    students = User.query.filter(User.email.like('demo_student%')).all()

    # create course
    course = Course.query.filter_by(title='Demo Course').first()
    if not course:
        course = Course(title='Demo Course', description='A demo course for testing quizzes', instructor_id=instructor.id)
        db.session.add(course)
        db.session.commit()

    # create a simple module
    if not Module.query.filter_by(course_id=course.id, title='Intro').first():
        mod = Module(course_id=course.id, title='Intro', content='Welcome')
        db.session.add(mod)
        db.session.commit()

    # create quiz
    quiz = Quiz.query.filter_by(course_id=course.id, title='Demo Quiz').first()
    if not quiz:
        quiz = Quiz(course_id=course.id, title='Demo Quiz')
        db.session.add(quiz)
        db.session.commit()

        q1 = Question(quiz_id=quiz.id, text='What is 2+2?', explanation='Basic math', order=1)
        q2 = Question(quiz_id=quiz.id, text='Which is a fruit?', explanation='General knowledge', order=2)
        db.session.add_all([q1, q2])
        db.session.commit()

        c11 = Choice(question_id=q1.id, text='3', is_correct=False)
        c12 = Choice(question_id=q1.id, text='4', is_correct=True)
        c21 = Choice(question_id=q2.id, text='Carrot', is_correct=False)
        c22 = Choice(question_id=q2.id, text='Apple', is_correct=True)
        db.session.add_all([c11, c12, c21, c22])
        db.session.commit()

    # enroll students and add sample answers
    for s in students:
        # enroll
        cp = CourseProgress.query.filter_by(student_id=s.id, course_id=course.id).first()
        if not cp:
            cp = CourseProgress(student_id=s.id, course_id=course.id, module_id=None)
            db.session.add(cp)
            db.session.commit()

    # sample answers: student1 all correct, student2 one correct, student3 none
    quiz = Quiz.query.filter_by(course_id=course.id, title='Demo Quiz').first()
    questions = Question.query.filter_by(quiz_id=quiz.id).all()
    # map choices
    choices_map = {}
    for q in questions:
        choices = Choice.query.filter_by(question_id=q.id).all()
        for c in choices:
            if c.is_correct:
                choices_map[(q.id, 'correct')] = c.id
            else:
                if (q.id, 'wrong') not in choices_map:
                    choices_map[(q.id, 'wrong')] = c.id

    students = User.query.filter(User.email.like('demo_student%')).all()
    # student1: all correct
    s1 = students[0]
    for q in questions:
        sa = StudentAnswer.query.filter_by(student_id=s1.id, question_id=q.id).first()
        if not sa:
            sa = StudentAnswer(student_id=s1.id, question_id=q.id, choice_id=choices_map[(q.id,'correct')], correct=True)
            db.session.add(sa)
    # student2: first correct, second wrong
    s2 = students[1]
    for q in questions:
        sa = StudentAnswer.query.filter_by(student_id=s2.id, question_id=q.id).first()
        if not sa:
            if q.order == 1:
                cid = choices_map[(q.id,'correct')]
                correct = True
            else:
                cid = choices_map.get((q.id,'wrong'))
                correct = False
            sa = StudentAnswer(student_id=s2.id, question_id=q.id, choice_id=cid, correct=correct)
            db.session.add(sa)
    # student3: no answers (skip)
    db.session.commit()

    print('Seeded demo course, quiz, and sample student answers.')
*** End Patch