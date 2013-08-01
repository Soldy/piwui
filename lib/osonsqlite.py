# -*- coding: utf-8 -*-


import sqlite3

def dictfactory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def connect (dbfile):
    out = sqlite3.connect(dbfile)
    out.row_factory = dictfactory
    return out



def make(dbcon, dbtable, dbname, dbtype, dbsize):
    dbcommand = "CREATE TABLE "+dbtable+" ("
    for i in range(0, len(dbname)):
         if i > 0:
             dbcommand += ", "
         dbcommand += dbname[i]
         if (dbtype[i] == "text") or (dbtype[i] == "varchar"):
             dbcommand += " text"
    dbcommand += ")"
    dbconi = dbcon.cursor()
    dbconi.execute(dbcommand)
    

def insert(dbcon, dbtable, dbname, dbvalue):
    dbnamefull = ""
    dbvaluefull = ""
    for i in range(0, len(dbname)):
        if i > 0 :
            dbnamefull  +=", "
            dbvaluefull  +=", "
        dbnamefull += dbname[i]
        dbvaluefull += "'"+dbvalue[i]+"'"
    dbcommand = ("insert into "+dbtable+" ("+dbnamefull+") values ("+dbvaluefull+")")
    dbconi = dbcon.cursor()
    dbconi.execute(dbcommand) 


def select(dbcon, dbtable, dbname, dbeq, dbvalue, dbxor):
    dbcommand = "select * from "
    dbcommand += dbtable
    dbcommand += " where "
    out = []
    for i in range(0, len(dbname)):
        if i > 0:
            if (dbxor[i] == "and") or (dbxor[i] == "AND"):
                dbcommand += " and "
        dbcommand += dbname[i]
        dbcommand += " "
        dbcommand += dbeq[i]
        dbcommand += " '"
        dbcommand += dbvalue[i]
        dbcommand += "' "
    dbconi = dbcon.cursor()
    dbconi.execute(dbcommand) 
    outs = dbconi.fetchall()
    for outi in outs:
        out.append(outi)
    return out

def update(dbcon, dbtable, dbname, dbeq, dbvalue, dbxor, dbnamen, dbvaluen):
    dbcommand = "UPDATE "+dbtable+" SET "
    for i in range(0, len(dbname)):
        if i > 0 :
            dbcommand +=", "
        dbcommand += dbnamen[i]+"= '"+dbvaluen[i]+"'"
    dbcommand += " WHERE "
    for i in range(0, len(dbname)):
        if i > 0:
            if (dbxor[i] == "and") or (dbxor[i] == "AND"):
                dbcommand += " AND "
        dbcommand += dbname[i]
        dbcommand += " "
        dbcommand += dbeq[i]
        dbcommand += " '"
        dbcommand += dbvalue[i]
        dbcommand += "' "
    dbconi = dbcon.cursor()
    dbconi.execute(dbcommand)




def commit(dbcon):
    dbcon.commit()    
    
def close(dbcon):
    dbcon.commit()
    dbcon.close()