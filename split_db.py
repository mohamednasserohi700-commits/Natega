"""
سكريبت لتقسيم students.db لأجزاء صغيرة (أقل من 25 ميجا لكل جزء)
عشان ترفعها على GitHub بالسحب والإفلات (Drag & Drop) لو ملف قاعدة البيانات كبير.

استخدمه بعد ما تشغّل build_db.py وتعمل students.db جديد، لو حجمه أكبر من 25 ميجا.

طريقة الاستخدام:
    python split_db.py
"""

import os
import math

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "students.db")
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db_parts")

# الحد الآمن لكل جزء (بايت) - أقل بكثير من حد الـ 25 ميجا بتاع GitHub
MAX_PART_SIZE = 20_000_000  # ~20 ميجا


def main():
    if not os.path.exists(SRC):
        print(f"الملف غير موجود: {SRC}")
        return

    size = os.path.getsize(SRC)

    if size <= 25_000_000:
        print(f"حجم students.db ({size / 1_000_000:.2f} MB) أصلًا أقل من 25 ميجا، مش محتاج تقسيم.")
        return

    num_parts = math.ceil(size / MAX_PART_SIZE)
    part_size = math.ceil(size / num_parts) + 1

    # امسح أجزاء قديمة لو موجودة
    if os.path.exists(OUT_DIR):
        for f in os.listdir(OUT_DIR):
            os.remove(os.path.join(OUT_DIR, f))
    os.makedirs(OUT_DIR, exist_ok=True)

    with open(SRC, "rb") as f:
        i = 0
        while True:
            chunk = f.read(part_size)
            if not chunk:
                break
            part_path = os.path.join(OUT_DIR, f"students.db.part{i:02d}")
            with open(part_path, "wb") as pf:
                pf.write(chunk)
            print(f"{part_path}: {os.path.getsize(part_path) / 1_000_000:.2f} MB")
            i += 1

    print(f"\nتم إنشاء {i} أجزاء في مجلد db_parts/")
    print("ارفع مجلد db_parts كامل على GitHub، الموقع هيجمّعها تلقائيًا وقت التشغيل.")


if __name__ == "__main__":
    main()
