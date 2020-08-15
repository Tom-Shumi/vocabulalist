from vocabulalist import app
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

#model class-----------

#User
class UserTbl(Base):
    __tablename__ = "usertbl"

    userid = Column(String(20), primary_key=True)
    password = Column(String(20))
    regdttm = Column(DateTime())
    upddttm = Column(DateTime())

    def to_dict(self):
        return {
            'userId':str(self.userid)
            ,'password':str(self.password)
            ,'regDtTm':str(self.regdttm)
            ,'updDtTm':str(self.upddttm)
        }

#Category
class CategoryTbl(Base):
    __tablename__ = "categorytbl"

    userid = Column(String(20), primary_key=True)
    catecd = Column(Integer(), primary_key=True)
    catename = Column(String(40))

    def to_dict(self):
        return {
            'userId':str(self.userid)
            ,'cateCd':str(self.catecd)
            ,'cateName':str(self.catename)
        }

#WordTbl
class WordTbl(Base):
    __tablename__ = "wordtbl"

    userid = Column(String(20), primary_key=True)
    wordcd = Column(Integer(), primary_key=True)
    word = Column(String(100))
    meaning = Column(String(100))
    catecd = Column(Integer())

    def to_dict(self):
        return {
            'userId':str(self.userid)
            ,'wordCd':str(self.wordcd)
            ,'word':str(self.word)
            ,'meaning':str(self.meaning)
            ,'cateCd':str(self.catecd)
        }

def init():
    db.create_all()