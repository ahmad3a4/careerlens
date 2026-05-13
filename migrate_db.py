import sqlite3

conn = sqlite3.connect('careerlens.db')
c = conn.cursor()

cols = [
    ('job_title', 'TEXT'),
    ('job_company', 'TEXT'),
    ('pi_alerted', 'BOOLEAN DEFAULT 0')
]

for col_name, col_type in cols:
    try:
        c.execute(f'ALTER TABLE seen_jobs ADD COLUMN {col_name} {col_type}')
        print(f"Added column {col_name}")
    except sqlite3.OperationalError:
        print(f"Column {col_name} already exists")

conn.commit()
conn.close()
print("Migration finished")
