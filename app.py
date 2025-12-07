from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify, make_response, send_file, Response, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import io
import csv
import re
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

# Paystack helper (server-side initialization + verification)
from paystack import initialize_transaction, verify_transaction, get_public_key

# =====================================================
#  LANGUAGE SUPPORT
# =====================================================
SUPPORTED_LANGUAGES = {
    'en': {'name': 'English', 'flag': '🇬🇧'},
    'ha': {'name': 'Hausa', 'flag': '🇳🇪'},
    'yo': {'name': 'Yoruba', 'flag': '🇳🇬'},
    'ig': {'name': 'Igbo', 'flag': '🇳🇬'},
}

# Translation dictionary
TRANSLATIONS = {
    'en': {
        'Welcome Back!': 'Welcome Back!',
        'Login to access your learning dashboard': 'Login to access your learning dashboard',
        'Email Address': 'Email Address',
        'Password': 'Password',
        'Remember me': 'Remember me',
        'Forgot password?': 'Forgot password?',
        'Login': 'Login',
        'Don\'t have an account?': 'Don\'t have an account?',
        'Register here': 'Register here',
        'Create Your Account': 'Create Your Account',
        'Join ZIT Learn Online and start your journey': 'Join ZIT Learn Online and start your journey',
        'Full Name': 'Full Name',
        'Account Type': 'Account Type',
        'Student': 'Student',
        'Instructor': 'Instructor',
        'Create Account': 'Create Account',
        'Home': 'Home',
        'About': 'About',
        'Courses': 'Courses',
        'Dashboard': 'Dashboard',
        'Logout': 'Logout',
        'Settings': 'Settings',
        'Language': 'Language',
    },
    'ha': {
        'Welcome Back!': 'Sannu Sauran!',
        'Login to access your learning dashboard': 'Shiga domin samun damar gida na koyo',
        'Email Address': 'Adreshin Email',
        'Password': 'Kalmar Sirri',
        'Remember me': 'Tuna ni',
        'Forgot password?': 'Mun sahilta kalmer sirri?',
        'Login': 'Shiga',
        'Don\'t have an account?': 'Ba ka da asusu?',
        'Register here': 'Jimreta a nan',
        'Create Your Account': 'Aika Asusu Naka',
        'Join ZIT Learn Online and start your journey': 'Yi haɗi da ZIT Learn Online kuma fara janyewarka',
        'Full Name': 'Cikakken Suna',
        'Account Type': 'Nau\'in Asusu',
        'Student': 'Dalibi',
        'Instructor': 'Maista',
        'Create Account': 'Aika Asusu',
        'Home': 'Gida',
        'About': 'Game da',
        'Courses': 'Ayyuka',
        'Dashboard': 'Dashboard',
        'Logout': 'Fita',
        'Settings': 'Saitunan',
        'Language': 'Harshe',
    },
    'yo': {
        'Welcome Back!': 'Kaabọ Pade!',
        'Login to access your learning dashboard': 'Wọle lati lo oju-iwe akọkọ rẹ',
        'Email Address': 'Adirẹsi Email',
        'Password': 'Ọrọ Ofin',
        'Remember me': 'Ranti mi',
        'Forgot password?': 'Ṣe o gbagbe ọrọ ofin?',
        'Login': 'Wọle',
        'Don\'t have an account?': 'Ṣe o ni akaụntụ?',
        'Register here': 'Forukọsilẹ nibi',
        'Create Your Account': 'Ṣẹda Akaụntụ Rẹ',
        'Join ZIT Learn Online and start your journey': 'Darapọ pelu ZIT Learn Online ki o bẹrẹ irin ajo rẹ',
        'Full Name': 'Orukọ Ni Kikun',
        'Account Type': 'Iru Akaụntụ',
        'Student': 'Olukọ',
        'Instructor': 'Olukọ',
        'Create Account': 'Ṣẹda Akaụntụ',
        'Home': 'Ile',
        'About': 'Nipa',
        'Courses': 'Awọn ẹkọ',
        'Dashboard': 'Dashboard',
        'Logout': 'Jade',
        'Settings': 'Awọn iṣeto',
        'Language': 'Ede',
    },
    'ig': {
        'Welcome Back!': 'Ozeligo!',
        'Login to access your learning dashboard': 'Banye iji nweta aka na ụlọ ihe ọmụmụ gị',
        'Email Address': 'Adreesị Email',
        'Password': 'Okwu Nzuzo',
        'Remember me': 'Cheta mụ',
        'Forgot password?': 'Chefutara okwu nzuzo?',
        'Login': 'Banye',
        'Don\'t have an account?': 'Ụdị akụ̀nnta a dịghị gị?',
        'Register here': 'Debanye aha ebe a',
        'Create Your Account': 'Mepụta Akụ̀nnta Gị',
        'Join ZIT Learn Online and start your journey': 'Sọọ na ZIT Learn Online ma malite njem gị',
        'Full Name': 'Aha Zuru Ezu',
        'Account Type': 'Ụdị Akụ̀nnta',
        'Student': 'Nwa Akwụkwọ',
        'Instructor': 'Onye Ọkụ̀',
        'Create Account': 'Mepụta Akụ̀nnta',
        'Home': 'Ụlọ',
        'About': 'Maka',
        'Courses': 'Ihe Ọmụmụ',
        'Dashboard': 'Dashboard',
        'Logout': 'Pụta',
        'Settings': 'Nhazi',
        'Language': 'Asụsụ',
    }
}

def translate(text, lang='en'):
    """Translate text to specified language."""
    if lang not in TRANSLATIONS:
        lang = 'en'
    return TRANSLATIONS[lang].get(text, text)

# =====================================================
#  APP CONFIGURATION
# =====================================================
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///zit_online.db'
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
csrf = CSRFProtect(app)
limiter = Limiter(app=app, key_func=get_remote_address)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# =====================================================
#  CONTEXT PROCESSOR FOR CSRF TOKEN & LANGUAGE
# =====================================================
from flask_wtf.csrf import generate_csrf

@app.context_processor
def inject_csrf_token():
    """Make csrf_token(), language helpers available in all templates."""
    lang = session.get('language', 'en')
    return {
        'csrf_token': generate_csrf,
        'current_language': lang,
        'supported_languages': SUPPORTED_LANGUAGES,
        'translate': translate,
    }

@app.before_request
def set_default_language():
    """Set default language from session or browser preference."""
    if 'language' not in session:
        # Try to detect from browser Accept-Language header
        lang = request.accept_languages.best_match(['en', 'ha', 'yo', 'ig'])
        session['language'] = lang or 'en'

# =====================================================
#  MODELS
# =====================================================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), default='student')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    image = db.Column(db.String(300))
    price = db.Column(db.Float, default=0.0)
    is_approved = db.Column(db.Boolean, default=False)
    is_rejected = db.Column(db.Boolean, default=False)
    rejection_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    instructor = db.relationship('User', backref='courses')


class Module(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    course = db.relationship('Course', backref='modules')


class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class CourseProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('module.id'), nullable=True)  # allow None
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('module.id'))
    grade = db.Column(db.Float)
    feedback = db.Column(db.Text)
    graded_at = db.Column(db.DateTime, default=datetime.utcnow)


class ModuleProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('module.id'), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('student_id', 'module_id', name='uix_student_module'),)


######### Quiz Models #########
class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)


class Choice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    text = db.Column(db.String(500), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)


class StudentAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    choice_id = db.Column(db.Integer, db.ForeignKey('choice.id'))
    correct = db.Column(db.Boolean)
    answered_at = db.Column(db.DateTime, default=datetime.utcnow)


# =====================================================
#  Video Model
# =====================================================
class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(200))
    filename = db.Column(db.String(300), nullable=False)
    original_filename = db.Column(db.String(300))
    mimetype = db.Column(db.String(100), default='video/mp4')
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    course = db.relationship('Course', backref='videos')


# =====================================================
#  LOGIN MANAGER
# =====================================================
@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception:
        return None


# =====================================================
#  INITIAL DATABASE CREATION (Flask-safe)
# =====================================================
def init_db():
    """Initialize or recreate the database."""
    with app.app_context():
        db.drop_all()
        db.create_all()

        admin = User.query.filter_by(email='admin@zit.edu').first()
        if not admin:
            admin = User(
                full_name='Administrator',
                email='admin@zit.edu',
                role='admin'
            )
            admin.set_password('admin123')  # change in production
            db.session.add(admin)
            db.session.commit()


@app.before_request
def ensure_database():
    # Run once to create tables and try to add missing columns safely
    if not hasattr(app, '_db_created'):
        with app.app_context():
            db.create_all()
            try:
                ensure_course_columns()
            except Exception:
                import traceback
                traceback.print_exc()
            app._db_created = True


def ensure_course_columns():
    """Add missing columns to the course table if they don't exist (SQLite-safe)."""
    with app.app_context():
        conn = db.engine.connect()
        try:
            res = conn.execute(text("PRAGMA table_info('course');"))
            cols = [row[1] for row in res.fetchall()]
            if 'image' not in cols:
                conn.execute(text("ALTER TABLE course ADD COLUMN image VARCHAR(300);"))
            if 'price' not in cols:
                conn.execute(text("ALTER TABLE course ADD COLUMN price REAL DEFAULT 0.0;"))
            if 'is_approved' not in cols:
                conn.execute(text("ALTER TABLE course ADD COLUMN is_approved BOOLEAN DEFAULT 0;"))
            if 'is_rejected' not in cols:
                conn.execute(text("ALTER TABLE course ADD COLUMN is_rejected BOOLEAN DEFAULT 0;"))
            if 'rejection_reason' not in cols:
                conn.execute(text("ALTER TABLE course ADD COLUMN rejection_reason TEXT;"))
        finally:
            conn.close()


# =====================================================
#  VALIDATION HELPERS
# =====================================================
def is_valid_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_strong_password(password):
    """Check if password meets minimum strength requirements."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    return True, "Password is strong"

def sanitize_input(text, max_length=None):
    """Basic input sanitization - remove/escape HTML entities."""
    if not text:
        return ''
    text = text.strip()
    # Remove script tags and common XSS vectors
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)
    if max_length:
        text = text[:max_length]
    return text


# =====================================================
#  ROUTES
# =====================================================
@app.route('/')
def index():
    courses = Course.query.order_by(Course.created_at.desc()).limit(6).all()
    return render_template('index.html', courses=courses)


@app.route('/courses')
def courses():
    courses_list = Course.query.order_by(Course.created_at.desc()).all()
    return render_template('courses.html', courses=courses_list)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per minute")
def register():
    if request.method == 'POST':
        full_name = sanitize_input(request.form.get('full_name', ''), max_length=150)
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', 'student')
        if role not in ('student', 'instructor'):
            role = 'student'

        if not full_name or not email or not password or not confirm_password:
            flash('All fields are required', 'error')
            return redirect(url_for('register'))

        if not is_valid_email(email):
            flash('Please enter a valid email address', 'error')
            return redirect(url_for('register'))

        is_strong, msg = is_strong_password(password)
        if not is_strong:
            flash(msg, 'error')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return redirect(url_for('register'))

        new_user = User(full_name=full_name, email=email, role=role)
        new_user.set_password(password)

        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('An account with that email already exists. Please log in or use a different email.', 'error')
            return redirect(url_for('register'))

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have logged out successfully.', 'info')
    return redirect(url_for('index'))


@app.route('/set_language/<lang>')
def set_language(lang):
    """Set the user's language preference."""
    if lang in ['en', 'es', 'fr', 'ar', 'yo']:
        session['language'] = lang
    return redirect(request.referrer or url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        total_users = User.query.count()
        total_students = User.query.filter_by(role='student').count()
        total_instructors = User.query.filter_by(role='instructor').count()
        total_admins = User.query.filter_by(role='admin').count()

        total_courses = Course.query.count()
        total_enrollments = CourseProgress.query.count()

        recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
        recent_courses = Course.query.order_by(Course.created_at.desc()).limit(10).all()

        recent_enrollments = db.session.query(CourseProgress, User, Course)
        recent_enrollments = recent_enrollments.join(User, CourseProgress.student_id == User.id)
        recent_enrollments = recent_enrollments.join(Course, CourseProgress.course_id == Course.id)
        recent_enrollments = recent_enrollments.order_by(CourseProgress.created_at.desc()).limit(15).all()

        # Enhanced analytics
        # Total revenue from paid courses
        total_revenue = db.session.query(db.func.sum(Course.price)).scalar() or 0.0
        
        # Enrollment trend (last 7 days)
        from datetime import timedelta
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        enrollments_by_day = db.session.query(
            db.func.date(CourseProgress.created_at).label('date'),
            db.func.count(CourseProgress.id).label('count')
        ).filter(CourseProgress.created_at >= seven_days_ago).group_by(db.func.date(CourseProgress.created_at)).all()
        enrollment_dates = [str(row[0]) for row in enrollments_by_day] if enrollments_by_day else []
        enrollment_counts = [int(row[1]) for row in enrollments_by_day] if enrollments_by_day else []

        # Course enrollment distribution (top courses)
        top_courses_data = db.session.query(
            Course.title,
            db.func.count(CourseProgress.id).label('enrollment_count')
        ).join(CourseProgress, Course.id == CourseProgress.course_id).group_by(Course.id).order_by(db.desc('enrollment_count')).limit(5).all()
        top_course_titles = [row[0] for row in top_courses_data] if top_courses_data else []
        top_course_enrollments = [row[1] for row in top_courses_data] if top_courses_data else []

        # User role distribution
        role_dist = [
            {'name': 'Students', 'value': total_students},
            {'name': 'Instructors', 'value': total_instructors},
            {'name': 'Admins', 'value': total_admins}
        ]

        return render_template('admin_dashboard.html',
                               total_users=total_users,
                               total_students=total_students,
                               total_instructors=total_instructors,
                               total_admins=total_admins,
                               total_courses=total_courses,
                               total_enrollments=total_enrollments,
                               total_revenue=total_revenue,
                               recent_users=recent_users,
                               recent_courses=recent_courses,
                               recent_enrollments=recent_enrollments,
                               enrollment_dates=enrollment_dates,
                               enrollment_counts=enrollment_counts,
                               top_course_titles=top_course_titles,
                               top_course_enrollments=top_course_enrollments,
                               role_dist=role_dist)
    elif current_user.role == 'instructor':
        courses = Course.query.filter_by(instructor_id=current_user.id).order_by(Course.created_at.desc()).all()

        total_students = db.session.query(db.func.count(db.distinct(CourseProgress.student_id)))\
            .join(Course, CourseProgress.course_id == Course.id)\
            .filter(Course.instructor_id == current_user.id).scalar() or 0

        for course in courses:
            course.enrolled_students = db.session.query(db.func.count(db.distinct(CourseProgress.student_id)))\
                .filter(CourseProgress.course_id == course.id).scalar() or 0

        return render_template('instructor_dashboard.html',
                               courses=courses,
                               total_students=total_students,
                               recent_enrollments=total_students)
    else:
        # Build a simple enrolled courses list with progress percentage for the student
        progresses = CourseProgress.query.filter_by(student_id=current_user.id).all()
        enrolled_courses = []
        course_ids = []
        for p in progresses:
            course = Course.query.get(p.course_id)
            if not course:
                continue
            modules = Module.query.filter_by(course_id=course.id).order_by(Module.id).all()
            total = len(modules)
            progress_pct = 0
            if total > 0:
                module_ids = [m.id for m in modules]
                completed = ModuleProgress.query.filter(ModuleProgress.student_id == current_user.id, ModuleProgress.module_id.in_(module_ids)).count()
                try:
                    progress_pct = int(round((completed / total) * 100))
                except Exception:
                    progress_pct = 0
            else:
                progress_pct = 0

            enrolled_courses.append({
                'id': course.id,
                'title': course.title,
                'description': course.description,
                'progress': progress_pct
            })
            course_ids.append(course.id)

        announcements = []
        if course_ids:
            announcements = Announcement.query.filter(Announcement.course_id.in_(course_ids))\
                .order_by(Announcement.created_at.desc()).limit(5).all()

        return render_template('student_dashboard.html', enrolled_courses=enrolled_courses, announcements=announcements)


@app.route('/teacher-dashboard')
@login_required
def teacher_dashboard():
    """Lightweight teacher dashboard for instructors."""
    if current_user.role != 'instructor':
        flash('Only instructors can access the teacher dashboard.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get instructor's courses
    courses = Course.query.filter_by(instructor_id=current_user.id).order_by(Course.created_at.desc()).all()
    
    # Calculate total students across all courses
    total_students = db.session.query(db.func.count(db.distinct(CourseProgress.student_id)))\
        .join(Course, CourseProgress.course_id == Course.id)\
        .filter(Course.instructor_id == current_user.id).scalar() or 0
    
    # Get recent enrollments count (last 7 days)
    from datetime import timedelta
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_enrollments = db.session.query(db.func.count(CourseProgress.id))\
        .join(Course, CourseProgress.course_id == Course.id)\
        .filter(Course.instructor_id == current_user.id)\
        .filter(CourseProgress.created_at >= seven_days_ago).scalar() or 0
    
    return render_template('teacher_dashboard.html',
                           courses=courses,
                           total_students=total_students,
                           recent_enrollments=recent_enrollments)


@app.route('/course/<int:course_id>')
@login_required
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    modules = Module.query.filter_by(course_id=course_id).all()
    announcements = Announcement.query.filter_by(course_id=course_id).order_by(Announcement.created_at.desc()).all()
    quizzes = Quiz.query.filter_by(course_id=course_id).order_by(Quiz.created_at.desc()).all()
    videos = Video.query.filter_by(course_id=course_id).order_by(Video.created_at.desc()).all()
    # If student, also gather completed module ids for UI
    completed_module_ids = set()
    if current_user.is_authenticated and current_user.role == 'student':
        m_ids = [m.id for m in modules]
        if m_ids:
            rows = ModuleProgress.query.filter(ModuleProgress.student_id == current_user.id, ModuleProgress.module_id.in_(m_ids)).all()
            completed_module_ids = {r.module_id for r in rows}

    return render_template('course_detail.html', course=course, modules=modules, announcements=announcements, completed_module_ids=completed_module_ids, quizzes=quizzes, videos=videos)


@app.route('/course/<int:course_id>/videos/upload', methods=['GET','POST'])
@login_required
def upload_video(course_id):
    course = Course.query.get_or_404(course_id)
    if current_user.role not in ('instructor', 'admin'):
        flash('Only instructors or admins can upload videos.', 'error')
        return redirect(url_for('course_detail', course_id=course_id))
    # if instructor ensure they own the course
    if current_user.role == 'instructor' and course.instructor_id != current_user.id:
        flash('Only the course instructor can upload videos for this course.', 'error')
        return redirect(url_for('course_detail', course_id=course_id))

    if request.method == 'POST':
        file = request.files.get('video')
        title = request.form.get('title', '').strip() or (file.filename if file else '')
        if not file:
            flash('No file uploaded', 'error')
            return redirect(url_for('upload_video', course_id=course_id))
        ALLOWED_EXT = {'mp4', 'webm', 'ogg', 'm4v'}
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        if ext not in ALLOWED_EXT:
            flash('Unsupported video format', 'error')
            return redirect(url_for('upload_video', course_id=course_id))
        upload_dir = os.path.join(app.root_path, 'static', 'uploads', 'videos')
        os.makedirs(upload_dir, exist_ok=True)
        stored_name = f"{int(datetime.utcnow().timestamp())}_{filename}"
        path = os.path.join(upload_dir, stored_name)
        file.save(path)
        # Auto-detect MIME type based on file extension
        mimetype_map = {
            'mp4': 'video/mp4',
            'webm': 'video/webm',
            'ogg': 'video/ogg',
            'm4v': 'video/mp4'
        }
        detected_mimetype = mimetype_map.get(ext, 'video/mp4')
        v = Video(course_id=course_id, title=title, filename=stored_name, original_filename=filename, mimetype=detected_mimetype, uploaded_by=current_user.id)
        db.session.add(v)
        db.session.commit()
        flash('Video uploaded successfully', 'success')
        return redirect(url_for('course_detail', course_id=course_id))

    return render_template('upload_video.html', course=course)


@app.route('/video/<int:video_id>')
@login_required
def view_video(video_id):
    video = Video.query.get_or_404(video_id)
    return render_template('video_player.html', video=video)


@app.route('/video/<int:video_id>/stream')
def stream_video(video_id):
    video = Video.query.get_or_404(video_id)
    file_path = os.path.join(app.root_path, 'static', 'uploads', 'videos', video.filename)
    if not os.path.exists(file_path):
        abort(404)
    file_size = os.path.getsize(file_path)
    range_header = request.headers.get('Range', None)
    if not range_header:
        return send_file(file_path, mimetype=video.mimetype, conditional=True)
    # parse Range header: bytes=start-end
    import re
    m = re.match(r'bytes=(\d+)-(\d*)', range_header)
    if m:
        start = int(m.group(1))
        end = m.group(2)
        end = int(end) if end else file_size - 1
    else:
        start = 0
        end = file_size - 1
    if start >= file_size:
        abort(416)
    length = end - start + 1
    with open(file_path, 'rb') as f:
        f.seek(start)
        data = f.read(length)
    rv = Response(data, 206, mimetype=video.mimetype, direct_passthrough=True)
    rv.headers.add('Content-Range', f'bytes {start}-{end}/{file_size}')
    rv.headers.add('Accept-Ranges', 'bytes')
    rv.headers.add('Content-Length', str(length))
    return rv


@app.route('/enroll/<int:course_id>')
@login_required
def enroll(course_id):
    if current_user.role != 'student':
        flash('Only students can enroll in courses.', 'error')
        return redirect(url_for('course_detail', course_id=course_id))

    course = Course.query.get_or_404(course_id)

    existing_progress = CourseProgress.query.filter_by(
        student_id=current_user.id,
        course_id=course_id
    ).first()

    if existing_progress:
        flash('You are already enrolled in this course.', 'info')
        return redirect(url_for('course_detail', course_id=course_id))

    first_module = Module.query.filter_by(course_id=course_id).first()
    if not first_module:
        flash('This course has no modules yet. Please try again later.', 'error')
        return redirect(url_for('course_detail', course_id=course_id))

    progress = CourseProgress(
        student_id=current_user.id,
        course_id=course_id,
        module_id=first_module.id
    )

    db.session.add(progress)
    db.session.commit()

    flash('You have successfully enrolled in this course!', 'success')
    return redirect(url_for('course_detail', course_id=course_id))


@app.route('/start_payment/<int:course_id>')
@login_required
def start_payment(course_id):
    if current_user.role != 'student':
        flash('Only students can purchase courses.', 'error')
        return redirect(url_for('course_detail', course_id=course_id))

    course = Course.query.get_or_404(course_id)
    try:
        price = float(course.price or 0.0)
    except Exception:
        price = 0.0

    if price <= 0.0:
        return redirect(url_for('enroll', course_id=course_id))

    # For development without Paystack: auto-enroll and show success
    # Check if already enrolled
    existing_progress = CourseProgress.query.filter_by(
        student_id=current_user.id,
        course_id=course_id
    ).first()

    if existing_progress:
        flash('You are already enrolled in this course.', 'info')
        return redirect(url_for('course_detail', course_id=course_id))

    # Get first module
    first_module = Module.query.filter_by(course_id=course_id).first()
    if not first_module:
        flash('This course has no modules yet. Please try again later.', 'error')
        return redirect(url_for('course_detail', course_id=course_id))

    # Create enrollment with first module
    progress = CourseProgress(
        student_id=current_user.id,
        course_id=course_id,
        module_id=first_module.id
    )
    db.session.add(progress)
    db.session.commit()

    flash('Course purchased successfully! You now have access to this course.', 'success')
    return redirect(url_for('course_detail', course_id=course_id))


@app.route('/module/<int:module_id>/complete', methods=['POST'])
@login_required
def complete_module(module_id):
    if current_user.role != 'student':
        flash('Only students can mark modules complete.', 'error')
        return redirect(request.referrer or url_for('dashboard'))

    module = Module.query.get_or_404(module_id)

    # Ensure student is enrolled in the course
    enrollment = CourseProgress.query.filter_by(student_id=current_user.id, course_id=module.course_id).first()
    if not enrollment:
        flash('You must enroll in the course before marking modules complete.', 'error')
        return redirect(url_for('course_detail', course_id=module.course_id))

    existing = ModuleProgress.query.filter_by(student_id=current_user.id, module_id=module_id).first()
    if existing:
        flash('This module is already marked complete.', 'info')
        return redirect(request.referrer or url_for('course_detail', course_id=module.course_id))

    mp = ModuleProgress(student_id=current_user.id, module_id=module_id)
    db.session.add(mp)
    db.session.commit()

    flash('Module marked complete.', 'success')
    return redirect(request.referrer or url_for('course_detail', course_id=module.course_id))


@app.route('/paystack_callback')
def paystack_callback():
    reference = request.args.get('reference') or request.args.get('trxref')
    if not reference:
        flash('Missing payment reference.', 'error')
        return redirect(url_for('courses'))

    try:
        verify_resp = verify_transaction(reference)
    except Exception:
        app.logger.exception('Paystack verify failed')
        flash('Unable to validate payment. Contact support.', 'error')
        return redirect(url_for('courses'))

    if not verify_resp.get('status'):
        flash(verify_resp.get('message', 'Payment verification failed'), 'error')
        return redirect(url_for('courses'))

    data = verify_resp.get('data') or {}
    if data.get('status') != 'success':
        flash('Payment was not successful.', 'error')
        return redirect(url_for('courses'))

    metadata = data.get('metadata') or {}
    try:
        course_id = int(metadata.get('course_id') or request.args.get('course_id'))
    except Exception:
        course_id = None

    student_id = metadata.get('student_id')

    if not course_id:
        flash('Payment verified but could not determine course. Contact support.', 'error')
        return redirect(url_for('courses'))

    try:
        student_id = int(student_id) if student_id else None
    except Exception:
        student_id = None

    enrolled_user = None
    if student_id:
        enrolled_user = User.query.get(student_id)
    else:
        email = data.get('customer', {}).get('email')
        if email:
            enrolled_user = User.query.filter_by(email=email).first()

    if not enrolled_user:
        flash('Payment verified but student account not found. Please register with the same email.', 'error')
        return redirect(url_for('courses'))

    existing = CourseProgress.query.filter_by(student_id=enrolled_user.id, course_id=course_id).first()
    if existing:
        flash('Payment successful. You are now enrolled in the course.', 'success')
        return redirect(url_for('course_detail', course_id=course_id))

    first_module = Module.query.filter_by(course_id=course_id).first()
    if not first_module:
        progress = CourseProgress(student_id=enrolled_user.id, course_id=course_id, module_id=None)
    else:
        progress = CourseProgress(student_id=enrolled_user.id, course_id=course_id, module_id=first_module.id)

    db.session.add(progress)
    db.session.commit()

    flash('Payment successful. You are now enrolled in the course.', 'success')
    return redirect(url_for('course_detail', course_id=course_id))


# =====================================================
#  COURSE MANAGEMENT ROUTES
# =====================================================
@app.route('/create_course', methods=['GET', 'POST'])
@login_required
def create_course():
    if current_user.role != 'instructor':
        flash('You do not have permission to create courses.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        image = request.form.get('image')
        try:
            price = float(request.form.get('price') or 0.0)
        except ValueError:
            price = 0.0

        if not title or not description:
            flash('All fields are required', 'error')
            return redirect(url_for('create_course'))

        course = Course(
            title=title,
            description=description,
            instructor_id=current_user.id,
            image=image,
            price=price
        )

        db.session.add(course)
        db.session.commit()

        flash('Course created successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('create_course.html')


@app.route('/edit_course/<int:course_id>', methods=['GET', 'POST'])
@login_required
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)

    if current_user.id != course.instructor_id:
        flash('You do not have permission to edit this course.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        course.title = request.form.get('title')
        course.description = request.form.get('description')
        course.image = request.form.get('image')
        try:
            course.price = float(request.form.get('price') or 0.0)
        except ValueError:
            course.price = 0.0

        db.session.commit()
        flash('Course updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('create_course.html', course=course)


@app.route('/course/<int:course_id>/modules/create', methods=['GET', 'POST'])
@login_required
def create_module(course_id):
    course = Course.query.get_or_404(course_id)
    if current_user.role != 'instructor' or current_user.id != course.instructor_id:
        flash('You do not have permission to add modules to this course.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        if not title or not content:
            flash('All fields are required', 'error')
            return redirect(url_for('create_module', course_id=course_id))

        module = Module(course_id=course_id, title=title, content=content)
        db.session.add(module)
        db.session.commit()
        flash('Module added successfully!', 'success')
        return redirect(url_for('course_detail', course_id=course_id))

    return render_template('create_module.html', course=course)


@app.route('/course/<int:course_id>/quiz/create', methods=['GET', 'POST'])
@login_required
def create_quiz(course_id):
    course = Course.query.get_or_404(course_id)
    if current_user.role != 'instructor' or current_user.id != course.instructor_id:
        flash('You do not have permission to create quizzes for this course.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        title = request.form.get('title')
        questions_json = request.form.get('questions_json')
        if not title or not questions_json:
            flash('Title and questions are required', 'error')
            return redirect(url_for('create_quiz', course_id=course_id))

        try:
            import json
            questions = json.loads(questions_json)
        except Exception:
            flash('Invalid JSON for questions', 'error')
            return redirect(url_for('create_quiz', course_id=course_id))

        quiz = Quiz(course_id=course_id, title=title)
        db.session.add(quiz)
        db.session.flush()

        for idx, q in enumerate(questions, start=1):
            question = Question(quiz_id=quiz.id, text=q.get('text', ''), explanation=q.get('explanation'), order=idx)
            db.session.add(question)
            db.session.flush()
            for choice in q.get('choices', []):
                c = Choice(question_id=question.id, text=choice.get('text', ''), is_correct=bool(choice.get('is_correct', False)))
                db.session.add(c)

        db.session.commit()
        flash('Quiz created successfully', 'success')
        return redirect(url_for('course_detail', course_id=course_id))

    return render_template('create_quiz.html', course=course)


@app.route('/quiz/<int:quiz_id>')
@login_required
def view_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz.id).order_by(Question.order).all()
    qdata = []
    for q in questions:
        choices = Choice.query.filter_by(question_id=q.id).all()
        qdata.append({'id': q.id, 'text': q.text, 'choices': choices})
    return render_template('quiz.html', quiz=quiz, questions=qdata)


@app.route('/quiz/<int:quiz_id>/answer/<int:question_id>', methods=['POST'])
@login_required  # ADD THIS DECORATOR
def submit_answer(quiz_id, question_id):
    if current_user.role != 'student':
        return jsonify({'error': 'Only students can answer quizzes.'}), 403  # FIXED: Added back the role check

    data = request.get_json() or {}
    choice_id = data.get('choice_id')
    if not choice_id:
        return jsonify({'error': 'choice_id required'}), 400

    question = Question.query.filter_by(id=question_id, quiz_id=quiz_id).first_or_404()
    choice = Choice.query.filter_by(id=choice_id, question_id=question_id).first()
    if not choice:
        return jsonify({'error': 'Invalid choice'}), 400

    correct = bool(choice.is_correct)

    # store student answer (idempotent: if exists, update)
    existing = StudentAnswer.query.filter_by(student_id=current_user.id, question_id=question_id).first()
    if existing:
        existing.choice_id = choice.id
        existing.correct = correct
        existing.answered_at = datetime.utcnow()
    else:
        sa = StudentAnswer(student_id=current_user.id, question_id=question_id, choice_id=choice.id, correct=correct)
        db.session.add(sa)

    db.session.commit()

    return jsonify({'correct': correct, 'explanation': question.explanation or ''})


@app.route('/quiz/<int:quiz_id>/results')
@login_required
def quiz_results(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    course = Course.query.get(quiz.course_id)
    # Only instructor of the course or admin can view results
    if not current_user.is_authenticated or (current_user.role != 'admin' and current_user.id != course.instructor_id):
        flash('You do not have permission to view quiz results.', 'error')
        return redirect(url_for('dashboard'))

    questions = Question.query.filter_by(quiz_id=quiz.id).order_by(Question.order).all()
    q_ids = [q.id for q in questions]
    total_q = len(q_ids)

    # Aggregate student answers
    results = []
    average_score = 0
    leaderboard = []
    if total_q > 0:
        # map correct answers text per question
        correct_answers = {}
        for q in questions:
            correct_choice = Choice.query.filter_by(question_id=q.id, is_correct=True).first()
            correct_answers[q.id] = correct_choice.text if correct_choice else None
        # Get distinct students who answered
        rows = db.session.query(User, 
                       db.func.count(StudentAnswer.id).label('answers'), 
                       db.func.sum(db.case((StudentAnswer.correct == True, 1), else_=0)).label('correct'))
        rows = rows.join(StudentAnswer, StudentAnswer.student_id == User.id)
        rows = rows.filter(StudentAnswer.question_id.in_(q_ids))
        rows = rows.group_by(User.id).all()

        total_percent_sum = 0
        for user, answers_count, correct_count in rows:
            correct_count = correct_count or 0
            percent = int(round((correct_count) / total_q * 100))
            total_percent_sum += percent
            # fetch per-question answers for this user and include choice text
            per_q = StudentAnswer.query.filter(StudentAnswer.student_id == user.id, StudentAnswer.question_id.in_(q_ids)).all()
            per_map = {}
            for a in per_q:
                choice = Choice.query.get(a.choice_id) if a.choice_id else None
                per_map[a.question_id] = {
                    'choice_id': a.choice_id,
                    'choice_text': choice.text if choice else None,
                    'correct': a.correct,
                    'correct_choice_text': correct_answers.get(a.question_id)
                }

            results.append({'student': user, 'answers': answers_count, 'correct': correct_count, 'percent': percent, 'per_question': per_map})

        # compute average and leaderboard
        if rows:
            average_score = int(round(total_percent_sum / len(rows)))
            # sort results for leaderboard
            leaderboard = sorted(results, key=lambda r: r['percent'], reverse=True)[:5]

    return render_template('quiz_results.html', quiz=quiz, questions=questions, results=results, total_q=total_q)


@app.route('/quiz/<int:quiz_id>/export.csv')
@login_required
def export_quiz_csv(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    course = Course.query.get(quiz.course_id)
    if not current_user.is_authenticated or (current_user.role != 'admin' and current_user.id != course.instructor_id):
        flash('You do not have permission to export quiz results.', 'error')
        return redirect(url_for('dashboard'))

    questions = Question.query.filter_by(quiz_id=quiz.id).order_by(Question.order).all()
    q_ids = [q.id for q in questions]

    # Header
    import csv
    from io import StringIO

    si = StringIO()
    writer = csv.writer(si)

    # Export timestamp metadata row
    export_time = datetime.utcnow().strftime('%Y-%m-%dT%H-%M-%SZ')

    header = ['Student Name', 'Student Email', 'Answered Count', 'Correct Count', 'Percent']
    # add per-question columns using full question text as headers
    for i, q in enumerate(questions, start=1):
        qlabel = q.text or f'Q{i}'
        header.append(f'Q{i} Answer - {qlabel}')
        header.append(f'Q{i} Answered At - {qlabel}')
        header.append(f'Q{i} Correct - {qlabel}')
    writer.writerow(header)

    # build rows
    rows = db.session.query(User).join(StudentAnswer, StudentAnswer.student_id == User.id).filter(StudentAnswer.question_id.in_(q_ids)).group_by(User.id).all()
    for user in rows:
        per_q = StudentAnswer.query.filter(StudentAnswer.student_id == user.id, StudentAnswer.question_id.in_(q_ids)).all()
        per_map = {a.question_id: a for a in per_q}
        answers_count = len(per_q)
        correct_count = sum(1 for a in per_q if a.correct)
        percent = int(round((correct_count) / len(q_ids) * 100)) if q_ids else 0
        row = [user.full_name, user.email, answers_count, correct_count, percent]
        for q in questions:
            a = per_map.get(q.id)
            if a:
                choice = Choice.query.get(a.choice_id) if a.choice_id else None
                answered_at = a.answered_at.strftime('%Y-%m-%dT%H:%M:%SZ') if a.answered_at else ''
                row.append(choice.text if choice else '')
                row.append(answered_at)
                row.append('Yes' if a.correct else 'No')
            else:
                row.append('')
                row.append('')
                row.append('')
        writer.writerow(row)

    # Prepend export metadata row then CSV header
    meta_si = StringIO()
    meta_writer = csv.writer(meta_si)
    meta_writer.writerow(['Exported At', export_time])
    meta_writer.writerow([])
    meta_writer.writerow(header)
    output = meta_si.getvalue() + si.getvalue()
    response = make_response(output)
    response.headers['Content-Disposition'] = f'attachment; filename=quiz_{quiz_id}_results_{export_time}.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response


@app.route('/delete_course/<int:course_id>')
@login_required
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)

    if current_user.id != course.instructor_id:
        flash('You do not have permission to delete this course.', 'error')
        return redirect(url_for('dashboard'))

    Module.query.filter_by(course_id=course_id).delete()
    Announcement.query.filter_by(course_id=course_id).delete()
    CourseProgress.query.filter_by(course_id=course_id).delete()
    Grade.query.filter_by(course_id=course_id).delete()

    db.session.delete(course)
    db.session.commit()

    flash('Course deleted successfully!', 'success')
    return redirect(url_for('dashboard'))


# =====================================================
#  ERROR HANDLERS
# =====================================================
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(e):
    db.session.rollback()
    return render_template('500.html'), 500


# =====================================================
#  ADMIN EXPORT ROUTES
# =====================================================
@app.route('/admin/export/users.csv')
@login_required
def admin_export_users():
    if current_user.role != 'admin':
        flash('Admin access required', 'error')
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(['ID', 'Full Name', 'Email', 'Role', 'Created At'])
    for u in users:
        writer.writerow([u.id, u.full_name, u.email, u.role, u.created_at.strftime('%Y-%m-%d %H:%M:%S')])
    
    output = si.getvalue()
    response = make_response(output)
    response.headers['Content-Disposition'] = f'attachment; filename=users_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response


@app.route('/admin/export/courses.csv')
@login_required
def admin_export_courses():
    if current_user.role != 'admin':
        flash('Admin access required', 'error')
        return redirect(url_for('dashboard'))
    
    courses = Course.query.all()
    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(['ID', 'Title', 'Instructor', 'Price', 'Created At', 'Module Count', 'Enrollment Count'])
    for c in courses:
        module_count = Module.query.filter_by(course_id=c.id).count()
        enrollment_count = CourseProgress.query.filter_by(course_id=c.id).count()
        writer.writerow([c.id, c.title, c.instructor.full_name if c.instructor else 'N/A', f'{c.price or 0:.2f}', c.created_at.strftime('%Y-%m-%d %H:%M:%S'), module_count, enrollment_count])
    
    output = si.getvalue()
    response = make_response(output)
    response.headers['Content-Disposition'] = f'attachment; filename=courses_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response


@app.route('/admin/export/enrollments.csv')
@login_required
def admin_export_enrollments():
    if current_user.role != 'admin':
        flash('Admin access required', 'error')
        return redirect(url_for('dashboard'))
    
    enrollments = db.session.query(CourseProgress, User, Course).join(User, CourseProgress.student_id == User.id).join(Course, CourseProgress.course_id == Course.id).all()
    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(['Student', 'Student Email', 'Course', 'Enrolled At', 'Status'])
    for progress, user, course in enrollments:
        status = 'Completed' if progress.completed else 'In Progress'
        writer.writerow([user.full_name, user.email, course.title, progress.created_at.strftime('%Y-%m-%d %H:%M:%S'), status])
    
    output = si.getvalue()
    response = make_response(output)
    response.headers['Content-Disposition'] = f'attachment; filename=enrollments_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response


# =====================================================
#  ADMIN USER MANAGEMENT
# =====================================================
@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        flash('Admin access required', 'error')
        return redirect(url_for('dashboard'))
    
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin_users_list.html', users=users)


@app.route('/admin/users/create', methods=['GET','POST'])
@login_required
def admin_create_user():
    if current_user.role != 'admin':
        flash('Admin access required', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        role = request.form.get('role', 'student')
        
        if not full_name or not email or not password:
            flash('All fields are required', 'error')
            return redirect(url_for('admin_create_user'))
        
        if role not in ('student', 'instructor', 'admin'):
            role = 'student'
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return redirect(url_for('admin_create_user'))
        
        new_user = User(full_name=full_name, email=email, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash(f'User {full_name} created successfully', 'success')
        return redirect(url_for('admin_users'))
    
    return render_template('admin_user_form.html', action='Create', user=None)


@app.route('/admin/users/<int:user_id>/edit', methods=['GET','POST'])
@login_required
def admin_edit_user(user_id):
    if current_user.role != 'admin':
        flash('Admin access required', 'error')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.full_name = request.form.get('full_name', '').strip() or user.full_name
        new_email = request.form.get('email', '').strip().lower()
        new_password = request.form.get('password', '').strip()
        new_role = request.form.get('role', user.role)
        
        if new_role not in ('student', 'instructor', 'admin'):
            new_role = user.role
        
        if new_email != user.email and User.query.filter_by(email=new_email).first():
            flash('Email already exists', 'error')
            return redirect(url_for('admin_edit_user', user_id=user_id))
        
        user.email = new_email
        user.role = new_role
        
        if new_password:
            user.set_password(new_password)
        
        db.session.commit()
        flash('User updated successfully', 'success')
        return redirect(url_for('admin_users'))
    
    return render_template('admin_user_form.html', action='Edit', user=user)


@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if current_user.role != 'admin':
        flash('Admin access required', 'error')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot delete your own account', 'error')
        return redirect(url_for('admin_users'))
    
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.full_name} deleted successfully', 'success')
    return redirect(url_for('admin_users'))


# =====================================================
#  COURSE MODERATION
# =====================================================
@app.route('/admin/courses/moderation')
@login_required
def admin_moderation():
    if current_user.role != 'admin':
        flash('Admin access required', 'error')
        return redirect(url_for('dashboard'))
    
    pending_courses = Course.query.filter_by(is_approved=False, is_rejected=False).order_by(Course.created_at.desc()).all()
    approved_courses = Course.query.filter_by(is_approved=True).order_by(Course.created_at.desc()).limit(10).all()
    rejected_courses = Course.query.filter_by(is_rejected=True).order_by(Course.created_at.desc()).limit(10).all()
    
    return render_template('admin_moderation.html', 
                         pending_courses=pending_courses,
                         approved_courses=approved_courses,
                         rejected_courses=rejected_courses)


@app.route('/admin/courses/<int:course_id>/approve', methods=['POST'])
@login_required
def admin_approve_course(course_id):
    if current_user.role != 'admin':
        flash('Admin access required', 'error')
        return redirect(url_for('dashboard'))
    
    course = Course.query.get_or_404(course_id)
    course.is_approved = True
    course.is_rejected = False
    course.rejection_reason = None
    db.session.commit()
    flash(f'Course "{course.title}" approved successfully', 'success')
    return redirect(url_for('admin_moderation'))


@app.route('/admin/courses/<int:course_id>/reject', methods=['POST'])
@login_required
def admin_reject_course(course_id):
    if current_user.role != 'admin':
        flash('Admin access required', 'error')
        return redirect(url_for('dashboard'))
    
    course = Course.query.get_or_404(course_id)
    reason = sanitize_input(request.form.get('reason', ''), max_length=500)
    
    if not reason:
        flash('Please provide a rejection reason', 'error')
        return redirect(url_for('admin_moderation'))
    
    course.is_rejected = True
    course.is_approved = False
    course.rejection_reason = reason
    db.session.commit()
    flash(f'Course "{course.title}" rejected', 'success')
    return redirect(url_for('admin_moderation'))


# =====================================================
#  ANALYTICS & INSIGHTS
# =====================================================
@app.route('/admin/analytics')
@login_required
def admin_analytics():
    if current_user.role != 'admin':
        flash('Admin access required', 'error')
        return redirect(url_for('dashboard'))
    
    # Course completion rates
    all_courses = Course.query.filter_by(is_approved=True).all()
    course_completion_data = []
    for course in all_courses:
        modules = Module.query.filter_by(course_id=course.id).count()
        enrollments = CourseProgress.query.filter_by(course_id=course.id).count()
        completions = CourseProgress.query.filter_by(course_id=course.id, completed=True).count()
        completion_rate = int((completions / enrollments * 100) if enrollments > 0 else 0)
        course_completion_data.append({
            'title': course.title,
            'enrollments': enrollments,
            'completions': completions,
            'rate': completion_rate
        })
    
    # Student engagement (hours online approximation based on activity frequency)
    engagement_by_week = []
    for i in range(7, 0, -1):
        week_ago = datetime.utcnow().replace(day=datetime.utcnow().day - i)
        week_enrollments = CourseProgress.query.filter(CourseProgress.created_at >= week_ago).count()
        engagement_by_week.append(week_enrollments)
    
    # Top performing students (by quiz scores)
    from sqlalchemy import func
    top_students_data = db.session.query(
        User.full_name,
        func.count(StudentAnswer.id).label('answers'),
        func.sum(func.cast(StudentAnswer.correct, db.Integer)).label('correct')
    ).join(StudentAnswer, User.id == StudentAnswer.student_id).group_by(User.id).order_by(db.desc('correct')).limit(5).all()
    
    top_students = []
    for student in top_students_data:
        if student[1] > 0:
            score = int(student[2] / student[1] * 100) if student[1] > 0 else 0
            top_students.append({'name': student[0], 'score': score, 'attempts': student[1]})
    
    return render_template('admin_analytics.html',
                         course_completion_data=course_completion_data,
                         engagement_by_week=engagement_by_week,
                         top_students=top_students)


# =====================================================
#  RUN APP
# =====================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)