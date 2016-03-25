from pagestore import *
from numpy import *

pagedir='.'
idx=arange(400)
rec=zeros((400,4))
p=Page.from_data(idx,rec,pagedir,0)
assert all(p.get_rec()==rec)
assert all(p.get_idx()==idx)
p.delete()

def makedata(nrec,lrec,lrecr):
  idx=arange(nrec*1.0)
  val=[random.rand(lrec+int(random.rand()*lrecr)) for i in idx]
  return idx,val

idx,rec=makedata(300,8000,0)
p=Page.from_data(idx,rec,pagedir,0)
assert all(p.get_rec()==rec)
assert all(p.get_idx()==idx)
p.delete()

p=Page.from_data(idx,rec,pagedir,0,comp='gzip')
assert all(p.get_rec()==rec)
assert all(p.get_idx()==idx)
p.delete()


