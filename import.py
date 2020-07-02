import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


def main():
    f = open("books.csv")
    reader = csv.reader(f)

    line_count = 0
    for isbn, title, author, year in reader:
        if line_count == 0:
            line_count += 1
        else:
            db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                       {"isbn": isbn, "title": title, "author": author, "year": year})
            line_count += 1

    db.commit()
    print(f'added {line_count - 1} lines.')


if __name__ == "__main__":
    main()
