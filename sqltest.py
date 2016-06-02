import sqlite3

con = sqlite3.connect('data.db')
data = con.cursor()

#data.execute("ALTER TABLE storage ADD COLUMN 'is_notify' 'INTEGER'")
#data.execute('SELECT * FROM storage')
#data.execute('DELETE FROM storage')
#data.execute('UPDATE storage SET last_id=96754 WHERE id=9')
#data.execute('UPDATE storage SET last_id=91540 WHERE id=105')
#con.commit()

#data.execute('UPDATE storage SET is_all_posts=0')
#con.commit()

#data.execute('UPDATE storage SET is_notify=1')
#con.commit()
data.execute('SELECT * FROM storage')
save = data.fetchall()
print save
con.close()