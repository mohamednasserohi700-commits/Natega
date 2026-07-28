"""
سكريبت لتحويل ملف الإكسيل (students.xlsx) إلى قاعدة بيانات SQLite (students.db)
شغّله كل ما يكون عندك ملف نتيجة جديد عايز تحدّث بيه الموقع.

طريقة الاستخدام:
    pip install pandas openpyxl
    python build_db.py students.xlsx

الملف لازم يحتوي على 4 أعمدة بنفس الأسماء دي بالظبط (أول صف):
    seating_no | arabic_name | total_degree | student_case_desc
"""

import sys
import os
import pandas as pd
import sqlite3

REQUIRED_COLUMNS = ["seating_no", "arabic_name", "total_degree", "student_case_desc"]


def main():
    if len(sys.argv) < 2:
        print("الاستخدام: python build_db.py path/to/students.xlsx")
        sys.exit(1)

    excel_path = sys.argv[1]
    if not os.path.exists(excel_path):
        print(f"الملف غير موجود: {excel_path}")
        sys.exit(1)

    print("جاري تحميل ملف الإكسيل، ممكن ياخد دقيقة لو الملف كبير...")
    df = pd.read_excel(excel_path)
    df.columns = [str(c).strip() for c in df.columns]

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        print(f"تحذير: الأعمدة دي مش موجودة في الملف: {missing}")
        print(f"الأعمدة الموجودة فعليًا: {list(df.columns)}")
        sys.exit(1)

    df["seating_no"] = df["seating_no"].astype(str).str.strip()
    df["student_case_desc"] = df["student_case_desc"].astype(str).str.strip()

    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "students.db")
    conn = sqlite3.connect(db_path)
    df.to_sql("students", conn, if_exists="replace", index=False)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_seating_no ON students(seating_no)")
    conn.commit()
    conn.close()

    print(f"تم إنشاء قاعدة البيانات بنجاح: {db_path}")
    print(f"عدد الطلاب: {len(df)}")


if __name__ == "__main__":
    main()
