import sqlite3

conn = sqlite3.connect("medigenie.db")
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE ai_reports ADD COLUMN clinical_intelligence TEXT")
    conn.commit()
    print("Added clinical_intelligence to ai_reports")
except Exception as e:
    print("Error:", e)

conn.close()
