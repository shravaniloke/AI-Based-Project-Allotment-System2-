from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import csv
from io import TextIOWrapper
import os
from flask import flash

#summarry and keyword

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
import PyPDF2

nltk.download('punkt')
nltk.download('stopwords')

app = Flask(__name__)
app.secret_key = "mysecret123"
# File upload folder
UPLOAD_FOLDER = "static/uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# MySQL Connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Kitten@0203",
    database="project_db"
)

cursor = db.cursor()

# ---------------- HOME ---------------- #
@app.route('/')
def home():
    return render_template('index.html')


# ---------------- STUDENT ---------------- #

@app.route('/studentregister', methods=['GET','POST'])
def student_register():

    if request.method == 'POST':
        leader = request.form['leader']
        m1 = request.form['member1']
        m2 = request.form['member2']
        m3 = request.form['member3']
        email = request.form['email']
        password = request.form['password']
        category = request.form['category']   # ✅ NEW

        query = "INSERT INTO students (leader, member1, member2, member3, email, password, category) VALUES (%s,%s,%s,%s,%s,%s,%s)"
        cursor.execute(query, (leader, m1, m2, m3, email, password, category))
        db.commit()

        return redirect(url_for('student_login'))

    # ✅ GET categories dynamically
    cursor.execute("SELECT DISTINCT category FROM projects")
    categories = cursor.fetchall()

    return render_template('studentregister.html', categories=categories)


@app.route('/studentlogin', methods=['GET','POST'])
def student_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        query = "SELECT * FROM students WHERE email=%s AND password=%s"
        cursor.execute(query, (email, password))
        user = cursor.fetchone()

        if user:
            session['student_id'] = user[0]   # ✅ store logged-in student
            return redirect('/studentdashboard')
        else:
            return "Invalid login"

    return render_template('studentlogin.html')


# @app.route('/studentdashboard')
# def student_dashboard():
#     return render_template('student_dashboard.html')

@app.route('/studentdashboard')
def student_dashboard():

    student_id = session.get('student_id')

    if not student_id:
        return redirect('/studentlogin')

    # get selected project
    cursor.execute("""
        SELECT p.title 
        FROM allotments a
        JOIN projects p ON a.project_id = p.id
        WHERE a.student_id=%s
    """, (student_id,))
    
    project = cursor.fetchone()

    selected_project = project[0] if project else None

    return render_template(
        'student_dashboard.html',
        selected_project=selected_project
    )


# ---------------- FACULTY ---------------- #

@app.route('/facultylogin', methods=['GET','POST'])
def faculty_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        query = "SELECT * FROM faculty WHERE email=%s AND password=%s"
        cursor.execute(query, (email, password))
        faculty = cursor.fetchone()

        if faculty:
            return redirect(url_for('faculty_dashboard'))
        else:
            return "Invalid Faculty Login"

    return render_template('facultylogin.html')


@app.route('/facultydashboard')
def faculty_dashboard():
    return render_template('faculty_dashboard.html')

# 🔹 Upload Projects CSV
@app.route('/uploadprojects', methods=['POST'])
def upload_projects():
    file = request.files['file']

    if file:
        csv_file = TextIOWrapper(file, encoding='utf-8')
        reader = csv.reader(csv_file)

        next(reader)  # skip header

        for row in reader:
            title = row[0]
            description = row[1]
            category = row[2]   # ✅ NEW

            query = "INSERT INTO projects (title, description, category) VALUES (%s, %s, %s)"
            cursor.execute(query, (title, description, category))

        db.commit()

        return "Projects Uploaded Successfully!"

    return "Upload Failed"


# 🔹 View Projects
@app.route('/viewprojects')
def view_projects():
    cursor.execute("SELECT * FROM projects")
    projects = cursor.fetchall()

    return render_template('view_projects.html', projects=projects)

# 🔹 View Projects
@app.route('/viewprojectsforfaculty')
def view_projects_faculty():
    cursor.execute("SELECT * FROM projects")
    projects = cursor.fetchall()

    return render_template('view_projectsforfaculty.html', projects=projects)

@app.route('/viewprojectsforadmin')
def view_projects_admin():
    cursor.execute("SELECT * FROM projects")
    projects = cursor.fetchall()

    return render_template('view_projectsforadmin.html', projects=projects)


# @app.route('/viewavailableprojects')
# def view_available_projects():

#     student_id = session.get('student_id')

#     if not student_id:
#         return redirect('/studentlogin')

#     cursor.execute("SELECT category FROM students WHERE id=%s", (student_id,))
#     student = cursor.fetchone()

#     if student:
#         category = student[0]
#         cursor.execute("SELECT * FROM projects WHERE category=%s", (category,))
#         projects = cursor.fetchall()
#     else:
#         projects = []

#     cursor.execute("SELECT project_id FROM allotments WHERE student_id=%s", (student_id,))
#     selected = cursor.fetchall()
#     selected_projects = [s[0] for s in selected]

#     return render_template(
#         'viewavailableprojects.html',
#         projects=projects,
#         selected_projects=selected_projects
#     )

#     # 🔹 get already selected project
#     cursor.execute("SELECT project_id FROM allotments WHERE student_id=%s", (student_id,))
#     selected = cursor.fetchall()

#     selected_projects = [s[0] for s in selected]

#     return render_template(
#         'viewavailableprojects.html',
#         projects=projects,
#         selected_projects=selected_projects
#     )


@app.route('/viewavailableprojects')
def view_available_projects():

    student_id = session.get('student_id')

    if not student_id:
        return redirect('/studentlogin')

    # get category
    cursor.execute("SELECT category FROM students WHERE id=%s", (student_id,))
    student = cursor.fetchone()

    if student:
        category = student[0]
        cursor.execute("""
            SELECT * FROM projects 
            WHERE category=%s 
            AND id NOT IN (SELECT project_id FROM allotments)
        """, (category,))
        projects = cursor.fetchall()
    else:
        projects = []

    # get selected projects
    cursor.execute("SELECT project_id FROM allotments WHERE student_id=%s", (student_id,))
    selected = cursor.fetchall()
    selected_projects = [s[0] for s in selected]

    return render_template(
        'viewavailableprojects.html',
        projects=projects,
        selected_projects=selected_projects
    )


# @app.route('/submitproject', methods=['GET', 'POST'])
# def submit_project():

#     student_id = session.get('student_id')

#     if not student_id:
#         return redirect('/studentlogin')

#     # 🔹 Get student's selected project
#     cursor.execute("""
#         SELECT project_id FROM allotments 
#         WHERE student_id=%s
#     """, (student_id,))
    
#     allotment = cursor.fetchone()

#     if not allotment:
#         return "⚠️ Please select a project first!"

#     project_id = allotment[0]

#     if request.method == 'POST':

#         summary = request.form['summary']
#         keywords = request.form['keywords']
#         file = request.files['report']

#         filename = None

#         # 🔹 File Upload
#         if file and file.filename != "":
#             filename = file.filename
#             filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#             file.save(filepath)

#         # 🔹 Dummy plagiarism %
#         plagiarism = "15%"   # (you can improve later)

#         # 🔹 Insert into DB
#         query = """
#             INSERT INTO submissions 
#             (student_id, project_id, file, summary, keywords, plagiarism)
#             VALUES (%s,%s,%s,%s,%s,%s)
#         """
#         cursor.execute(query, (student_id, project_id, filename, summary, keywords, plagiarism))
#         db.commit()

#         return "✅ Project Submitted Successfully!"

#     return render_template('submit_project.html')


def extract_keywords(text):

    vectorizer = TfidfVectorizer(stop_words='english', max_features=7)
    X = vectorizer.fit_transform([text])

    return ", ".join(vectorizer.get_feature_names_out())


def read_file(filepath):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()
    
def read_pdf(filepath):
    text = ""

    with open(filepath, 'rb') as file:
        reader = PyPDF2.PdfReader(file)

        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content + " "

    return text


# @app.route('/submitproject', methods=['GET', 'POST'])
# def submit_project():

#     student_id = session.get('student_id')

#     if not student_id:
#         return redirect('/studentlogin')

#     # get selected project
#     cursor.execute("""
#         SELECT project_id FROM allotments 
#         WHERE student_id=%s
#     """, (student_id,))
    
#     allotment = cursor.fetchone()

#     if not allotment:
#         return "⚠️ Please select a project first!"

#     project_id = allotment[0]

#     if request.method == 'POST':

#         file = request.files['report']

#         if not file or file.filename == "":
#             return "⚠️ Please upload a file!"

#         from werkzeug.utils import secure_filename
#         filename = secure_filename(file.filename)

#         filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#         file.save(filepath)

#         # 🔥 Read file content
#         text = read_pdf(filepath)   # OR read_pdf(filepath)

#         # 🔥 CLEAN TEXT (ADD HERE)
#         text = text.replace('\n', ' ')
#         text = text.replace('\x00', '')
#         text = text.strip()

#         # 🔥 ML Processing
#         summary = generate_summary(text)
#         keywords = extract_keywords(text)

#         # 🔹 Dummy plagiarism
#         plagiarism = "15%"

#         # 🔹 Prevent duplicate submission
#         cursor.execute("SELECT * FROM submissions WHERE student_id=%s", (student_id,))
#         existing = cursor.fetchone()

#         if existing:
#             return "⚠️ You have already submitted your project!"

#         # 🔹 Insert into DB
#         query = """
#             INSERT INTO submissions 
#             (student_id, project_id, file, summary, keywords, plagiarism)
#             VALUES (%s,%s,%s,%s,%s,%s)
#         """
#         cursor.execute(query, (student_id, project_id, filename, summary, keywords, plagiarism))
#         db.commit()

#         return "✅ Project Submitted Successfully!"

#     return render_template('submit_project.html')



@app.route('/submitproject', methods=['GET', 'POST'])
def submit_project():

    student_id = session.get('student_id')

    if not student_id:
        return redirect('/studentlogin')

    # check existing submission
    cursor.execute("SELECT * FROM submissions WHERE student_id=%s", (student_id,))
    existing = cursor.fetchone()

    # get project_id
    cursor.execute("SELECT project_id FROM allotments WHERE student_id=%s", (student_id,))
    allotment = cursor.fetchone()

    if not allotment:
        return "⚠️ Please select a project first!"

    project_id = allotment[0]

    if request.method == 'POST':

        file = request.files['report']

        if not file or file.filename == "":
            return "⚠️ Please upload a file!"

        from werkzeug.utils import secure_filename
        import time

        filename = str(int(time.time())) + "_" + secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        text = read_pdf(filepath)
        text = text.replace('\n', ' ').replace('\x00', '').strip()

        summary = generate_summary(text)
        keywords = extract_keywords(text)
        plagiarism = "15%"

        if existing:
            # UPDATE
            cursor.execute("""
                UPDATE submissions 
                SET file=%s, summary=%s, keywords=%s, plagiarism=%s 
                WHERE student_id=%s
            """, (filename, summary, keywords, plagiarism, student_id))
        else:
            # INSERT
            cursor.execute("""
                INSERT INTO submissions 
                (student_id, project_id, file, summary, keywords, plagiarism)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (student_id, project_id, filename, summary, keywords, plagiarism))

        db.commit()

        return redirect('/submitproject')

    return render_template('submit_project.html', submission=existing)

#----------------------------------------------------------------------------------------------------------------
def generate_summary(text):

    sentences = sent_tokenize(text)

    # limit processing (avoid huge data)
    sentences = sentences[:30]   # only first 30 sentences

    words = word_tokenize(text.lower())
    stop_words = set(stopwords.words("english"))

    word_freq = {}
    for word in words:
        if word.isalnum() and word not in stop_words:
            word_freq[word] = word_freq.get(word, 0) + 1

    sentence_scores = {}
    for sent in sentences:
        for word in word_tokenize(sent.lower()):
            if word in word_freq:
                sentence_scores[sent] = sentence_scores.get(sent, 0) + word_freq[word]

    # 🔥 pick top 4 sentences only
    summary_sentences = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:4]

    return " ".join(summary_sentences)






# 🔹 View Submissions
@app.route('/viewsubmissions')
def view_submissions():

    cursor.execute("""
        SELECT 
            sub.id,
            st.leader,
            p.title,
            sub.file,
            sub.summary,
            sub.keywords,
            sub.plagiarism,
            (SELECT COUNT(*) FROM marks m WHERE m.submission_id = sub.id) as mark_count
        FROM submissions sub
        JOIN students st ON sub.student_id = st.id
        JOIN projects p ON sub.project_id = p.id
    """)

    data = cursor.fetchall()

    return render_template('view_submissions.html', data=data)
# 🔹 Assign Marks
@app.route('/assignmarks/<int:submission_id>', methods=['GET','POST'])
def assign_marks(submission_id):

    # 🔹 Get student members
    cursor.execute("""
        SELECT s.leader, s.member1, s.member2, s.member3
        FROM students s
        JOIN submissions sub ON s.id = sub.student_id
        WHERE sub.id = %s
    """, (submission_id,))
    
    members = cursor.fetchone()

    if not members:
        return "❌ No student found!"

    if request.method == 'POST':

        m1 = request.form['member1']
        m2 = request.form['member2']
        m3 = request.form['member3']
        m4 = request.form['member4']

        # 🔹 Check if marks already exist
        cursor.execute("SELECT * FROM marks WHERE submission_id=%s", (submission_id,))
        existing = cursor.fetchone()

        if existing:
            return "⚠️ Marks already assigned!"

        query = "INSERT INTO marks (submission_id, member_name, marks) VALUES (%s,%s,%s)"

        names = [members[0], members[1], members[2], members[3]]
        marks = [m1, m2, m3, m4]

        for i in range(4):
            cursor.execute(query, (submission_id, names[i], marks[i]))

        db.commit()

        return redirect('/viewsubmissions')

    return render_template('assign_marks.html', members=members)



@app.route('/selectproject', methods=['POST'])
def select_project():

    student_id = session.get('student_id')
    project_id = request.form['project_id']

    # 🔹 Check if student already selected a project
    cursor.execute("SELECT * FROM allotments WHERE student_id=%s", (student_id,))
    existing = cursor.fetchone()

    if existing:
        return "⚠️ You have already selected a project!"

    # 🔹 If not selected → insert
    query = "INSERT INTO allotments (student_id, project_id) VALUES (%s,%s)"
    cursor.execute(query, (student_id, project_id))
    db.commit()

    return "✅ Project Selected Successfully!"

# ---------------- ADMIN ---------------- #

@app.route('/adminlogin', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        query = "SELECT * FROM admin WHERE email=%s AND password=%s"
        cursor.execute(query, (email, password))
        admin = cursor.fetchone()

        if admin:
            return redirect('/admindashboard')
        else:
            return "Invalid Admin Login"

    return render_template('adminlogin.html')


@app.route('/admindashboard')
def admin_dashboard():

    # 🔹 Total students
    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    # 🔹 Total projects
    cursor.execute("SELECT COUNT(*) FROM projects")
    total_projects = cursor.fetchone()[0]

    # 🔹 Total submissions
    cursor.execute("SELECT COUNT(*) FROM submissions")
    total_submissions = cursor.fetchone()[0]

    # 🔹 Evaluated (marks assigned)
    cursor.execute("""
        SELECT COUNT(DISTINCT submission_id) FROM marks
    """)
    evaluated = cursor.fetchone()[0]

    # 🔹 Not submitted
    not_submitted = total_students - total_submissions

    return render_template('admindashboard.html',
        total_students=total_students,
        total_projects=total_projects,
        total_submissions=total_submissions,
        evaluated=evaluated,
        not_submitted=not_submitted
    )


@app.route('/viewstudents')
def view_students():
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    return render_template('view_students.html', students=students)

@app.route('/viewfaculty')
def view_faculty():
    cursor.execute("SELECT * FROM faculty")
    faculty = cursor.fetchall()
    return render_template('view_faculty.html', faculty=faculty)

@app.route('/viewallotments')
@app.route('/viewallotments')
def view_allotments():

    cursor.execute("""
        SELECT 
            a.id,
            s.leader,
            p.title
        FROM allotments a
        JOIN students s ON a.student_id = s.id
        JOIN projects p ON a.project_id = p.id
    """)

    data = cursor.fetchall()
    return render_template('view_allotments.html', data=data)


@app.route('/viewmarks')
def view_marks():

    cursor.execute("""
        SELECT 
            st.leader,
            p.title,
            m.member_name,
            m.marks
        FROM marks m
        JOIN submissions sub ON m.submission_id = sub.id
        JOIN students st ON sub.student_id = st.id
        JOIN projects p ON sub.project_id = p.id
    """)

    data = cursor.fetchall()

    return render_template('view_marks.html', data=data)

# ---------------- RUN ---------------- #
if __name__ == '__main__':
    app.run(debug=True)