'''Modulo para identificacion de singletes y multipletes, evaluacion de ROI, 
fiteo y calculo del area neta de los picos detetados con el modulo peaksearch'''
import numpy as np
import matplotlib.pyplot as plt
from readfile import *
from peaksearch import *
# import dictio as wrd
from scipy.optimize import least_squares
#%%
class Peak(object):
    def __init__(self, n_peak=0, fit_data={'x':[0, 0, 0, 0]},\
                 roi_ch=None, curv_fit=None, bkg=None, npa=0,\
                     num_peak=1, tot_peak=1):
        self.n_peak = n_peak
        self.coef = fit_data['x']
        self.fit_data = fit_data
        self.roi_ch = roi_ch
        self.num_peak = num_peak
        self.tot_peak = tot_peak
        self.npa = npa
        self.cen_ch = self.coef[3]
        self.fwhm = self.coef[1]*np.sqrt(8*np.log(2))
        self.curv_fit = curv_fit
        self.bkg = bkg
        self.roi_ener = None
        self.cen_ener = None
#%%
def legen_r_w(n):
    pbb = np.array([1])
    pb = np.array([1, 0])
    if n == 0:
        co = pbb
    elif n == 1:
        co = pb
    else:
        for i in range(2, n+1):
            co = ((2*i-1)*np.append(pb, [0])-(i-1)*np.append([0, 0], pbb))/i
            pbb = pb
            pb = co
    root = np.sort(np.roots(co))
    weight = np.zeros(n)
    for i in range(n):
        y = np.zeros(n); y[i] = 1
        p = np.polyfit(root, y, n-1)
        P = np.polyint(p)
        weight[i] = np.polyval(P, 1)-np.polyval(P, -1)
    return root, weight
def integrate(func, coefficients, ch_ini, ch_fin, peak_center = 0, n = 16):
    '''integrate(func, coefficients, peak_center, ch_ini, ch_fin, n=16)
    \nParámetros:
        func \: string
            Nombre de la función
        coefficients \: array_like
            Coeficientes ajustados por NL LSQ
        peak_center \: float
            Canal central del Pico de Energía Completa
        ch_ini \: int or float
            Canal Inicial de la ROI a integrar
        ch_fin \: int or float
            Canal Final de la ROI a integrar
        n \: int, optional
            Orden de la cuadratura de Gauss-Legendre'''
    x, w = legen_r_w(n)
    while func(coefficients, ch_ini, peak_center) > 1:
        ch_ini -= 1
    while func(coefficients, ch_fin, peak_center) > 1:
        ch_fin += 1
    x = 0.5*((ch_fin-ch_ini)*x+ch_ini+ch_fin)
    y = func(coefficients, x, peak_center)
    inte = np.sum(w*y)*(ch_fin-ch_ini)/2
    return inte
def single_fun(COEF, CH, CENTROID):
    """
    COEF es un vector que contiene los valores de las constantes a ajustar.
    Al ser singlet, no se ajustará el centroide del pico.
        COEF[0] : Corresponderá a la altura del pico, como valor inicial de ajuste
                  se usará el valor de contaje del pico menos el del promedio de
                  los fondoss iniciales y finales de la ROI
        COEF[1] : Corresponderá al valor de sigma calculado a partir
                  del FWHM procedente del archivo de calibración
        COEF[2] : Corresponde al parámetro de cola, el cual se asumirá equivalente
                  a 0.1 veces el FWHM
    """
    curv = COEF[0]*np.exp(-((CH-CENTROID)**2)/(2*COEF[1]**2))\
        *np.heaviside(CH-CENTROID+COEF[2], 0.5) +COEF[0]\
            *np.exp(COEF[2]*(2*CH-2*CENTROID+COEF[2])/(2*COEF[1]**2))\
                *np.heaviside(CENTROID-COEF[2]-CH, 0.5)
    return curv
def single_fun_res(COEF, CH, COUNTS, PCENT, BG, WBG):
    # curv = COEF[0]*np.exp(-((CH-PCENT)**2)/(2*COEF[1]**2))\
    #     *np.heaviside(CH-PCENT+COEF[2], 1) +COEF[0]\
    #         *np.exp(COEF[2]*(2*CH-2*PCENT+COEF[2])/(2*COEF[1]**2))\
    #             *np.heaviside(PCENT-COEF[2]-CH, 0) + BG
    curv_s = BG+single_fun(COEF, CH, PCENT)
    return (COUNTS-curv_s)**2/WBG
def multiplet_fun(COEF, CH, dummy = None):
    """
    COEF es un vector que contiene los valores de las constantes a ajustar.
    Al ser singlet, no se ajustará el centroide del pico.
        COEF[0] : Corresponderá a la altura del pico, como valor inicial de ajuste
                  se usará el valor de contaje del pico menos el del promedio de
                  los fondoss iniciales y finales de la ROI
        COEF[1] : Corresponderá al valor de sigma calculado a partir
                  del FWHM procedente del archivo de calibración
        COEF[2] : Corresponde al parámetro de cola, el cual se asumirá equivalente
                  a 0.1 veces el FWHM
        COEF[3] : Corresponde al centroide del pico, se asume como valor inicial el
                  obntenido de la rutina peak_search
    """
    curv = COEF[0]*np.exp(-((CH-COEF[3])**2)/(2*COEF[1]**2))\
        *np.heaviside(CH-COEF[3]+COEF[2], 0.5)\
            +COEF[0]*np.exp(COEF[2]*(2*CH-2*COEF[3]+COEF[2])/(2*COEF[1]**2))\
                *np.heaviside(COEF[3]-COEF[2]-CH, 0.5)
    return curv

def multiplet_fun_res(COEF, n_mul, CH, COUNTS, BG, WBG):
    curv_m = 0
    for i in range(n_mul):
        curv_m += multiplet_fun(COEF[4*i:4*i+4], CH)
    return (COUNTS-curv_m-BG)**2*WBG

def peak_analysis(SPEC, FWHMC, BGSTEP=True, PLOT=False):
    FITEO = {'x':0}
    BG=0
    PCHANN = np.append(SPEC.peaks.T[0], 4096)
    PSIGNIF = SPEC.peaks.T[1]
    NPEAKS = len(PCHANN)
    CHANT = 0
    multiplet = None
    PD = SPEC.der_1
    Bkg_Tot = SPEC.counts*1
    Peaks_Indiv = []
    Peaks_Multi = []
    Peak_Fit_Data = []
    n_peak = 1
    for i in range(NPEAKS-1):
        fw = FWHMC[int(round(PCHANN[i]))-1]
        signi = PSIGNIF[i]
        single_tol = 4
        PCENT = PCHANN[i]
        if PCHANN[i+1]-PCENT > single_tol*fw and PCENT-CHANT > single_tol*fw:
            COEF = np.zeros(4)
            roi = 1.3
            fond = 5
            ROI = [10,10]
            if signi < 35:
                roi = 0.5
                fond = 7
            roi_tol = 4.5-roi
            p_f = int(np.floor(PCENT-roi*fw))
            n_it = 0
            while  np.mean(ROI) > 2 and ROI[0]*ROI[1] > 0:   # std_p = 100  and std_p > 3
                p_f -= 1
                ROI = PD[p_f-fond:p_f]
                n_it += 1
                if n_it > roi_tol*fw:
                    break
            li = p_f-fond                         # li = int(np.floor(PCENT-roi*fw)-fond)
            p_i = int(np.ceil(PCENT+roi*fw))
            n_it = 0
            ROI = [-10,-10]
            while  -np.mean(ROI) > 7 and ROI[-1]*ROI[-2] > 0:
                p_i += 1
                ROI = PD[p_i:p_i+fond]
                n_it += 1
                if n_it > roi_tol*fw:
                    break
            ls = p_i+fond+2                       # ls = int(np.ceil(PCENT+roi*fw)+fond)
            CHROI = np.arange(li, ls+1)
            ROI = SPEC.counts[li-1:ls]
            lroi = len(ROI)
            BGL = ROI*1  #BackGround Lineal
            WBGL = ROI*1
            BGS = ROI*1  #Background Step
            WBGS = ROI*1
            b1 = ROI[fond]*1.0
            b2 = ROI[lroi-fond]*1.0
            PSUM = ROI[fond]
            for j in range(fond, lroi-fond):
                BGL[j] = b1+(b2-b1)*(CHROI[j]-CHROI[fond])/(lroi-2*fond+1)
                BGS[j] = b1+(b2-b1)/np.sum(ROI[fond: lroi-fond])*PSUM*1.0
                PSUM += ROI[j+1]
            PSUM = 0
            for j in range(lroi):
                PSUM += ROI[j]
                WBGL[j] = ROI[j]+(b1*(lroi-2*fond+1-CHROI[j]+CHROI[fond])**2  \
                                  +b2*(CHROI[j]-CHROI[fond])**2)/(fond*(lroi-2*fond+1)**2)
                WBGS[j] = ROI[j]+(b1*(np.sum(ROI)-PSUM)**2+b2*np.sum(ROI)**2  \
                                  +(b2-b1)**2*PSUM*fond)/(fond*np.sum(ROI)**2)
            if BGSTEP:
                BG = BGS
                WBG = WBGS
            else:
                BG = BGL
                WBG = BGL
            COEF[0] = SPEC.counts[int(round(PCENT))-1]-BG[np.where(CHROI == round(PCENT))[0][0]]
            COEF[1] = FWHMC[int(round(PCENT))-1]/np.sqrt(8*np.log(2))
            COEF[2] = 0.5*FWHMC[int(round(PCENT))-1]
            COEF[3] = PCENT
            FITEO = least_squares(single_fun_res, COEF[:3], args=(CHROI, ROI, PCENT, BG, WBG))
            COEF[:3] = FITEO['x']
            NPA = integrate(single_fun, COEF, CHROI[0], CHROI[-1], PCENT)
            # CURVA FITEADA
            curv_fit = single_fun(COEF, CHROI, PCENT)
            FITEO['x'] = COEF
            # Almacenamiento de las curvas
            Bkg_Tot[li-1:ls] = BG
            p_ind = [[CHROI, curv_fit+BG]]
            Peaks_Indiv += p_ind
            Peak_Fit_Data += [Peak(n_peak, FITEO, CHROI, curv_fit, BG, NPA)] ;n_peak += 1
        else:
            multi = np.array([[PCENT, signi]])
            multiplet = np.concatenate((multiplet, multi))\
                if multiplet is not None else multi 
            if PCHANN[i+1]-PCENT > single_tol*fw:
                # print(multiplet)
                n_multi = len(multiplet.T[0])
                COEF = np.zeros(4*n_multi)
                roi = 1
                fond = 5
                ROI = [10,10]
                if multiplet[0][1] < 35:
                    roi = 0.5
                roi_tol = 4-roi
                p_f = int(np.floor(multiplet[0][0]-roi*fw))
                n_it = 0
                while  np.mean(ROI) > 2 and ROI[0]*ROI[1] > 0:
                    p_f -= 1
                    ROI = PD[p_f-fond:p_f]
                    n_it += 1
                    if n_it > roi_tol*fw:
                        break
                li = p_f-fond                         # li = int(np.floor(PCENT-roi*fw)-fond)
                roi = 1.2
                if multiplet[-1][1] < 35:
                    roi = 0.5
                roi_tol = 4-roi
                p_i = int(np.ceil(multiplet[-1][0]+roi*fw))
                n_it = 0
                ROI = [-10,-10]
                while  -np.mean(ROI) > 7 and ROI[-1]*ROI[-2] > 0:
                    p_i += 1
                    ROI = PD[p_i:p_i+fond]
                    n_it += 1
                    if n_it > roi_tol*fw:
                        break
                ls = p_i+2*fond
                CHROI = np.arange(li, ls+1)
                ROI = SPEC.counts[li-1:ls]
                lroi = len(ROI)
                BGL = ROI*1  #BackGround Lineal
                WBGL = ROI*1
                BGS = ROI*1  #Background Step
                WBGS = ROI*1
                b1 = ROI[fond]*1.0
                b2 = ROI[lroi-fond]*1.0
                PSUM = ROI[fond]
                for j in range(fond, lroi-fond):
                    BGL[j] = b1+(b2-b1)*(CHROI[j]-CHROI[fond])/(lroi-2*fond+1)
                    BGS[j] = b1+(b2-b1)/np.sum(ROI[fond: lroi-fond])*PSUM
                    PSUM += ROI[j+1]
                PSUM = 0
                for j in range(lroi):
                    PSUM += ROI[j]
                    WBGL[j] = ROI[j]+(b1*(lroi-2*fond+1-CHROI[j]+CHROI[fond])**2  \
                                      +b2*(CHROI[j]-CHROI[fond])**2)/(fond*(lroi-2*fond+1)**2)
                    WBGS[j] = ROI[j]+(b1*(np.sum(ROI)-PSUM)**2+b2*np.sum(ROI)**2  \
                                      +(b2-b1)**2*PSUM*fond)/(fond*np.sum(ROI)**2)
                if BGSTEP:
                    BG = BGS
                    WBG = WBGS
                else:
                    BG = BGL
                    WBG = BGL
                for k,j in enumerate(multiplet.T[0]):
                    COEF[4*k] = SPEC.counts[ int(round(j))-1 ] - BG[np.where(CHROI == round(j))[0][0]]
                    COEF[1+4*k] = FWHMC[int(round(j))-1]/np.sqrt(8*np.log(2))
                    COEF[2+4*k] = 0.5*FWHMC[int(round(j))-1]
                    COEF[3+4*k] = j
                curv_unfit=0
                for i in range(n_multi):
                    curv_unfit += multiplet_fun(COEF[4*i:4*i+4], CHROI)
                FITEO = least_squares(multiplet_fun_res, COEF, args=(n_multi, CHROI, ROI, BG, WBG))
                COEF = FITEO['x']
                curv_fit = np.zeros(lroi)
                n_multip = 1
                for i in range(n_multi):
                    COEF2 = COEF[4*i:4*i+4]
                    curv_indiv = multiplet_fun(COEF2, CHROI)
                    curv_fit += curv_indiv
                    p_ind = [[CHROI, curv_indiv+BG]]
                    Peaks_Indiv += p_ind
                    FITEO2 = FITEO
                    FITEO2['x'] = COEF2
                    NPA = integrate(multiplet_fun, COEF2, CHROI[0], CHROI[-1]) 
                    Peak_Fit_Data += [Peak(n_peak, FITEO2, CHROI, curv_indiv,\
                                           BG,  NPA, n_multip, n_multi)]
                    n_peak += 1; n_multip += 1
                curv_fit = curv_fit
                Bkg_Tot[li-1:ls] = BG
                p_ind = [[CHROI, curv_fit+BG]]
                Peaks_Multi += p_ind
                multiplet = None
        CHANT = PCHANN[i]
    chann = np.arange(1,4097)
    if PLOT:
        plt.scatter(chann, SPEC.counts, marker='.', c='y',linewidth = 0.5)    
        plt.plot(chann, Bkg_Tot, 'c' , linewidth=0.5)
        Peaks_Indiv = np.array(Peaks_Indiv)
        for i,j in Peaks_Indiv:
            plt.plot(i, j, 'r')
        Peaks_Multi = np.array(Peaks_Multi)
        for i,j in Peaks_Multi:
            plt.plot(i, j, 'b')
        plt.yscale('log')
        plt.grid()  
    for i in Peak_Fit_Data:
        i.roi_ener = np.polyval(SPEC.en_coef, i.roi_ch)
        i.cen_ener = np.polyval(SPEC.en_coef, i.cen_ch)
    return Peak_Fit_Data, Bkg_Tot
#%%
if __name__ == "__main__":
    FILENAME = 'eu3'
    signif = 50
    c = read_cnf_file('files/'+FILENAME+'.cnf', False)
    """Desglose de información guardada en archivo CNF"""
    # counts = c.counts
    enercal = c.en_coef
    # fwhme = c.fwhm #En Kev
    fwhmc = c.fwhm/c.en_coef[2] #En canales
    channels = c.channels 
    c.peaks, c.der_2, c.der_1 = peak_search(c.counts, fwhmc, signif, enercal)  # 10 a 12 channel
    c.peaks = np.array(c.peaks)
    c.peak_dat, c.bkg = peak_analysis(c, fwhmc, PLOT=True)
    