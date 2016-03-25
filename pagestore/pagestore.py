import os,sys,shutil

import sqlite3
import numpy as np

from page import Page

def merge(idx0,rec0,idx1,rec1):
    sel={};val=[rec0,rec1]
    for ii,iv in enumerate(idx0):
        sel[iv]=(0,ii)
    for ii,iv in enumerate(idx1):
        sel[iv]=(1,ii)
    idx=[];rec=[]
    for sv,(ir,ii) in sorted(sel.items()):
        idx.append(sv)
        rec.append(val[ir][ii])
    return idx,rec

def concatenate(val):
    try:
      return np.concatenate(val)
    except :
      out=[]
      for vv in val:
        out.extend(val)
      return out




class PageStore(object):
    def __init__(self,dbname,pagedir=None):
        self.dbname=dbname
        try:
            self.db=sqlite3.connect(dbname)
        except sqlite3.Error:
          print 'Error creating database %s'%dbname
          sys.exit(1)
        cur=self.db.cursor()
        sql="""CREATE TABLE IF NOT EXISTS pages(
              name   STRING,
              pageid INTEGER,
              idxtype STRING,
              count   INTEGER,
              idxa    NUMERIC,
              idxb    NUMERIC,
              rectype STRING,
              reclen  INTEGER,
              recsize INTEGER,
              comp    STRING,
              created STRING,
              checksum STRING,
              deleted STRING);"""
        cur.execute(sql)
        sql="""CREATE TABLE IF NOT EXISTS conf(
              variable STRING,
              value   STRING,
              timestamp STRING);"""
        cur.execute(sql)
        cur.close()
        if pagedir is None:
            pagedir=self.get_var('pagedir')
        else:
            self.set_pagedir(pagedir)
        self.db.commit()
    def set_var(self,name,value):
        cur=self.db.cursor()
        sql="INSERT INTO conf VALUES (?,?,datetime('now'))"
        cur.execute(sql,(name,value))
        cur.close()
        #setattr(self,name,value)
    def set_pagedir(self,dirpath):
        if not os.path.isdir(dirpath):
            os.mkdir(dirpath)
        dirpath=os.path.abspath(dirpath)
        self.set_var('pagedir',dirpath)
    def get_var(self,name,last=True):
        cur=self.db.cursor()
        sql="""SELECT value,timestamp FROM conf
               WHERE variable=? ORDER BY timestamp"""
        ret=list(cur.execute(sql,(name,)))
        if last:
            if len(ret)>0:
              ret=ret[-1][0]
            else:
              ret=None
        return ret
    def get_vars(self):
        cur=self.db.cursor()
        sql="""SELECT * FROM conf
               ORDER BY variable,timestamp"""
        ret=list(cur.execute(sql))
        return ret
    def get_last_pageid(self):
        cur=self.db.cursor()
        lastid=list(cur.execute("SELECT MAX(pageid) FROM pages"))[0][0]
        if lastid is None:
            return 0
        return lastid
    def __getattr__(self,variable):
        return self.get_var(variable,last=True)
    def delete(self):
        shutil.rmtree(self.pagedir)
        os.unlink(self.dbname)
    def store_page(self,variable,idx,rec):
        pageid=self.get_last_pageid()+1
        page=Page.from_data(idx,rec,self.pagedir,pageid)
        sql="""INSERT INTO pages VALUES
               (?,?,?,?,?,?,?,?,?,?,?,?,?)"""
        cur=self.db.cursor()
        cur.execute(sql,[variable]+page._tolist()+[None])
        self.db.commit()
    def get_pages(self,variable,idxa,idxb):
        cur=self.db.cursor()
        sql="""SELECT pageid,idxtype,count,idxa,idxb,
                      rectype,reclen,recsize,comp,checksum
               FROM pages WHERE name==? AND idxb>=? AND idxa<=?
               AND created < datetime("now") AND deleted IS NULL
               ORDER BY idxa"""
        pages=list(cur.execute(sql,[variable,idxa,idxb]))
        return pages
    def get_pages_all(self,variable):
        cur=self.db.cursor()
        sql="""SELECT pageid,idxtype,count,idxa,idxb,
                      rectype,reclen,recsize,comp,checksum
               FROM pages WHERE name==?
               AND created < datetime("now") AND deleted IS NULL
               ORDER BY idxa"""
        pages=list(cur.execute(sql,[variable]))
        return pages
    def get(self,variable,idxa,idxb):
        pages=self.get_pages(variable,idxa,idxb)
        page=Page(self.pagedir,*pages[0])
        out=[page.get(idxa,idxb)]
        for res in pages[1:-1]:
            page=Page(self.pagedir,*res)
            out.append(page.get_all())
        if len(pages)>1:
          page=Page(self.pagedir,*pages[-1])
          out.append(page.get(idxa,idxb))
        idx,rec=zip(*out)
        return concatenate(idx),concatenate(rec)
    def get_idx(self,variable,idxa,idxb):
        pages=self.get_pages(variable,idxa,idxb)
        page=Page(self.pagedir,*pages[0])
        out=[page.get_idx(idxa,idxb)]
        for res in pages[1:-1]:
            page=Page(self.pagedir,*res)
            out.append(page.get_idx_all())
        if len(pages)>1:
          page=Page(self.pagedir,*pages[-1])
          out.append(page.get_idx(idxa,idxb))
        return concatenate(out)
    def delete_page(self,page,keep=True):
        cur=self.db.cursor()
        sql="""UPDATE pages SET deleted=datetime("now")
               WHERE pageid==?"""
        cur.execute(sql,[page.pageid])
        if keep==False:
           page.delete()
        self.db.commit()
    def store(self,variable,idx,rec):
        count=len(idx)
        if count==0 or len(rec)!=count:
          msg="idx,rec length mismatch %d!=%d"%(len(idx),len(rec))
          raise ValueError,msg
        idxa=idx[0]
        idxb=idx[-1]
        pages=self.get_pages(variable,idxa,idxb)
        pages=[Page(self.pagedir,*res) for res in pages]
        for page in pages:
          if len(idx)>0:
           # if idx[0]<page.idxa:
           #   cut=idx.searchsorted(page.idxa)
#          #    self.merge_page(variable,page,idx[:cut],rec[:cut])
           #   self.store_page(variable,idx[:cut],rec[:cut])
           #   idx=idx[cut:];rec=rec[cut:]
            if idx[0]<=page.idxb:
              cut=idx.searchsorted(page.idxb,side='right')
              self.merge_page(variable,page,idx[:cut],rec[:cut])
              idx=idx[cut:];rec=rec[cut:]
        if len(idx)>0:
          self.store_page(variable,idx,rec)
    def merge_page(self,variable,page,idx,rec):
       pidx,prec=page.get_all()
       self.delete_page(page,keep=False)
       nidx,nrec=merge(pidx,prec,idx,rec)
       self.store_page(variable,nidx,nrec)
    def search(self,variable):
       cur=self.db.cursor()
       sql="""SELECT UNIQUE name FROM pages"""
       return list(execute(sql))
    def get_lim(self,variable):
       cur=self.db.cursor()
       sql="""SELECT MIN(idxa),MAX(idxb) FROM PAGES
              WHERE name==?"""
       a,b=list(cur.execute(sql,[variable]))[0]
       return a,b
    def rebalance(self,variable,size):
       a,b=self.get_lim(variable)
       pages=self.get_pages_all(variable)


