from vocabulalist import app
from flask import Flask,render_template, request, session, url_for, redirect, jsonify, json, make_response, Response
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.sql import func, text
from sqlalchemy.orm import sessionmaker
from vocabulalist.models import UserTbl, CategoryTbl, WordTbl
from datetime import datetime

app.secret_key = b'random string...'

engine = create_engine(db_str)


@app.route('/', methods=['GET'])
def index():
    session.pop('LOGINID', None)
    session.pop('PAGENUM', None)
    session.pop('PREVFLG', None)
    session.pop('NEXTFLG', None)
    
    return render_template('top.html')

@app.route('/regUser', methods=['GET']) 
def regUser():
    #リクエスト情報の取得
    id = request.args.get('reg_id')
    pw = request.args.get('reg_pw')
    
    regDtTm = datetime.now()

    #DB接続
    Session = sessionmaker(bind=engine)
    ses = Session()
    rec = ses.query(UserTbl).filter(UserTbl.userid == id).count()
    if rec > 0:
        result = '0'
    else:
        user = UserTbl(userid=id, password=pw, regdttm=regDtTm, upddttm=regDtTm)
        ses.add(user)
        ses.commit()
        ses.close()
        result = '1'

    return json.dumps({'success':True, 'result':result }), 200, {'ContentType':'application/json'} 

@app.route('/checkUser', methods=['GET'])
def checkUser():
    id = request.args.get('login_id')
    pw = request.args.get('login_pw')

    #DB接続
    Session = sessionmaker(bind=engine)
    ses = Session()
    rec = ses.query(UserTbl).filter(UserTbl.userid == id, UserTbl.password == pw).count()
    if rec == 1:
        result = '1'
    else:
        result = '0'

    return json.dumps({'success':True, 'result':result }), 200, {'ContentType':'application/json'} 


@app.route('/login', methods=['POST'])
def login():
    userId = request.form['login_id']
    session['LOGINID'] = userId
    session['PAGENUM'] = 1

    wordList = getWordList(userId, 0)
    cateList = getCateList(userId)
    return render_template('menu.html'
                            , wordList = wordList
                            , cateList = cateList
                            , prevFlg = session['PREVFLG']
                            , nextFlg = session['NEXTFLG']
                            , result = '0')

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('LOGINID', None)
    session.pop('PAGENUM', None)
    session.pop('PREVFLG', None)
    session.pop('NEXTFLG', None)
    return render_template('top.html')

@app.route('/regCate', methods=['POST'])
def regCate():
    result = '0'
    userId = session['LOGINID']
    cateName = request.form.get('cateName', None)
    targetCate = request.form.get('cateList', None)
    cateCd = None
    command = request.form['command']

    #DB接続
    Session = sessionmaker(bind=engine)
    ses = Session()
    if command == 'add':
        t = text("SELECT CateCd FROM CategoryTbl WHERE UserId = '%s' AND CateCd = (SELECT MAX(CateCd) FROM CategoryTbl WHERE UserId = '%s') " % (userId, userId))
        for r in ses.execute(t):
            cateCd = r["catecd"] + 1
        cateCd = cateCd if cateCd != None else 1
        cate = CategoryTbl(userid=userId, catecd=cateCd, catename=cateName)
        ses.add(cate)
    else:
        if command == 'upd':
            t = text("UPDATE CategoryTbl SET CateName = '%s' WHERE UserId = '%s' AND CateCd = '%s'" % (cateName, userId, targetCate))
            ses.execute(t)
        elif command == 'del':
            t1 = text("DELETE FROM CategoryTbl WHERE UserId = '%s' AND CateCd = '%s'" % (userId, targetCate))
            ses.execute(t1)
            t2 = text("UPDATE WordTbl SET CateCd = NULL WHERE UserId = '%s' AND CateCd = '%s'" % (userId, targetCate))
            ses.execute(t2)
    ses.commit()
    ses.close()
    result = '1'

    wordList = getWordList(userId, 0)
    cateList = getCateList(userId)
    return render_template('menu.html'
                            , wordList = wordList
                            , cateList = cateList
                            , prevFlg = session['PREVFLG']
                            , nextFlg = session['NEXTFLG']
                            , result = result)

#DBからカテゴリリスト取得
def getCateList(userId):
    cateList = []
    Session = sessionmaker(bind=engine)
    ses = Session()
    t = text("SELECT CateCd, CateName FROM CategoryTbl WHERE UserId = '%s' ORDER BY CateCd" % (userId))
    for r in ses.execute(t):
        cateCd = r["catecd"]
        cateName = r["catename"]
        cateList.append((cateCd, cateName))
    return cateList

#DBから英単語リスト取得
def getWordList(userId, pageAction):
    wordList = []
    maxWordCnt = 50
    pageNum = session['PAGENUM']
    Session = sessionmaker(bind=engine)
    ses = Session()

    rec = ses.query(WordTbl).filter(WordTbl.userid == userId).count()
    maxPageCnt = rec // maxWordCnt
    if rec % maxWordCnt != '0':
        maxPageCnt = maxPageCnt + 1

    if pageAction == '1' and pageNum != '1':
        pageNum = pageNum - 1
    elif pageAction == '2' and pageNum != maxPageCnt:
        pageNum = pageNum + 1

    offset = ((pageNum - 1) * maxWordCnt)

    t = text("SELECT w.WordCd, w.Word, w.Meaning, w.CateCd, c.CateName FROM WordTbl w LEFT JOIN CategoryTbl c ON w.CateCd = c.CateCd WHERE w.UserId = '%s' AND c.UserId = '%s' ORDER BY WordCd DESC LIMIT %s OFFSET %s" % (userId, userId, maxWordCnt, offset))
    for r in ses.execute(t):
        wordCd = r["wordcd"]
        english = r["word"]
        meaning = r["meaning"]
        cateCd = r["catecd"]
        cateName = r["catename"]
        cateName = cateName if cateName != None else "-"
        wordList.append((wordCd, english, meaning, cateCd, cateName))
    session['PAGENUM'] = pageNum
    prevFlg = False
    if pageNum != 1:
        prevFlg = True
    nextFlg = False
    if pageNum != maxPageCnt:
        nextFlg = True
    session['PREVFLG'] = prevFlg
    session['NEXTFLG'] = nextFlg

    return wordList


@app.route('/regWord', methods=['POST'])
def regWord():
    result = '0'
    userId = session['LOGINID']
    english = request.form.get('english', None)
    meaning = request.form.get('meaning', None)
    cateCd =  request.form.get('cateListWord', None)
    addWordCd = None
    updWordCd = request.form.get('updWordCd', "None")

    #DB接続
    Session = sessionmaker(bind=engine)
    ses = Session()
    if updWordCd == "None":
        t = text("SELECT WordCd FROM WordTbl WHERE UserId = '%s' AND WordCd = (SELECT MAX(WordCd) FROM WordTbl WHERE UserId = '%s') " % (userId, userId))
        for r in ses.execute(t):
            addWordCd = r["wordcd"] + 1
        addWordCd = addWordCd if addWordCd != None else 1
        word = WordTbl(userid=userId, wordcd=addWordCd, word=english, meaning=meaning, catecd=cateCd)
        ses.add(word)
    else:
        t = text("UPDATE WordTbl SET Word = '%s', Meaning = '%s', CateCd = '%s' WHERE UserId = '%s' AND WordCd = '%s'" % (english, meaning, cateCd, userId, updWordCd))
        ses.execute(t)

    ses.commit()
    ses.close()
    result = '1'

    wordList = getWordList(userId, 0)
    cateList = getCateList(userId)
    return render_template('menu.html'
                            , wordList = wordList
                            , cateList = cateList
                            , prevFlg = session['PREVFLG']
                            , nextFlg = session['NEXTFLG']
                            , result = result)

@app.route('/delWord', methods=['POST'])
def delWord():
    result = '0'
    userId = session['LOGINID']
    wordCd = request.form.get('delWordCd', None)

    #DB接続
    Session = sessionmaker(bind=engine)
    ses = Session()

    t = text("DELETE FROM WordTbl WHERE UserId = '%s' AND WordCd = '%s'" % (userId, wordCd))
    ses.execute(t)
    ses.commit()
    ses.close()
    result = '1'

    wordList = getWordList(userId, 0)
    cateList = getCateList(userId)
    return render_template('menu.html'
                            , wordList = wordList
                            , cateList = cateList
                            , prevFlg = session['PREVFLG']
                            , nextFlg = session['NEXTFLG']
                            , result = result)

@app.route('/searchWord', methods=['POST'])
def searchWord():
    result = '0'
    userId = session['LOGINID']
    english = request.form.get('searchEnglish', None)
    meaning = request.form.get('searchMeaning', None)
    cateCd = request.form.get('cateListSearch', None)
    allFlg = request.form.get('allSearch', '0')
    engSql = ""
    meanSql = ""
    cateSql = ""
    wordList = []

    Session = sessionmaker(bind=engine)
    ses = Session()
    if allFlg == '0':

        sql = "SELECT w.WordCd, w.Word, w.Meaning, w.CateCd, c.CateName FROM WordTbl w LEFT JOIN CategoryTbl c ON w.CateCd = c.CateCd WHERE w.UserId = '%s' AND c.UserId = '%s'" % (userId, userId)
        orderBy = " ORDER BY WordCd DESC "
        if english != None:
            engSql = " AND w.Word LIKE '%%%s%%'" % (english)
        if meaning != None:
            meanSql = " AND w.Meaning LIKE '%%%s%%'" % (meaning)
        if not(cateCd == "None" or cateCd == None) :
            cateSql = " AND w.CateCd = '%s'" % (cateCd)

        sql = sql + engSql + meanSql + cateSql + orderBy
    
        t = text(sql)
        for r in ses.execute(t):
            wordCd = r["wordcd"]
            english = r["word"]
            meaning = r["meaning"]
            cateCd = r["catecd"]
            cateName = r["catename"]
            cateName = cateName if cateName != None else "-"
            wordList.append((wordCd, english, meaning, cateCd, cateName))
    else:
        wordList = getWordList(userId, 0)

    cateList = getCateList(userId)
    return render_template('menu.html'
                            , wordList = wordList
                            , cateList = cateList
                            , prevFlg = session['PREVFLG']
                            , nextFlg = session['NEXTFLG']
                            , result = result)

@app.route('/paging', methods=['POST'])
def paging():
    result = '0'
    userId = session['LOGINID']
    pageAction = request.form.get('pageAction', None)

    wordList = getWordList(userId, pageAction)
    cateList = getCateList(userId)
    return render_template('menu.html'
                            , wordList = wordList
                            , cateList = cateList
                            , prevFlg = session['PREVFLG']
                            , nextFlg = session['NEXTFLG']
                            , result = result)