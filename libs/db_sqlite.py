# from db import Database
from libs.config import get_config
import sqlite3
import sys
try:
    # Python 3
    from itertools import zip_longest
except ImportError:
    # Python 2
    from itertools import izip_longest as zip_longest
from termcolor import colored

class SqliteDatabase():
  TABLE_SONGS = 'songs'
  TABLE_FINGERPRINTS = 'fingerprints'

  def __init__(self):
    self.connect()

  def connect(self):
    config = get_config()

    self.conn = sqlite3.connect(config['db.file'])
    self.conn.text_factory = str

    self.cur = self.conn.cursor()

    print(colored('sqlite - connection opened','white',attrs=['dark']))

  def __del__(self):
    self.conn.commit()
    self.conn.close()
    print(colored('sqlite - connection has been closed','white',attrs=['dark']))

  def query(self, query, values = []):
    self.cur.execute(query, values)

  def executeOne(self, query, values = []):
    self.cur.execute(query, values)
    return self.cur.fetchone()

  def executeAll(self, query, values = []):
    self.cur.execute(query, values)
    return self.cur.fetchall()

  def buildSelectQuery(self, table, params):
    conditions = []
    values = []

    for k, v in enumerate(params):
      key = v
      value = params[v]
      conditions.append("%s = ?" % key)
      values.append(value)

    conditions = ' AND '.join(conditions)
    query = "SELECT * FROM %s WHERE %s" % (table, conditions)

    return {
      "query": query,
      "values": values
    }

  def findOne(self, table, params):
    select = self.buildSelectQuery(table, params)
    return self.executeOne(select['query'], select['values'])

  def findAll(self, table, params):
    select = self.buildSelectQuery(table, params)
    return self.executeAll(select['query'], select['values'])

  def insert(self, table, params):
    keys = ', '.join(params.keys())
    values = params.values()

    query = "INSERT INTO songs (%s) VALUES (?, ?)" % (keys);

    self.cur.execute(query, values)
    self.conn.commit()

    return self.cur.lastrowid

  def insertMany(self, table, columns, values):
    def grouper(iterable, n, fillvalue=None):
      args = [iter(iterable)] * n
      return (filter(None, values) for values
          in zip_longest(fillvalue=fillvalue, *args))

    for split_values in grouper(values, 1000):
      query = "INSERT OR IGNORE INTO %s (%s) VALUES (?, ?, ?)" % (table, ", ".join(columns))
      self.cur.executemany(query, split_values)

    self.conn.commit()

  def get_song_hashes_count(self, song_id):
    query = 'SELECT count(*) FROM %s WHERE song_fk = %d' % (self.TABLE_FINGERPRINTS, song_id)
    rows = self.executeOne(query)
    return int(rows[0])

  def get_song_by_filehash(self, filehash):
    return self.findOne(self.TABLE_SONGS, {
      "filehash": filehash
    })

  def get_song_by_id(self, id):
    return self.findOne(self.TABLE_SONGS, {
      "id": id
    })

  def add_song(self, filename, filehash):
    song = self.get_song_by_filehash(filehash)

    if not song:
      song_id = self.insert(self.TABLE_SONGS, {
        "name": filename,
        "filehash": filehash
      })
    else:
      song_id = song[0]

    return song_id

  def store_fingerprints(self, values):
    self.insertMany(self.TABLE_FINGERPRINTS,
      ['song_fk', 'hash', 'offset'], values
    )
