import os,time,gzip
import hashlib

import numpy as np

import sys

def id_to_path(num,nchar=3):
    sss=str(num)[::-1]
    sss=[sss[i:i+nchar][::-1] for i in range(0,len(sss),nchar)][::-1]
    sss=['0'+a for a in sss[:-1]]+sss[-1:]
    return os.path.join(*sss)

def hashfile(sha,fpath,BUF_SIZE = 65536):
    with open(fpath, 'rb') as f:
      while True:
        data = f.read(BUF_SIZE)
        if not data:
          break
        sha.update(data)
    return sha

def split_string_utf32(sss):
  sss=[a for a in sss.decode('utf-32').split('\0') if len(a)>0]
  return sss

def split_string(sss):
  sss=[a for a in sss.split('\0') if len(a)>0]
  return sss

class Page(object):
    def __init__(self,pagedir,pageid,
                      idxtype,count,idxa,idxb,
                      rectype,reclen,recsize,comp,checksum,check=False):
       self.pageid=pageid
       self.pagedir=pagedir
       self.rectype=rectype
       self.reclen=reclen
       self.idxtype=idxtype
       self.count=count
       self.idxa=idxa
       self.idxb=idxb
       self.recsize=recsize
       self.comp=comp
       self.checksum=checksum
       base=os.path.join(pagedir,id_to_path(self.pageid))
       self.pagepath=os.path.split(base)[0]
       self.recpath=os.path.join(base+'.rec')
       self.idxpath=os.path.join(base+'.idx')
       if self.reclen == -1:
         self.lenpath=os.path.join(base+'.len')
       if check and self.checksum is not None:
         assert self.check()
    @classmethod
    def from_data(cls,idx,rec,pagedir,pageid,comp=None):
       count=len(idx)
       if count==0 or len(rec)!=count:
          msg="Error creating Page %s: idx,rec length mismatch %d!=%d"
          raise ValueError(msg%(pageid,len(idx),len(rec)))
       lengths=[len(rrr) if hasattr(rrr,'__len__') else 0 for rrr in rec]
       if len(set(lengths))>1:
           reclen=-1
           out=[]
           nlengths=[]
           for rrr in rec:
               rrr=np.array(rrr)
               # for string, save data in zero terminated strings
               if 'S' in rrr.dtype.str:
                   nt=str(int(rrr.dtype.str[2:])+1)
                   rrr=np.array([rrr],dtype='S'+nt).view('S1').flatten()
               elif 'U' in rrr.dtype.str:
                   nt=str(int(rrr.dtype.str[2:])+1)
                   rrr=np.array([rrr],dtype='U'+nt).view('U1').flatten()
               out.append(rrr)
               nlengths.append(len(rrr))
           rec=out
           lengths=np.array(nlengths,dtype='<i8')
           rectypes=[rrr.dtype.str for rrr in rec]
           if len(set(rectypes))>1:
               msg="type mismatch in variable length data: %s"%rectypes
               raise ValueError(msg)
           rectype=rectypes[0]
           recsize=sum(lengths)*rec[0].dtype.itemsize
       else:
           rec=np.array(rec)
           recsize=rec.nbytes
           rectype=rec.dtype.str
           if rec.ndim==1:
               reclen=0
           else:
              reclen=rec.shape[1]
       idx=np.array(idx)
       idxtype=idx.dtype.str
       self=cls(pagedir,pageid,idxtype,count,idx[0],idx[-1],
                        rectype,reclen,int(recsize),comp,None)
       if not os.path.isdir(self.pagepath):
         os.makedirs(self.pagepath)
       idx.tofile(self.idxpath)
       sha = hashlib.md5()
       sha=hashfile(sha,self.idxpath)
       if reclen==-1:
          recfh=open(self.recpath,'wb')
          lengths.tofile(self.lenpath)
          sha=hashfile(sha,self.lenpath)
          [ rrr.tofile(recfh) for rrr in rec]
          recfh.close()
       else:
          if recsize>0:
            rec.tofile(self.recpath)
       if recsize>0:
         sha=hashfile(sha,self.recpath)
         if comp=='gzip':
            os.system("gzip %s"%self.recpath)
         self.checksum=sha.hexdigest()
       return self
    def get_all(self):
        return self.get_idx_all(),self.get_rec_all()
    def get_rec_all(self):
        if self.recsize==0:
            rec=np.array([[]]*self.count,dtype=self.rectype)
        else:
            if self.comp=='gzip':
                os.system("gunzip %s.gz"%self.recpath)
            cc=self.count
            reclen=self.reclen
            if reclen==-1:
                lengths=np.fromfile(self.lenpath,dtype='<i8',count=cc)
                recfh=open(self.recpath)
                rec=[np.fromfile(recfh,dtype=self.rectype,count=cc)
                                                      for cc in lengths]
                recfh.close()
                if 'S' in self.rectype:
                    rec=[split_string(rrr.tostring()) for rrr in rec]
                elif 'U' in self.rectype:
                    rec=[split_string_utf32(rrr.tostring()) for rrr in rec]
            elif reclen==0:
                rec=np.fromfile(self.recpath,dtype=self.rectype,count=cc)
            else:
                rec=np.fromfile(self.recpath,dtype=self.rectype,
                        count=cc*reclen)
                if len(rec)<cc*reclen:
                    msg="Error in Page %s: not enough records:%d!=%d*%d"
                    raise IOError(msg%(self.pageid,cc*reclen,cc,reclen))
                rec=rec.reshape(cc,reclen)
            if len(rec)!=self.count:
                msg='Error: Record mismatch in Page %d: %d read vs %d'
                raise IOError(msg%(self.pageid,len(rec),self.count))
        return rec
    def get_idx_all(self):
        cc=self.count
        idx=np.fromfile(self.idxpath,dtype=self.idxtype,count=cc)
        if len(idx)!=cc:
            msg='Error: Index mismatch in Page %d: %d read vs %d'
            raise IOError(msg%(self.pageid,len(idx),cc))
        return idx
    def delete(self):
        os.unlink(self.recpath)
        os.unlink(self.idxpath)
        if self.reclen==-1:
            os.unlink(self.lenpath)
    def _tolist(self):
        timestamp=os.path.getmtime(self.idxpath)
        return [self.pageid,self.idxtype,self.count,self.idxa,self.idxb,
               self.rectype,self.reclen,self.recsize,self.comp,
               timestamp,self.checksum]
    def get(self,idxa,idxb,skip=1):
        idx,rec=self.get_all()
        a=idx.searchsorted(idxa,side='left')
        b=idx.searchsorted(idxb,side='right')
        return idx[a:b:skip],rec[a:b:skip]
    def get_idx(self,idxa,idxb,skip=1):
        idx=self.get_idx_all()
        a=idx.searchsorted(idxa,side='left')
        b=idx.searchsorted(idxb,side='right')
        return idx[a:b:skip]
    def get_range(self,idxa,idxb):
        a=idx.searchsorted(idxa,side='left')
        b=idx.searchsorted(idxb,side='right')
        return a,b
    def get_count(self,idxa,idxb,skip=1):
        return len(self.get_idx(idxa,idxb,skip=skip))
    def get_recsize(self,idxa,idxb,skip=1):
        if self.reclen>=0:
            itemsize=self.recsize/self.count
            return self.count(idxa,idxb,skip=skip)*itemsize
        else:
           a,b=self.get_range(idxa,idxb)
           items=np.sum(np.fromfile(self.lenpath,
                                     dtype='<i8',count=cc)[a:b:skip])
           return items*np.dtype(self.rectype).itemsize
    def check(self):
        sha=hashlib.md5()
        sha=hashfile(sha,self.idxpath)
        if self.reclen==-1:
          sha=hashfile(sha,self.lenpath)
        if self.comp=='gzip':
          sha=hashfile(sha,self.recpath+'.gz')
        else:
          sha=hashfile(sha,self.recpath)
        res=sha.hexdigest()==self.checksum
        if res==False:
            print("Checksum failsed for page %s"%self.pageid)
        return res

