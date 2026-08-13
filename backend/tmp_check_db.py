import sqlite3
import json

conn = sqlite3.connect('backend/medigenie_cdss.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM patients')
total_patients = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM ai_reports')
total_reports = cursor.fetchone()[0]

cursor.execute('SELECT risk_assessment FROM ai_reports')
rows = cursor.fetchall()
inferred_true = sum(1 for (r,) in rows if json.loads(r).get('is_model_inferred') is True)
inferred_false = sum(1 for (r,) in rows if json.loads(r).get('is_model_inferred') is False)
no_flag = sum(1 for (r,) in rows if 'is_model_inferred' not in json.loads(r))

print(f"Total patients : {total_patients}")
print(f"Total AI reports : {total_reports}")
print(f"is_model_inferred=True : {inferred_true}")
print(f"is_model_inferred=False : {inferred_false}")
print(f"Missing is_model_inferred: {no_flag}")

conn.close()
