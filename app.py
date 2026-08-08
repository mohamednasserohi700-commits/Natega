import os
import glob
import sqlite3
from flask import Flask, render_template, request, g

app = Flask(__name__)

BASE_DIR = os.path.dirname(__file__)
DB_FILE = os.path.join(BASE_DIR, "students.db")
DB_PARTS_DIR = os.path.join(BASE_DIR, "db_parts")


def ensure_db_assembled():
    """لو students.db مش موجود لكن أجزاؤه موجودة في db_parts/، يجمّعها في ملف واحد."""
    if os.path.exists(DB_FILE):
        return

    part_files = sorted(glob.glob(os.path.join(DB_PARTS_DIR, "students.db.part*")))
    if not part_files:
        return

    with open(DB_FILE, "wb") as out_f:
        for part_path in part_files:
            with open(part_path, "rb") as part_f:
                out_f.write(part_f.read())


ensure_db_assembled()

# أسماء الأعمدة الحقيقية في قاعدة البيانات
COL_SEAT = "seating_no"
COL_NAME = "arabic_name"
COL_TOTAL = "total_degree"
COL_STATUS = "student_case_desc"

# تحويل نص الحالة الخام (زي ما هو في الملف) لشكل واضح للعرض + لون مناسب
STATUS_MAP = {
    "ناجح دور أول": {"label": "ناجح", "css_class": "status-pass", "icon": "✅"},
    "دور ثان": {"label": "دور ثانٍ", "css_class": "status-second", "icon": "⚠️"},
    "راسب دور أول": {"label": "راسب", "css_class": "status-fail", "icon": "❌"},
    "غياب كلى دور أول": {"label": "غياب كلي", "css_class": "status-absent", "icon": "⚪"},
}

DEFAULT_STATUS = {"label": None, "css_class": "status-second", "icon": "ℹ️"}

# رابط موقع التنسيق الإلكتروني الرسمي التابع لوزارة التعليم العالي والبحث العلمي
TANSIK_URL = "https://tansik.digital.gov.eg/"

# الحد الأقصى للمجموع الكلي (المجموع من 320)
MAX_TOTAL = 320

# تصنيف التقدير العام حسب النسبة المئوية من المجموع الكلي
GRADE_BANDS = [
    (85, "ممتاز", "grade-excellent"),
    (75, "جيد جدًا", "grade-verygood"),
    (65, "جيد", "grade-good"),
    (50, "مقبول", "grade-pass"),
    (0, "ضعيف", "grade-weak"),
]


def compute_grade(total):
    try:
        percentage = (float(total) / MAX_TOTAL) * 100
    except (TypeError, ZeroDivisionError, ValueError):
        return None

    for threshold, label, css_class in GRADE_BANDS:
        if percentage >= threshold:
            return {"label": label, "css_class": css_class, "percentage": round(percentage, 1)}
    return None


def get_db():
    """فتح اتصال بقاعدة البيانات لكل طلب (وإعادة استخدامه لو موجود بالفعل)."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_FILE)
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def format_status(raw_status):
    info = STATUS_MAP.get(raw_status)
    if info is None:
        # لو ظهرت قيمة حالة جديدة مش متوقعة، نعرضها زي ما هي بدل ما نكسر الصفحة
        info = dict(DEFAULT_STATUS)
        info["label"] = raw_status
    return info


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


def build_result(row):
    seat_number, name, total, raw_status = row
    status_info = format_status(raw_status)
    if isinstance(total, float) and total.is_integer():
        total = int(total)
    grade_info = compute_grade(total)
    return {
        "seat_number": seat_number,
        "name": name,
        "total": total,
        "max_total": MAX_TOTAL,
        "status_label": status_info["label"],
        "status_class": status_info["css_class"],
        "status_icon": status_info["icon"],
        "grade_label": grade_info["label"] if grade_info else None,
        "grade_class": grade_info["css_class"] if grade_info else None,
        "grade_percentage": grade_info["percentage"] if grade_info else None,
        # التسجيل في موقع التنسيق بيبقى متاح بس للطلاب الناجحين
        "can_register_tansik": status_info["css_class"] == "status-pass",
        "tansik_url": TANSIK_URL,
    }


@app.route("/search", methods=["POST"])
def search():
    search_type = request.form.get("search_type", "seat")

    if search_type == "name":
        return search_by_name()
    return search_by_seat()


def search_by_seat():
    seat_number = request.form.get("seat_number", "").strip()

    if not seat_number:
        return render_template("index.html", error="من فضلك ادخل رقم الجلوس", active_tab="seat")

    try:
        db = get_db()
        row = db.execute(
            f"SELECT {COL_SEAT}, {COL_NAME}, {COL_TOTAL}, {COL_STATUS} "
            f"FROM students WHERE {COL_SEAT} = ?",
            (seat_number,),
        ).fetchone()
    except Exception:
        return render_template(
            "index.html",
            error="حدث خطأ في الاتصال بقاعدة البيانات، حاول لاحقًا",
            active_tab="seat",
        )

    if row is None:
        return render_template(
            "index.html",
            error="لا توجد نتيجة لرقم الجلوس المدخل، تأكد من الرقم وحاول مرة أخرى",
            seat_number=seat_number,
            active_tab="seat",
        )

    return render_template("result.html", result=build_result(row))


MAX_NAME_RESULTS = 30


def search_by_name():
    name_query = request.form.get("student_name", "").strip()

    if not name_query:
        return render_template("index.html", error="من فضلك ادخل اسم الطالب", active_tab="name")

    if len(name_query) < 3:
        return render_template(
            "index.html",
            error="اكتب 3 أحرف على الأقل من اسم الطالب عشان البحث يبقى أدق",
            name_query=name_query,
            active_tab="name",
        )

    try:
        db = get_db()
        rows = db.execute(
            f"SELECT {COL_SEAT}, {COL_NAME}, {COL_TOTAL}, {COL_STATUS} "
            f"FROM students WHERE {COL_NAME} LIKE ? LIMIT {MAX_NAME_RESULTS + 1}",
            (f"%{name_query}%",),
        ).fetchall()
    except Exception:
        return render_template(
            "index.html",
            error="حدث خطأ في الاتصال بقاعدة البيانات، حاول لاحقًا",
            active_tab="name",
        )

    if not rows:
        return render_template(
            "index.html",
            error="لا يوجد طلاب بهذا الاسم، تأكد من كتابة الاسم صح وحاول مرة أخرى",
            name_query=name_query,
            active_tab="name",
        )

    # طالب واحد بس مطابق -> نعرض نتيجته مباشرة
    if len(rows) == 1:
        return render_template("result.html", result=build_result(rows[0]))

    truncated = len(rows) > MAX_NAME_RESULTS
    results = [build_result(r) for r in rows[:MAX_NAME_RESULTS]]

    return render_template(
        "results_list.html",
        results=results,
        name_query=name_query,
        truncated=truncated,
    )


@app.route("/result/<seat_number>", methods=["GET"])
def view_result(seat_number):
    seat_number = seat_number.strip()
    try:
        db = get_db()
        row = db.execute(
            f"SELECT {COL_SEAT}, {COL_NAME}, {COL_TOTAL}, {COL_STATUS} "
            f"FROM students WHERE {COL_SEAT} = ?",
            (seat_number,),
        ).fetchone()
    except Exception:
        return render_template(
            "index.html", error="حدث خطأ في الاتصال بقاعدة البيانات، حاول لاحقًا"
        )

    if row is None:
        return render_template(
            "index.html",
            error="لا توجد نتيجة لرقم الجلوس المدخل",
        )

    return render_template("result.html", result=build_result(row))


@app.route("/health")
def health():
    try:
        db = get_db()
        count = db.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        return {"status": "ok", "students_count": count}
    except Exception as e:
        return {"status": "error", "detail": str(e)}, 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
