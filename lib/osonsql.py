# -*- coding: utf-8 -*-

import osonsqlite


def connect (dbtype, dbaddr, dbport=None, dbuser=None, dbpass=None):
    if dbtype == "sqlite":
        return osonsqlite.connect(dbaddr)

def make(dbtyp, dbcon, dbtable, dbname, dbtype, dbsize):
    if dbtyp == "sqlite":
        osonsqlite.make(dbcon, dbtable, dbname, dbtype, dbsize)
    
def insert(dbtype, dbcon, dbtable, dbname, dbvalue):
    if dbtype == "sqlite":
        osonsqlite.insert(dbcon, dbtable, dbname, dbvalue)

def select(dbtype, dbcon, dbtable, dbname, dbeq, dbvalue, dbxor):
    if dbtype == "sqlite":
        return osonsqlite.select(dbcon, dbtable, dbname, dbeq, dbvalue, dbxor)

def update(dbtype, dbcon, dbtable, dbname, dbeq, dbvalue, dbxor, dbnamen, dbvaluen):
    if dbtype == "sqlite":
        return osonsqlite.update(dbcon, dbtable, dbname, dbeq, dbvalue, dbxor, dbnamen, dbvaluen)


def commit(dbtype, dbcon):
    if dbtype == "sqlite":
        osonsqlite.commit(dbcon)    
    
def close(dbtype, dbcon):
    if dbtype == "sqlite":
       osonsqlite.commit(dbcon) 
       osonsqlite.close(dbcon)