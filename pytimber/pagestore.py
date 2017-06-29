import os,sys,shutil,tempfile

import sqlite3
import numpy as np

from .page import Page



try:
    isinstance("", basestring)
    def isstr(s):
        return isinstance(s, basestring)
except NameError:
    def isstr(s):
        return isinstance(s, str)


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
        out.extend(vv)
      return out

_suffixes = ['bytes', 'KiB', 'MiB', 'GiB', 'TiB', 'EiB', 'ZiB']

def human_readable(size,suffixes=' kMGTEZ'):
    order = int(np.log10(size)/3) if size else 0
    return ('%.4g%s'%(size/(10.**(order*3)),suffixes[order])).rstrip()



class PageStore(object):
    def __repr__(self):
        fmt="PageStore(%r,pagedir=%r,maxpagesize=%r)"
        return fmt%(self.dbname,self.pagedir,self.maxpagesize)
    def __init__(self,dbname,pagedir,maxpagesize=None,
                      checksum=False,
                      keep_deleted_pages=False,
                      readonly=False):
        try:
            if dbname.startswith('file:'):
               if readonly:
                  dbname+='?mode=ro'
               self.db=sqlite3.connect(dbname,
                       isolation_level="IMMEDIATE",uri=True)
            else:
               if readonly:
                 tmp=tempfile.mktemp()
                 shutil.copy2(dbname,tmp)
                 dbname=tmp
               self.db=sqlite3.connect(dbname,
                       isolation_level="IMMEDIATE")
        except sqlite3.Error as e:
          print(e.msg)
          print('Error creating database %s'%dbname)
          sys.exit(1)
        self.dbname=dbname
        self.create_db()
        self.set_pagedir(pagedir)
        self.set_var('maxpagesize',maxpagesize,2**24)
        self.checksum=checksum
        self.keep_deleted_pages=keep_deleted_pages
    def create_db(self):
        sql="""
        CREATE TABLE IF NOT EXISTS pages(
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
              created NUMERIC,
              checksum STRING,
              deleted NUMERIC);
        CREATE INDEX IF NOT EXISTS page_index ON pages(pageid);
        CREATE TABLE IF NOT EXISTS conf(
              variable STRING,
              value   STRING,
              timestamp STRING);"""
        self.db.executescript(sql)
        self.db.commit()
        return self
    def set_var(self,name,value,default=None):
        if value is None:
            value=self.get_var(name)
        if value is None:
            value=default
        setattr(self,name,value)
        return value
    def store_var(self,name,value):
        cur=self.db.cursor()
        sql="INSERT INTO conf VALUES (?,?,datetime('now'))"
        cur.execute(sql,(name,value))
        self.db.commit()
    def set_pagedir(self,dirpath):
        if dirpath is None:
            dirpath=self.get_var('pagedir','data')
        if not os.path.isdir(dirpath):
            os.mkdir(dirpath)
        dirpath=os.path.abspath(dirpath)
        self.set_var('pagedir',dirpath)
    def get_var(self,name,default=None):
        cur=self.db.cursor()
        sql="""SELECT value FROM conf
               WHERE variable=? ORDER BY timestamp DESC LIMIT 1"""
        ret=cur.execute(sql,(name,)).fetchone()
        if ret:
            return ret[0]
        else:
            return default
    def get_vars(self):
        cur=self.db.cursor()
        sql="""SELECT * FROM conf
               ORDER BY variable,timestamp"""
        ret=list(cur.execute(sql))
        return ret
    def get_last_pageid(self):
        cur=self.db.cursor()
        lastid=cur.execute("SELECT MAX(pageid) FROM pages").fetchone()[0]
        if lastid is None:
            return 0
        return lastid
    def delete(self):
        if os.path.exists(self.pagedir):
          shutil.rmtree(self.pagedir)
        os.unlink(self.dbname)
    def store_page(self,variable,idx,rec,commit=True):
        #print("Store page %s"%variable)
        pageid=self.get_last_pageid()+1
        page=Page.from_data(idx,rec,self.pagedir,pageid)
        sql="""INSERT INTO pages VALUES
             (?,?,?,?,?,?,?,?,?,?,?,?,?)"""
        self.db.execute(sql,[variable]+page._tolist()+[None])
        if commit:
          self.db.commit()
    def get_pages(self,variable,idxa=None,idxb=None):
        cur=self.db.cursor()
        idxa,idxb=self.get_lim(variable,idxa,idxb)
        sql="""SELECT pageid,idxtype,count,idxa,idxb,
                      rectype,reclen,recsize,comp,checksum
               FROM pages WHERE name==? AND idxb>=? AND idxa<=?
               AND deleted IS NULL
               ORDER BY idxa"""
        pages=list(cur.execute(sql,[variable,idxa,idxb]))
        return pages
    def get(self,variables,idxa=None,idxb=None):
        data={}
        if isstr(variables):
            varlist=self.search(variables)
        elif isinstance(variables, (list, tuple)):
            varlist=variables
        for variable in varlist:
            data[variable]=self.get_variable(variable,idxa=idxa,idxb=idxb)
        return data
    def get_variable(self,variable,idxa=None,idxb=None):
        idxa,idxb=self.get_lim(variable,idxa,idxb)
        pages=self.get_pages(variable,idxa,idxb)
        if len(pages)>0:
          page=Page(self.pagedir,*pages[0],check=True)
          out=[page.get(idxa,idxb)]
          for res in pages[1:-1]:
            page=Page(self.pagedir,*res,check=True)
            out.append(page.get_all())
          if len(pages)>1:
            page=Page(self.pagedir,*pages[-1],check=True)
            out.append(page.get(idxa,idxb))
          idx,rec=zip(*out)
          idx=concatenate(idx)
          rec=concatenate(rec)
        else:
          idx=np.array([]);rec=np.array([])
        return idx,rec
    def get_idx(self,variable,idxa=None,idxb=None):
        idxa,idxb=self.get_lim(variable,idxa,idxb)
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
    def count(self,variable,idxa=None,idxb=None):
        idxa,idxb=self.get_lim(variable,idxa,idxb)
        pages=self.get_pages(variable,idxa,idxb)
        if len(pages)>0:
          page=Page(self.pagedir,*pages[0])
          tot=page.get_count(idxa,idxb)
          for res in pages[1:-1]:
            tot+=res[2] #to change when using named_tupled
          if len(pages)>1:
            page=Page(self.pagedir,*pages[-1])
            tot+=page.get_count(idxa,idxb)
          return tot
        else:
          return 0
    def get_page(self,pageid):
        cur=self.db.cursor()
        sql="""SELECT pageid,idxtype,count,idxa,idxb,
                      rectype,reclen,recsize,comp,checksum
               FROM pages WHERE pageid=?"""
        page=cur.execute(sql,[pageid]).fetchone()
        return Page(self.pagedir,*page)
    def delete_page(self,page):
        cur=self.db.cursor()
        if self.keep_deleted_pages:
          sql="""UPDATE pages SET deleted=strftime('%s','now')
                 WHERE pageid==?"""
        else:
          sql="""DELETE FROM pages WHERE pageid==?"""
          #print("Delete page %s"%page.pageid)
        cur.execute(sql,[page.pageid])
        self.db.commit()
        if self.keep_deleted_pages is False:
           page.delete()
    def delete_variable(self,variable):
        for  page in self.get_pages(variable):
          page=Page(self.pagedir,*page)
          self.delete_page(page)
    def store(self,data):
        for variable,(idx,rec) in data.items():
            self.store_variable(variable,idx,rec)
    def store_variable(self,variable,idx,rec):
        count=len(idx)
        idx=np.array(idx)
        if count>0:
          if  len(rec)!=count:
            msg="idx,rec length mismatch %d!=%d"%(len(idx),len(rec))
            raise ValueError(msg)
          idxa=idx[0]
          idxb=idx[-1]
          pages=self.get_pages(variable,idxa,idxb)
          pages=[Page(self.pagedir,*res) for res in pages]
          for page in pages:
            if len(idx)>0:
             # if idx[0]<page.idxa:
             #   cut=idx.searchsorted(page.idxa)
#            #    self.merge_page(variable,page,idx[:cut],rec[:cut])
             #   self.store_page(variable,idx[:cut],rec[:cut])
             #   idx=idx[cut:];rec=rec[cut:]
              if idx[0]<=page.idxb:
                cut=idx.searchsorted(page.idxb,side='right')
                self.merge_page(variable,page,idx[:cut],rec[:cut])
                idx=idx[cut:];rec=rec[cut:]
          if len(idx)>0:
             self.store_page(variable,idx,rec)
        if self.maxpagesize>0:
           self.rebalance(variable,self.maxpagesize)
    def merge_page(self,variable,page,idx,rec):
       pidx,prec=page.get_all()
       nidx,nrec=merge(pidx,prec,idx,rec)
       self.store_page(variable,nidx,nrec,commit=False)
       self.delete_page(page)
    def search(self,searchexp="%"):
       cur=self.db.cursor()
       sql="""SELECT DISTINCT name FROM pages WHERE name LIKE ?"""
       res=cur.execute(sql,[str(searchexp)]).fetchall()
       return [rr[0] for rr in res]
    def get_lim(self,variable,idxa=None,idxb=None):
       cur=self.db.cursor()
       if idxa is None:
         sql="""SELECT MIN(idxa) FROM PAGES WHERE name==?"""
         idxa=cur.execute(sql,[variable]).fetchone()[0]
       if idxb is None:
         sql="""SELECT MAX(idxb) FROM PAGES WHERE name==?"""
         idxb=cur.execute(sql,[variable]).fetchone()[0]
       return idxa,idxb
    def rebalance(self,variables,maxpagesize):
       for variable in self.search(variables):
          self.rebalance_variable(variable,maxpagesize)
    def rebalance_variable(self,variable,maxpagesize):
       print("Rebalance %s"%variable)
       acc=0; tomerge=[]
       for pagedata in self.get_pages(variable):
           page=Page(self.pagedir,*pagedata)
           if acc!=0 or page.recsize<maxpagesize/2:
             acc+=page.recsize
             tomerge.append(page)
             if acc> maxpagesize:
               self.merge_pages(variable,tomerge)
               acc=0; tomerge=[]
       if len(tomerge)>1:
           self.merge_pages(variable,tomerge)
       return self
    def get_info(self,variable=None):
       cur=self.db.cursor()
       suf='FROM pages'
       if variable is not None:
         suf+=' WHERE name=="%s"'%variable
         out=''
       else:
         nvars=cur.execute("SELECT COUNT(DISTINCT name) FROM pages").fetchone()[0]
         out='%s variables, '%(human_readable(nvars))
       npages=cur.execute("SELECT COUNT(*)"+suf).fetchone()[0]
       nrecords=cur.execute("SELECT SUM(count)"+suf).fetchone()[0]
       nsize=cur.execute("SELECT SUM(recsize)"+suf).fetchone()[0]
       asize=cur.execute("SELECT AVG(recsize)"+suf).fetchone()[0]
       if npages>0:
         data=tuple(map(human_readable,(npages,nrecords,nsize,asize)))
         out+=("%s pages, %s records, %sB total, %sB/page"%data)
       return out
    def merge_pages(self,variable,pages):
        print("Merging %d pages"%len(pages))
        out=[page.get_all() for page in pages]
        idxlist,reclist=zip(*out)
        self.store_page(variable,concatenate(idxlist),concatenate(reclist))
        for page in pages:
          self.delete_page(page)
    def split_pages(self,variable,maxsize):
       for pagedata in self.get_pages(variable):
           page=Page(self.pagedir,*pagedata)
           if page.recsize>maxsize:
             chunks=int(page.recsize/maxsize)
             step=int(page.count/chunks)
             print("Splitting in %d pages"%chunks)
             for i in range(0,page.count,step):
               idx,rec=page.get_all()
               self.store_page(variable,idx[i:i+step],rec[i:i+step])
             self.delete_page(page)
    def prune_delete_pages(self,timestamp=None):
        cur=self.db.cursor()
        if timestamp is None:
            timestamp='now'
        sql="""SELECT pageid,idxtype,count,idxa,idxb,
                      rectype,reclen,recsize,comp,checksum
               FROM pages WHERE
               deleted < strftime('%s',?)
               """
        pages=list(cur.execute(sql,[timestamp]))
        for pagedata in pages:
            page=Page(self.pagedir,*pagedata)
            self.delete_page(page)

