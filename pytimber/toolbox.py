import numpy as np

mp      = 938.272046 #MeV/c^2

# ----- beam parameters
def gammarel(EGeV,m0=mp):
  """returns the relativistic gamma
  Parameters:
  -----------
  EGeV: kinetic energy [GeV]
  m0: restmass [MeV]
  """
  return (EGeV*1.e3+m0)/m0

def betarel(EGeV,m0=mp):
  g=gammarel(EGeV,m0=m0)
  return np.sqrt(1-1/g**2)

def emitnorm(eps,EGeV,m0=mp):
  """returns normalized emittance in [um].
  input: eps [um], E [GeV], m0 [MeV]
  """
  gamma= gammarel(EGeV,m0)
  beta = betarel(EGeV,m0)
  return eps*(gamma*beta)

# ----- general functions

def exp_fit(x,a,tau):
  return a*np.exp(x/tau)

def movingaverage(data,navg):
  """calculates the moving average over
  *navg* data points"""
  weights = np.repeat(1.0, navg)/navg
  dataavg = np.convolve(data, weights, 'valid')
  return dataavg

