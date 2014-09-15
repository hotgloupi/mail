

class Contact:

    def __init__(self, mail = None, fullname = None, id = None):
        self.mail = mail
        self.id = id
        self.fullname = fullname
        if id is None and mail is None:
            raise Exception("You must provide the id or the mail")


    def synchronize(self, conn):
        assert self.id is not None or self.fullname is not None
        curs = conn.cursor()
        if self.id is None:
            curs.execute(
                "SELECT id FROM contact WHERE email = ?", (self.mail, )
            )
            res = curs.fetchone()
            if res:
                self.id = res[0]

        if self.id is not None:
            if self.fullname is None or self.mail is None:
                curs.execute(
                    "SELECT email, fullname FROM contact WHERE id = ?",
                    (self.id, )
                )
                self.mail, self.fullname = curs.fetchone()
        else:
            if self.fullname is None:
                raise Exception("Cannot save a contact without a fullname")
            curs.execute(
                "INSERT INTO contact (id, email, fullname) VALUES (NULL, ?, ?)",
                (self.mail, self.fullname)
            )
            self.id = curs.lastrowid
        conn.commit()
        return self

    def __str__(self):
        return "%s <%s>" % (self.fullname, self.mail)
