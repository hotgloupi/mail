import requests

from . import db

def get_resource(uri, conn = None):
    if conn is None: conn = db.conn()

    curs = conn.cursor()
    curs.execute(
        "SELECT content_type, payload FROM external_content WHERE uri = ?",
        (uri, )
    )
    res = curs.fetchone()
    if res:
        return tuple(res)

    print("Fetching '%s'" % uri)
    r = requests.get(uri)
    if r.status_code != 200:
        raise Exception("Cannot fetch '%s'" % uri)
    curs.execute(
        "INSERT INTO external_content (uri, content_type, payload) VALUES (?, ?, ?)",
        (uri, r.headers['content-type'], r.content)
    )
    conn.commit()

    return (r.headers['content-type'], r.content)
