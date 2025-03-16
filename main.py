from flask import Flask, render_template_string, request, redirect, url_for, session, send_from_directory
import os, random

app = Flask(__name__)
app.secret_key = "mysecretkey"

UPLOAD_FOLDER = "static/videos"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# =========================
#        بيانات الكورسات
# =========================
courses = {
    "الفرقة الأولى": {
        "الفصل الدراسي الأول": [
            "الشريعة الإسلامية",
            "المدخل للعلوم القانونية",
            "النظم السياسية والقانون الدستوري",
            "التنظيم الدولي"
        ],
        "الفصل الدراسي الثاني": [
            "الاقتصاد",
            "علم الإجرام",
            "لغة أجنبية ومصطلحاتها القانونية",
            "تاريخ النظم الاجتماعية والقانونية"
        ]
    },
    "الفرقة الثانية": {
        "الفصل الدراسي الأول": [
            "القانون المدني (أحكام الالتزام والإثبات)",
            "القانون المدني – مصادر الالتزام",
            "القانون الجنائي (القسم العام)",
            "القانون الإداري",
            "القانون الدولي العام"
        ],
        "الفصل الدراسي الثاني": [
            "الشريعة الإسلامية – الزواج والطلاق",
            "تاريخ القانون المصري",
            "أحوال شخصية لغير المسلمين",
            "لغة أجنبية ومصطلحاتها القانونية",
            "اقتصاد"
        ]
    },
    "الفرقة الثالثة": {
        "الفصل الدراسي الأول": [
            "القانون المدني (العقود المدنية)",
            "القانون الجنائي (القسم الخاص)",
            "القانون التجاري",
            "قانون العمل والتأمينات الاجتماعية",
            "المقرر القانوني بلغة أجنبية"
        ],
        "الفصل الدراسي الثاني": [
            "القضاء الإداري",
            "الشريعة الإسلامية (المواريث – الوصية – الوقف)",
            "قانون المرافعات",
            "مالية عامة وتشريع ضريبي",
            "قانون الجنسية"
        ]
    },
    "الفرقة الرابعة": {
        "الفصل الدراسي الأول": [
            "القانون الدولي الخاص",
            "أصول الفقه",
            "التنفيذ الجبري",
            "القضاء الدستوري",
            "القانون البحري والجوي"
        ],
        "الفصل الدراسي الثاني": [
            "حقوق عينية أصلية",
            "الإجراءات الجنائية",
            "القانون التجاري",
            "التأمينات العينية والشخصية"
        ]
    }
}

# =========================
#  تخزين الفيديوهات والقبول
# =========================
subject_videos = {}     # { subject: [ {filename, title}, ... ] }
accepted_students = {}  # { subject: [username, ...] }

# =========================
#  بيانات المستخدمين + OTP
# =========================
# users[username] = {
#   "password": "...",
#   "phone": "...",
#   "full_name": "...",
#   "ip": None/SomeIP,
#   "otp": None,
#   "otp_verified": False
# }
users = {}

# =========================
#   منع التحميل (DRM) بسيط
# =========================
drm_script = """
<script>
  // منع كليك يمين
  document.addEventListener('contextmenu', function(e) {
    e.preventDefault();
  }, false);

  // منع اختصارات مثل Ctrl+S, Ctrl+U, F12, Ctrl+Shift+I
  document.onkeydown = function(e) {
    // Ctrl+S أو Ctrl+U
    if (e.ctrlKey && (e.key === 's' || e.key === 'u')) {
      e.preventDefault();
      return false;
    }
    // F12
    if (e.keyCode === 123) {
      e.preventDefault();
      return false;
    }
    // Ctrl+Shift+I
    if (e.ctrlKey && e.shiftKey && e.keyCode === 73) {
      e.preventDefault();
      return false;
    }
  };
</script>
"""

# =========================
#   الثيم + خطوط + دارك مود
# =========================
theme_script = """
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap">
<script>
  if (localStorage.getItem("theme") === "dark") {
    document.body.classList.add("dark-mode");
  }
  function toggleTheme() {
    document.body.classList.toggle("dark-mode");
    if(document.body.classList.contains("dark-mode")) {
      localStorage.setItem("theme", "dark");
    } else {
      localStorage.setItem("theme", "light");
    }
  }
</script>
"""

# =========================
#   قوالب HTML
# =========================

# الصفحة الرئيسية
home_html = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <title>منصة العالمي</title>
  <style>
    body {
      font-family: 'Cairo', sans-serif;
      font-size: 24px;
      background-color: #CDA8CD;
      text-align: center;
      margin: 0;
      transition: background-color 0.3s, color 0.3s;
    }
    .dark-mode {
      background-color: #121212;
      color: #ffffff;
    }

    header img {
      width: 900px;
      height: 350px;
      border-radius: 15px;
      box-shadow: 0 0 30px rgba(128, 0, 128, 0.3);
      transition: transform 0.3s, box-shadow 0.3s;
    }
    header img:hover {
      transform: scale(1.05);
      box-shadow: 0 0 50px rgba(128, 0, 128, 0.5);
    }
    h1 {
      font-size: 36px;
      color: #800080;
      margin-top: 20px;
    }
    h2 {
      font-size: 30px;
      color: #4B0082;
    }
    p {
      font-size: 24px;
    }
    .btn {
      background-color: #800080;
      color: white;
      padding: 15px;
      font-size: 24px;
      margin: 10px;
      border: none;
      border-radius: 10px;
      width: 90%;
      max-width: 400px;
      cursor: pointer;
      text-decoration: none;
      display: inline-block;
      transition: box-shadow 0.3s, transform 0.3s;
    }
    .btn:hover {
      box-shadow: 0 5px 15px rgba(0,0,0,0.3);
      transform: scale(1.03);
    }
    .social a {
      display: block;
      margin: 5px;
      color: #800080;
      font-size: 24px;
      text-decoration: none;
    }
    .footer-made {
      font-size: 14px;
      color: #666;
      margin-top: 30px;
    }
  </style>
</head>
<body ondragstart="return false;" ondrop="return false;">
  {{ drm_script|safe }}
  <header>
    <img src="https://i.ibb.co/N646ppyG/enhanced-image.jpg" alt="شعار الكورس">
  </header>

  <h1>أهلا بيك في منصة العالمي</h1>
  <h2>منصتك نحو التفوق</h2>
  <p>شرح للمنهج كامل - مراجعات نهائية - مذكرات مختصرة لا يخرج عنها الامتحان</p>
  <p style="color:#4B0082;">رقم فودافون كاش: 01017105237</p>
  <p style="color:#4B0082;">واتساب: 01212415229</p>
  <button class="btn" onclick="toggleTheme()">تبديل الوضع (دارك/لايت)</button>
  <a href="{{ url_for('login') }}" class="btn">تسجيل الدخول</a>
  <a href="{{ url_for('register') }}" class="btn">إنشاء حساب جديد</a>
  <a href="{{ url_for('years') }}" class="btn">ابدأ الدراسة</a>
  <a href="{{ url_for('admin_login') }}" class="btn">لوحة تحكم الدكتور</a>
  <div class="social">
    <a href="https://www.facebook.com/groups/soot.al.shabab/" target="_blank">facebook</a>
    <a href="https://www.tiktok.com/@muhammed_abdelrahman" target="_blank">tiktok</a>
    <a href="https://www.instagram.com/muhammed_abdel_rahman" target="_blank">instagram</a>
  </div>
  <p class="footer-made">Made by Amany Saleh (01212827594)</p>
  {{ theme_script|safe }}
</body>
</html>
"""

# صفحة المادة (قوائم التشغيل)
subject_html = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <title>{{ subject }}</title>
  <style>
    body {
      font-family: 'Cairo', sans-serif;
      font-size: 24px;
      background-color: #E6E6FA;
      text-align: center;
      margin: 0;
      padding: 20px;
      transition: background-color 0.3s, color 0.3s;
    }
    .dark-mode {
      background-color: #121212;
      color: #ffffff;
    }
    .btn {
      background-color: #800080;
      color: white;
      padding: 15px;
      font-size: 24px;
      margin: 10px;
      border: none;
      border-radius: 10px;
      cursor: pointer;
      text-decoration: none;
      display: inline-block;
      width: 90%;
      max-width: 400px;
      transition: box-shadow 0.3s, transform 0.3s;
    }
    .btn:hover {
      box-shadow: 0 5px 15px rgba(0,0,0,0.3);
      transform: scale(1.03);
    }
    .video-list {
      max-width: 700px;
      margin: 20px auto;
      text-align: left;
    }
    .video-card {
      background-color: #fff;
      border-radius: 10px;
      margin: 20px 0;
      padding: 15px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.2);
      transition: transform 0.2s ease, box-shadow 0.2s ease;
      display: flex;
      align-items: center;
      gap: 20px;
    }
    .video-card:hover {
      transform: scale(1.02);
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .thumbnail-video {
      width: 200px;
      border-radius: 10px;
    }
    .video-info {
      flex: 1;
    }
    .video-title {
      font-size: 28px;
      color: #800080;
      margin-bottom: 10px;
      font-weight: bold;
    }
    .no-videos {
      text-align: center;
      font-size: 24px;
      color: #800080;
    }
    .header-subject {
      text-align: center;
      margin-bottom: 20px;
    }
    .header-subject h1 {
      margin: 0;
      padding: 0;
    }
  </style>
</head>
<body ondragstart="return false;" ondrop="return false;">
  {{ drm_script|safe }}
  <div class="header-subject">
    <h1>{{ subject }}</h1>
  </div>
  {% if videos %}
    <div class="video-list">
      {% for video in videos %}
      <div class="video-card">
        <video class="thumbnail-video" muted>
          <source src="{{ url_for('uploaded_file', filename=video.filename) }}" type="video/mp4">
        </video>
        <div class="video-info">
          <div class="video-title">{{ video.title }}</div>
          <a href="{{ url_for('watch_video', subject=subject, filename=video.filename) }}" class="btn">شاهد الفيديو</a>
        </div>
      </div>
      {% endfor %}
    </div>
  {% else %}
    <p class="no-videos">لا يوجد فيديوهات لهذه المادة بعد.</p>
  {% endif %}
  <button class="btn" onclick="toggleTheme()">تبديل الوضع (دارك/لايت)</button>
  <a href="{{ url_for('years') }}" class="btn">العودة للفرق</a>
  {{ theme_script|safe }}
</body>
</html>
"""

# صفحة مشاهدة الفيديو بالحجم الكبير
watch_video_html = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <title>مشاهدة الفيديو</title>
  <style>
    body {
      font-family: 'Cairo', sans-serif;
      font-size: 24px;
      background-color: #E6E6FA;
      text-align: center;
      margin: 0;
      padding: 20px;
      transition: background-color 0.3s, color 0.3s;
    }
    .dark-mode {
      background-color: #121212;
      color: #ffffff;
    }
    video {
      width: 80%;
      max-width: 800px;
      border-radius: 10px;
      margin: 20px 0;
    }
    .btn {
      background-color: #800080;
      color: white;
      padding: 15px;
      font-size: 24px;
      border: none;
      border-radius: 10px;
      cursor: pointer;
      width: 90%;
      max-width: 400px;
      margin: 10px;
      transition: box-shadow 0.3s, transform 0.3s;
    }
    .btn:hover {
      box-shadow: 0 5px 15px rgba(0,0,0,0.3);
      transform: scale(1.03);
    }
  </style>
</head>
<body ondragstart="return false;" ondrop="return false;">
  {{ drm_script|safe }}
  <h1>مشاهدة الفيديو: {{ video_title }}</h1>
  <video controls>
    <source src="{{ url_for('uploaded_file', filename=filename) }}" type="video/mp4">
    المتصفح لا يدعم تشغيل الفيديو.
  </video>
  <br>
  <button class="btn" onclick="toggleTheme()">تبديل الوضع (دارك/لايت)</button>
  <a href="{{ url_for('subject_page_route', subject=subject) }}" class="btn">العودة لقائمة الفيديوهات</a>
  {{ theme_script|safe }}
</body>
</html>
"""

# صفحات الفرق/الفصول (years_html, year_html, term_html) موجودة في نفس الأسلوب.  
years_html = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <title>الفرق الدراسية</title>
  <style>
    body {
      font-family: 'Cairo', sans-serif;
      font-size: 24px;
      background-color: #E6E6FA;
      text-align: center;
      margin: 0; padding: 20px;
      transition: background-color 0.3s, color 0.3s;
    }
    .dark-mode {
      background-color: #121212;
      color: #ffffff;
    }
    .btn {
      background-color: #800080;
      color: white;
      padding: 15px;
      font-size: 24px;
      margin: 10px;
      border: none;
      border-radius: 10px;
      width: 90%;
      max-width: 400px;
      cursor: pointer;
      text-decoration: none;
      display: inline-block;
      transition: box-shadow 0.3s, transform 0.3s;
    }
    .btn:hover {
      box-shadow: 0 5px 15px rgba(0,0,0,0.3);
      transform: scale(1.03);
    }
  </style>
</head>
<body>
  <h1>اختار الفرقة الدراسية</h1>
  {% for year in courses.keys() %}
    <a href="{{ url_for('year_page', year=year) }}" class="btn">{{ year }}</a><br>
  {% endfor %}
  <button class="btn" onclick="toggleTheme()">تبديل الوضع (دارك/لايت)</button>
  <a href="{{ url_for('home') }}" class="btn">العودة للصفحة الرئيسية</a>
  {{ theme_script|safe }}
</body>
</html>
"""

year_html = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <title>{{ year }}</title>
  <style>
    body {
      font-family: 'Cairo', sans-serif;
      font-size: 24px;
      background-color: #E6E6FA;
      text-align: center;
      margin: 0; padding: 20px;
      transition: background-color 0.3s, color 0.3s;
    }
    .dark-mode {
      background-color: #121212;
      color: #ffffff;
    }
    .btn {
      background-color: #800080;
      color: white;
      padding: 15px;
      font-size: 24px;
      margin: 10px;
      border: none;
      border-radius: 10px;
      width: 90%;
      max-width: 400px;
      cursor: pointer;
      text-decoration: none;
      display: inline-block;
      transition: box-shadow 0.3s, transform 0.3s;
    }
    .btn:hover {
      box-shadow: 0 5px 15px rgba(0,0,0,0.3);
      transform: scale(1.03);
    }
  </style>
</head>
<body>
  <h1>{{ year }}</h1>
  {% for term in courses[year].keys() %}
    <a href="{{ url_for('term_page', year=year, term=term) }}" class="btn">{{ term }}</a><br>
  {% endfor %}
  <button class="btn" onclick="toggleTheme()">تبديل الوضع (دارك/لايت)</button>
  <a href="{{ url_for('years') }}" class="btn">العودة للفرق</a>
  {{ theme_script|safe }}
</body>
</html>
"""

term_html = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <title>{{ term }} - {{ year }}</title>
  <style>
    body {
      font-family: 'Cairo', sans-serif;
      font-size: 24px;
      background-color: #E6E6FA;
      text-align: center;
      margin: 0; padding: 20px;
      transition: background-color 0.3s, color 0.3s;
    }
    .dark-mode {
      background-color: #121212;
      color: #ffffff;
    }
    .btn {
      background-color: #800080;
      color: white;
      padding: 15px;
      font-size: 24px;
      margin: 10px;
      border: none;
      border-radius: 10px;
      width: 90%;
      max-width: 400px;
      cursor: pointer;
      text-decoration: none;
      display: inline-block;
      transition: box-shadow 0.3s, transform 0.3s;
    }
    .btn:hover {
      box-shadow: 0 5px 15px rgba(0,0,0,0.3);
      transform: scale(1.03);
    }
  </style>
</head>
<body>
  <h1>{{ term }} - {{ year }}</h1>
  {% for subject in courses[year][term] %}
    <a href="{{ url_for('subject_page_route', subject=subject) }}" class="btn">{{ subject }}</a><br>
  {% endfor %}
  <button class="btn" onclick="toggleTheme()">تبديل الوضع (دارك/لايت)</button>
  <a href="{{ url_for('year_page', year=year) }}" class="btn">العودة للفرقة</a>
  {{ theme_script|safe }}
</body>
</html>
"""

# صفحة تسجيل الدخول
login_html = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <title>تسجيل الدخول</title>
  <style>
    body {
      font-family: 'Cairo', sans-serif;
      font-size: 24px;
      background-color: #E6E6FA;
      text-align: center;
      margin: 0; padding: 20px;
      transition: background-color 0.3s, color 0.3s;
    }
    .dark-mode {
      background-color: #121212;
      color: #ffffff;
    }
    input {
      padding: 10px;
      font-size: 24px;
      margin: 10px;
      width: 90%;
      max-width: 400px;
    }
    .btn {
      background-color: #800080;
      color: white;
      padding: 15px;
      font-size: 24px;
      border: none;
      border-radius: 10px;
      cursor: pointer;
      width: 90%;
      max-width: 400px;
      margin: 10px;
      transition: box-shadow 0.3s, transform 0.3s;
    }
    .btn:hover {
      box-shadow: 0 5px 15px rgba(0,0,0,0.3);
      transform: scale(1.03);
    }
  </style>
</head>
<body ondragstart="return false;" ondrop="return false;">
  {{ drm_script|safe }}
  <h1>تسجيل الدخول</h1>
  <form method="POST">
    <input type="text" name="username" placeholder="اسم المستخدم" required><br>
    <input type="password" name="password" placeholder="كلمة المرور" required><br>
    <button type="submit" class="btn">دخول</button>
  </form>
  <button class="btn" onclick="toggleTheme()">تبديل الوضع (دارك/لايت)</button>
  <a href="{{ url_for('home') }}" class="btn">العودة للصفحة الرئيسية</a>
  {{ theme_script|safe }}
</body>
</html>
"""

# صفحة التسجيل (الاسم الثلاثي + رقم الهاتف + باسورد)
register_html = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <title>إنشاء حساب جديد</title>
  <style>
    body {
      font-family: 'Cairo', sans-serif;
      font-size: 24px;
      background-color: #E6E6FA;
      text-align: center;
      margin: 0; padding: 20px;
      transition: background-color 0.3s, color 0.3s;
    }
    .dark-mode {
      background-color: #121212;
      color: #ffffff;
    }
    input {
      padding: 10px;
      font-size: 24px;
      margin: 10px;
      width: 90%;
      max-width: 400px;
    }
    .btn {
      background-color: #800080;
      color: white;
      padding: 15px;
      font-size: 24px;
      border: none;
      border-radius: 10px;
      cursor: pointer;
      width: 90%;
      max-width: 400px;
      margin: 10px;
      transition: box-shadow 0.3s, transform 0.3s;
    }
    .btn:hover {
      box-shadow: 0 5px 15px rgba(0,0,0,0.3);
      transform: scale(1.03);
    }
  </style>
</head>
<body ondragstart="return false;" ondrop="return false;">
  {{ drm_script|safe }}
  <h1>إنشاء حساب جديد</h1>
  <form method="POST">
    <input type="text" name="full_name" placeholder="الاسم الثلاثي" required><br>
    <input type="text" name="phone" placeholder="رقم الهاتف" required><br>
    <input type="text" name="username" placeholder="اسم المستخدم" required><br>
    <input type="password" name="password" placeholder="كلمة المرور" required><br>
    <button type="submit" class="btn">تسجيل</button>
  </form>
  <button class="btn" onclick="toggleTheme()">تبديل الوضع (دارك/لايت)</button>
  <a href="{{ url_for('home') }}" class="btn">العودة للصفحة الرئيسية</a>
  {{ theme_script|safe }}
</body>
</html>
"""

# صفحة دخول الدكتور
admin_login_html = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <title>دخول الدكتور</title>
  <style>
    body {
      font-family: 'Cairo', sans-serif;
      font-size: 24px;
      background-color: #E6E6FA;
      text-align: center;
      margin: 0; padding: 20px;
      transition: background-color 0.3s, color 0.3s;
    }
    .dark-mode {
      background-color: #121212;
      color: #ffffff;
    }
    input {
      padding: 10px;
      font-size: 24px;
      margin: 10px;
      width: 90%;
      max-width: 400px;
    }
    .btn {
      background-color: #800080;
      color: white;
      padding: 15px;
      font-size: 24px;
      border: none;
      border-radius: 10px;
      cursor: pointer;
      width: 90%;
      max-width: 400px;
      margin: 10px;
      transition: box-shadow 0.3s, transform 0.3s;
    }
    .btn:hover {
      box-shadow: 0 5px 15px rgba(0,0,0,0.3);
      transform: scale(1.03);
    }
  </style>
</head>
<body ondragstart="return false;" ondrop="return false;">
  {{ drm_script|safe }}
  <h1>دخول الدكتور</h1>
  <form method="POST">
    <input type="password" name="password" placeholder="كلمة مرور الدخول للدكتور" required><br>
    <button type="submit" class="btn">دخول</button>
  </form>
  <button class="btn" onclick="toggleTheme()">تبديل الوضع (دارك/لايت)</button>
  <a href="{{ url_for('home') }}" class="btn">العودة للصفحة الرئيسية</a>
  {{ theme_script|safe }}
</body>
</html>
"""

# لوحة تحكم الدكتور
admin_panel_html = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <title>لوحة تحكم الدكتور</title>
  <style>
    body {
      font-family: 'Cairo', sans-serif;
      font-size: 24px;
      background-color: #F8F8FF;
      text-align: center;
      margin: 0; padding: 20px;
      transition: background-color 0.3s, color 0.3s;
    }
    .dark-mode {
      background-color: #121212;
      color: #ffffff;
    }
    input, select {
      padding: 10px;
      font-size: 24px;
      margin: 10px;
      width: 90%;
      max-width: 400px;
    }
    .btn {
      background-color: #800080;
      color: white;
      padding: 15px;
      font-size: 24px;
      border: none;
      border-radius: 10px;
      cursor: pointer;
      width: 90%;
      max-width: 400px;
      margin: 10px;
      text-decoration: none;
      display: inline-block;
      transition: box-shadow 0.3s, transform 0.3s;
    }
    .btn:hover {
      box-shadow: 0 5px 15px rgba(0,0,0,0.3);
      transform: scale(1.03);
    }
  </style>
</head>
<body ondragstart="return false;" ondrop="return false;">
  {{ drm_script|safe }}
  <h1>لوحة تحكم الدكتور</h1>
  <form method="POST" enctype="multipart/form-data">
    <h2>تحميل فيديو</h2>
    <select name="year" required>
      {% for year in courses.keys() %}
        <option value="{{ year }}">{{ year }}</option>
      {% endfor %}
    </select>
    <select name="term" required>
      <option value="الفصل الدراسي الأول">الفصل الدراسي الأول</option>
      <option value="الفصل الدراسي الثاني">الفصل الدراسي الثاني</option>
    </select>
    <select name="subject" required>
      {% for yr, terms in courses.items() %}
        {% for term, subjects in terms.items() %}
          {% for subject in subjects %}
            <option value="{{ subject }}">{{ subject }}</option>
          {% endfor %}
        {% endfor %}
      {% endfor %}
    </select>
    <input type="text" name="video_title" placeholder="عنوان الفيديو" required>
    <input type="file" name="video" accept="video/*" required>
    <button type="submit" name="action" value="upload_video" class="btn">رفع الفيديو</button>
  </form>
  <form method="POST">
    <h2>قبول طالب</h2>
    <input type="text" name="student_name" placeholder="اسم الطالب" required>
    <select name="subject" required>
      {% for yr, terms in courses.items() %}
        {% for term, subjects in terms.items() %}
          {% for subject in subjects %}
            <option value="{{ subject }}">{{ subject }}</option>
          {% endfor %}
        {% endfor %}
      {% endfor %}
    </select>
    <button type="submit" name="action" value="accept_student" class="btn">قبول الطالب</button>
  </form>
  <button class="btn" onclick="toggleTheme()">تبديل الوضع (دارك/لايت)</button>
  <a href="{{ url_for('admin_courses') }}" class="btn">عرض محتويات الكورسات</a>
  <a href="{{ url_for('home') }}" class="btn">العودة للصفحة الرئيسية</a>
  {{ theme_script|safe }}
</body>
</html>
"""

# صفحة عرض محتويات الكورسات
admin_courses_html = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
   <meta charset="UTF-8">
   <title>عرض محتويات الكورسات</title>
   <style>
     body {
       font-family: 'Cairo', sans-serif;
       font-size: 24px;
       background-color: #F8F8FF;
       text-align: center;
       margin: 0; padding: 20px;
       transition: background-color 0.3s, color 0.3s;
     }
     .dark-mode {
       background-color: #121212;
       color: #ffffff;
     }
     .container {
       max-width: 1200px;
       margin: auto;
     }
     h1, h2, h3, h4, h5 {
       margin: 10px 0;
     }
     .subjects-grid {
         display: grid;
         grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
         gap: 20px;
         justify-items: center;
     }
     .subject {
         padding: 10px;
         background-color: #fff;
         border-radius: 10px;
         box-shadow: 0 0 10px rgba(0,0,0,0.1);
         width: 100%;
         max-width: 300px;
         transition: transform 0.2s ease, box-shadow 0.2s ease;
     }
     .subject:hover {
       transform: scale(1.02);
       box-shadow: 0 4px 12px rgba(0,0,0,0.3);
     }
     video {
         width: 100%;
         max-width: 400px;
         border-radius: 10px;
         margin: 10px 0;
     }
     .delete-btn {
       display: inline-block;
       background-color: #FF0000;
       color: #fff;
       padding: 5px 10px;
       border-radius: 5px;
       text-decoration: none;
       font-size: 18px;
       margin-top: 5px;
     }
     .btn {
       background-color: #800080;
       color: white;
       padding: 15px;
       font-size: 24px;
       border: none;
       border-radius: 10px;
       cursor: pointer;
       margin: 10px;
       text-decoration: none;
       display: inline-block;
       transition: box-shadow 0.3s, transform 0.3s;
     }
     .btn:hover {
       box-shadow: 0 5px 15px rgba(0,0,0,0.3);
       transform: scale(1.03);
     }
   </style>
</head>
<body ondragstart="return false;" ondrop="return false;">
  {{ drm_script|safe }}
   <div class="container">
     <h1>عرض محتويات الكورسات</h1>
     {% for year, terms in courses.items() %}
       <h2>{{ year }}</h2>
       {% for term, subjects in terms.items() %}
         <h3>{{ term }}</h3>
         <div class="subjects-grid">
         {% for subject in subjects %}
           <div class="subject">
             <h4>{{ subject }}</h4>
             {% if subject in subject_videos %}
               {% for video in subject_videos[subject] %}
                 <h5>{{ video.title }}</h5>
                 <video controls>
                   <source src="{{ url_for('uploaded_file', filename=video.filename) }}" type="video/mp4">
                   المتصفح لا يدعم تشغيل الفيديو.
                 </video>
                 <a href="{{ url_for('delete_video', subject=subject, filename=video.filename) }}" class="delete-btn" onclick="return confirm('هل تريد حذف هذا الفيديو؟');">⋮ حذف</a>
               {% endfor %}
             {% else %}
               <p>لا يوجد فيديوهات لهذه المادة.</p>
             {% endif %}
           </div>
         {% endfor %}
         </div>
       {% endfor %}
     {% endfor %}
     <button class="btn" onclick="toggleTheme()">تبديل الوضع (دارك/لايت)</button>
     <a href="{{ url_for('admin_panel') }}" class="btn">العودة للوحة التحكم</a>
   </div>
   {{ theme_script|safe }}
</body>
</html>
"""

# =========================
#       المسارات (Routes)
# =========================

@app.route("/")
def home():
    return render_template_string(home_html,
                                  drm_script=drm_script,
                                  theme_script=theme_script)

@app.route("/years")
def years():
    return render_template_string(years_html,
                                  courses=courses,
                                  drm_script=drm_script,
                                  theme_script=theme_script)

@app.route("/year/<year>")
def year_page(year):
    if year not in courses:
        return "الفرقة غير موجودة"
    return render_template_string(year_html,
                                  year=year,
                                  courses=courses,
                                  drm_script=drm_script,
                                  theme_script=theme_script)

@app.route("/year/<year>/term/<term>")
def term_page(year, term):
    if year not in courses or term not in courses[year]:
        return "الفصل الدراسي غير موجود"
    return render_template_string(term_html,
                                  year=year,
                                  term=term,
                                  courses=courses,
                                  drm_script=drm_script,
                                  theme_script=theme_script)

# منع الطالب من مشاهدة مادة ما لم يقبله الدكتور
@app.route("/subject/<subject>")
def subject_page_route(subject):
    if "user" not in session:
        return "يجب تسجيل الدخول أولاً"
    username = session["user"]
    # الطالب لازم يكون مقبول
    if subject not in accepted_students or username not in accepted_students[subject]:
        return "لم يتم قبولك في هذه المادة، لا يمكنك مشاهدة محتواها."
    vids = subject_videos.get(subject, [])
    return render_template_string(subject_html,
                                  subject=subject,
                                  videos=vids,
                                  drm_script=drm_script,
                                  theme_script=theme_script)

# صفحة مشاهدة الفيديو بحجم كبير
@app.route("/watch/<subject>/<filename>")
def watch_video(subject, filename):
    if "user" not in session:
        return "يجب تسجيل الدخول أولاً"
    username = session["user"]
    # لازم يكون مقبول في المادة
    if subject not in accepted_students or username not in accepted_students[subject]:
        return "لم يتم قبولك في هذه المادة."

    video_title = ""
    if subject in subject_videos:
        for vid in subject_videos[subject]:
            if vid["filename"] == filename:
                video_title = vid["title"]
                break

    return render_template_string(watch_video_html,
                                  subject=subject,
                                  filename=filename,
                                  video_title=video_title,
                                  drm_script=drm_script,
                                  theme_script=theme_script)

# =========================
#    تسجيل الدخول / OTP
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        uname = request.form.get("username")
        pwd = request.form.get("password")

        if uname in users:
            if users[uname]["password"] == pwd:
                user_ip = request.remote_addr
                # فحص IP
                if users[uname]["ip"] is None or users[uname]["ip"] == user_ip:
                    users[uname]["ip"] = user_ip
                    # دخول مباشر (بدون OTP حقيقي)
                    session["user"] = uname
                    return redirect(url_for("years"))
                else:
                    return "لا يمكنك تسجيل الدخول من جهاز آخر! اتصل بالدكتور."
            else:
                return "كلمة المرور غير صحيحة!"
        else:
            return "لا يوجد مستخدم بهذا الاسم!"
    return render_template_string(login_html,
                                  drm_script=drm_script,
                                  theme_script=theme_script)

# =========================
#    تسجيل حساب جديد
# =========================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name")
        phone = request.form.get("phone")
        uname = request.form.get("username")
        pwd = request.form.get("password")

        if uname in users:
            return "اسم المستخدم موجود بالفعل!"

        # انشاء مستخدم جديد
        users[uname] = {
            "password": pwd,
            "phone": phone,
            "full_name": full_name,
            "ip": None
        }
        # تسجيل دخول فوري
        session["user"] = uname
        return redirect(url_for("years"))
    return render_template_string(register_html,
                                  drm_script=drm_script,
                                  theme_script=theme_script)

# =========================
#  تسجيل الخروج
# =========================
@app.route("/logout")
def logout():
    if "user" in session:
        uname = session["user"]
        users[uname]["ip"] = None  # نسمح له بتسجيل الدخول لاحقًا من جهاز آخر
        session.pop("user", None)
    return redirect(url_for("home"))

# =========================
#    دخول الدكتور
# =========================
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        pwd = request.form.get("password")
        if pwd == "12345&67890muhamed.":
            session["admin"] = True
            return redirect(url_for("admin_panel"))
        else:
            return "كلمة مرور الدكتور خاطئة!"
    return render_template_string(admin_login_html,
                                  drm_script=drm_script,
                                  theme_script=theme_script)

# =========================
#    لوحة تحكم الدكتور
# =========================
@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        action = request.form.get("action")
        if action == "upload_video":
            year = request.form.get("year")
            term = request.form.get("term")
            subject = request.form.get("subject")
            video_title = request.form.get("video_title")
            video_file = request.files.get("video")
            if video_file:
                filename = video_file.filename
                video_path = os.path.join(UPLOAD_FOLDER, filename)
                video_file.save(video_path)
                if subject not in subject_videos:
                    subject_videos[subject] = []
                subject_videos[subject].append({"filename": filename, "title": video_title})
                return f"تم رفع الفيديو بنجاح إلى مادة {subject} في {term} - {year}"
        elif action == "accept_student":
            student_name = request.form.get("student_name")
            subject = request.form.get("subject")
            if subject and student_name:
                if subject not in accepted_students:
                    accepted_students[subject] = []
                if student_name not in accepted_students[subject]:
                    accepted_students[subject].append(student_name)
                return f"تم قبول الطالب {student_name} في مادة {subject}"

    return render_template_string(admin_panel_html,
                                  courses=courses,
                                  drm_script=drm_script,
                                  theme_script=theme_script)

@app.route("/admin-courses")
def admin_courses():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    return render_template_string(admin_courses_html,
                                  courses=courses,
                                  subject_videos=subject_videos,
                                  drm_script=drm_script,
                                  theme_script=theme_script)

@app.route("/delete_video/<subject>/<filename>")
def delete_video(subject, filename):
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    if subject in subject_videos:
        subject_videos[subject] = [
            vid for vid in subject_videos[subject]
            if vid["filename"] != filename
        ]
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    return redirect(url_for("admin_courses"))

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# =========================
#   تشغيل السيرفر
# =========================
if __name__ == "__main__":
    app.run(debug=True)
