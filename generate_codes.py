"""
سكريبت بسيط لتوليد أكواد تفعيل جديدة لخاصية "البحث بالاسم" المدفوعة.

الاستخدام:
    python generate_codes.py            # يولد 10 أكواد افتراضيًا
    python generate_codes.py 30         # يولد 30 كود

الأكواد بتتضاف في نهاية ملف activation_codes.txt، وكل كود منها صالح
للاستخدام مرة واحدة بس (بيتشال من الملف أول ما حد يستخدمه في الموقع).
"""

import os
import secrets
import sys
import string

BASE_DIR = os.path.dirname(__file__)
ACTIVATION_CODES_FILE = os.path.join(BASE_DIR, "activation_codes.txt")

ALPHABET = string.ascii_uppercase + string.digits  # حروف كبيرة + أرقام (سهل النسخ من على الموبايل)


def generate_code(length=8):
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 10

    existing = set()
    if os.path.exists(ACTIVATION_CODES_FILE):
        with open(ACTIVATION_CODES_FILE, "r", encoding="utf-8") as f:
            existing = {line.strip() for line in f if line.strip()}

    new_codes = []
    while len(new_codes) < count:
        code = generate_code()
        if code not in existing and code not in new_codes:
            new_codes.append(code)

    with open(ACTIVATION_CODES_FILE, "a", encoding="utf-8") as f:
        for code in new_codes:
            f.write(code + "\n")

    print(f"تم توليد {count} كود جديد وإضافتهم لملف {ACTIVATION_CODES_FILE}:\n")
    for code in new_codes:
        print(code)


if __name__ == "__main__":
    main()
