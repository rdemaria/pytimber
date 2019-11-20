import numpy as np
from scipy.stats import norm

mp = 938.272046  # MeV/c^2

# ----- beam parameters


def gammarel(EGeV, m0=mp):
    """returns the relativistic gamma
    Parameters:
    -----------
    EGeV: kinetic energy [GeV]
    m0: restmass [MeV]
    """
    return (EGeV * 1.0e3 + m0) / m0


def betarel(EGeV, m0=mp):
    g = gammarel(EGeV, m0=m0)
    return np.sqrt(1 - 1 / g ** 2)


def emitnorm(eps, EGeV, m0=mp):
    """returns normalized emittance in [um].
    input: eps [um], E [GeV], m0 [MeV]
    """
    gamma = gammarel(EGeV, m0)
    beta = betarel(EGeV, m0)
    return eps * (gamma * beta)


# ----- general functions


def exp_fit(x, a, tau):
    return a * np.exp(x / tau)


def movingaverage(data, navg):
    """calculates the moving average over
    *navg* data points"""
    weights = np.repeat(1.0, navg) / navg
    dataavg = np.convolve(data, weights, "valid")
    return dataavg


def gauss_pdf(x, c, a, mu, sig):
    """
    probability distribution function for a normal or Gaussian
    distribution:
      gauss_pdf(x,mu,sig) = c+a*1/(sqrt(2*sig**2*np.pi))*
                               exp(-((x-mu)**2/(2*sig**2)))

    Parameters:
    -----------
    c : constant offset to fit background of profiles
    a : amplitude to compensate for *c*. a should be close to 1 if c is
        small. a should be equal to 1 if c is zero.
    mu : mean of Gaussian distribution
    sig : sigma of Gaussian distribution
    """
    # norm.pdf(x) = exp(-x**2/2)/sqrt(2*pi)
    # and y = (x - loc) / scale
    # -> loc = mu, scale = sig
    # gauss_fit(x,mu,sig) = norm.pdf(x,mu,sig)/sig
    return c + a * norm.pdf(x, mu, sig)
