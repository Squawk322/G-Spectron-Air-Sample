'''Modulo para busqueda de picos automatica de un espectro gamma'''
import numpy as np
import matplotlib.pyplot as plt
from readfile import *
from scipy.optimize import least_squares
#%%
def c_i(FW, niv=2):
    '''Función para calcular los coeficientes para la \
        |Segunda Derivada generalizada'''
    SIG = FW/2.355
    CIS = np.array([0])
    i = 1
    if niv == 2:
        CIS[0] = -100.0
        test = lambda i, SIG: 100*(i*i-SIG*SIG)*np.exp(-i*i/2/SIG/SIG)/(SIG*SIG)
        TEST = test(i,SIG)
        while True:
            CIS = np.append(CIS, TEST)
            i += 1
            TEST = test(i,SIG)
            if np.absolute(TEST) < 1 and i > SIG+1:
                break
        return np.append(np.flip(CIS)[:len(CIS)-1], CIS)
    elif niv == 1:
        SIG = 1*SIG
        # test = lambda i, SIG: -(i)*np.exp(-i*i/2/SIG/SIG)/SIG
        test = lambda i, SIG: -np.exp(-i*i/2/SIG/SIG)
        CIS[0] = 0
        TEST = test(i,SIG)
        while True:
            CIS = np.append(CIS, TEST)
            i += 1
            TEST = test(i,SIG)
            if np.absolute(TEST) < 0.1:
                break
        return np.append(-np.flip(CIS)[:len(CIS)-1], CIS)
    else:
        return None

#%%
def convolu(COUNTS, FWHMC, CHANNELS, niv=2):
    NSTEP = CHANNELS//64
    loop = np.array([np.arange(NSTEP), np.arange(1, NSTEP+1)]).T*64
    DD = np.empty(0)
    SD = np.empty(0)
    ST = (len(c_i(np.mean(FWHMC[0:64]), niv))-1)//2
    EN = (len(c_i(np.mean(FWHMC[CHANNELS-64:CHANNELS]), niv))-1)//2
    COUNTS2 = np.append(np.zeros(ST), COUNTS)
    COUNTS2 = np.append(COUNTS2, np.zeros(EN))
    for i, j in loop:
        # Coeficientes para la Segunda Derivada
        cij = c_i(np.mean(FWHMC[i:j]), niv)  #Coef dependientes de FWHM promedio cada 64 canales
        l = (len(cij)-1)//2
        # Ubicacion del array convolucionado
        COU = COUNTS2[i+ST-l:j+l+ST]
        ai = 2*l
        bi = ai+64
        # Calculo de la Segunda derivada generalizada y su Desviación Estándar
        DD = np.append(DD, np.convolve(COU, cij)[ai:bi])
        SD = np.append(SD, np.sqrt(np.convolve(COU, cij*cij))[ai:bi])
    SD[SD == 0] = 1
    # Calculo de la función para evaluar significancia
    SS = DD/SD
    SS[0:ST] = 0
    SS[CHANNELS-EN:CHANNELS] = 0
    return SS

def peak_search(COUNTS, FWHMC, SIGNIFICANCE, encal, CHANNELS=4096, PLOT=False, ch_ini=120, ch_end=4096):

    SS = convolu(COUNTS, FWHMC, CHANNELS)
    PP = convolu(COUNTS, FWHMC, CHANNELS, niv=1)
    PEAKFOUND = []
    ISSUM = 0
    SSUM = 0
    VA = 0
    PEND = 0
    PENDAN = 0
    k = 0
    iant = 0
    for i, j in enumerate(SS):
        PEND = j-VA
        if j < 0:
            if VA >= 0:
                print(i,j)
                CI = i
            ISSUM += (i+1)*j
            SSUM += j
            if PEND*PENDAN < 0:
                UBIC = np.array([[i-1, VA]])  #posicion del Canal, Signif
                if (i-iant) > 3:
                    k += 1
                    if k == 1:
                        DOB = UBIC
                    else: # elif NP-np.floor(NP)==0:
                        DOB = np.concatenate((DOB, UBIC))
                else:
                    k -= 1
                    DOB = DOB[:-1]
                iant = i
        if VA < 0 <= j:
            if k == 1:
                PCENTR = ISSUM/SSUM
                PSIGNIF = -DOB[0][1]
                if PSIGNIF >= SIGNIFICANCE and ch_ini <= PCENTR <= ch_end:
                    PEAK = [[PCENTR, np.polyval(encal, PCENTR), PSIGNIF]]
                    PEAKFOUND += PEAK
            else:
                NP = (k+1)//2
                for l in range(NP):
                    ISSUM = 0
                    SSUM = 0
                    if 2*l == 0:
                        LI = CI
                    else:
                        LI = DOB[2*l-1][0]
                    if 2*l+1 >= k:
                        LS = i-1
                    else:
                        LS = DOB[2*l+1][0]
                    for m in range(int(LI), int(LS+1)):
                        SSUM += SS[m]
                        ISSUM += (m+1)*SS[m]
                    PCENTR = ISSUM/SSUM
                    PSIGNIF = -DOB[2*l][1]
                    if PSIGNIF >= SIGNIFICANCE and ch_ini <= PCENTR <= ch_end:
                        PEAK = [[PCENTR, np.polyval(encal, PCENTR), PSIGNIF]]
                        PEAKFOUND += PEAK
            ISSUM = 0
            SSUM = 0
            k = 0
        PENDAN = PEND
        VA = j #Valor anterior
    
    if PLOT:
        for i in range(8):
            ste = CHANNELS//8
            plt.plot(np.arange(i*ste, (i+1)*ste), SS[i*ste:(i+1)*ste])
            plt.grid()
            plt.show()
            plt.plot(np.arange(i*ste, (i+1)*ste), COUNTS[i*ste:(i+1)*ste])
            plt.grid()
            plt.show()
    return PEAKFOUND, SS, PP
# def ener_fit(Peaks, Energy, Orden=2):
#     coe = np.zeros(4)
#     if Orden == 1:
#         return least_squares(lambda co,ch,en:en-(co[0]+co[1]*ch),\
#                             coe, args=(Peaks, Energy) ).x
#     elif Orden == 2:
#         return least_squares(lambda co,ch,en:en-(co[0]+co[1]*ch+co[2]*ch*ch),\
#                             coe, args=(Peaks, Energy) ).x
#     elif Orden == 3:
#         return least_squares(lambda co,ch,en:en-(co[0]+co[1]*ch+co[2]*ch*ch+\
#                                                   co[3]*ch*ch*ch), coe,\
#                               args=(Peaks, Energy) ).x
#     else: 
#         return coe
    # if Orden > 3:
    #     return np.zeros(4)
    # else:
    #     return np.polyfit(Peaks, Energy, Orden)
# def ener_from_ch(en_coef, ch):
    # return en_coef[0] + en_coef[1]*ch + en_coef[2]*ch*ch + en_coef[3]*ch*ch*ch
#%%
if __name__ == "__main__":
    FILENAME = 'cs137'
    signif = 30
    c = read_cnf_file('files/'+FILENAME+'.cnf', False, False)
    """Desglose de información guardada en archivo CNF"""
    counts = c.counts
    enercal = c.en_coef
    fwhme = c.fwhm #En Kev
    fwhmc = fwhme/enercal[2] #En canales
    c.peaks, c.der_2, c.der_1 = peak_search(counts, fwhmc, signif, enercal)
    # plt.plot(counts)
    # plt.plot(10*peaks[2])
    # plt.plot(10*peaks[1])
    # plt.grid()
    
    # ener_act = np.array([121.782, 244.697, 344.279, 411.117, 443.961,\
    #                      778.905, 964.057, 1085.837, 1112.076, 1408.013])
    # enercal2 = ener_fit(cal, ener_act)
    # enin2 = ener_from_ch(enercal2, cal)
    
    
    ## c.peaks = np.array(c.peaks)
    ## cal = c.peaks.T[0]
    ## enin = np.polyval(enercal, cal)   
    ## cal2 = np.append(cal[:7],cal[-1])
    ## ener_act = np.array([121.782, 244.697, 344.279, 411.117, 443.961,\
    ##                      778.905, 964.057, 1408.013])
    ## enercal3 = np.polyfit(cal2, ener_act,2)
    ## enin3 = np.polyval(enercal3, cal2)
                    
        
        
        
# 121.782	28.530
# 244.697	7.550
# 344.279	26.590
# 411.117	2.237
# 443.961	2.827
# 778.905	12.930
# 867.380	4.230
# 964.057	14.510
# 1085.837	10.110
# 1089.737	1.734
# 1112.076	13.670
# 1299.142	1.633
# 1408.013	20.870
    
#     -0.73441
# 0.749427
# -1.13291e-07
# 8.40663e-10
    
#     -0.300248
# 0.747303
# 2.45237e-06
# 0

