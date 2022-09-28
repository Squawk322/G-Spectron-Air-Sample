'''Modulo para busqueda de picos automatica de un espectro gamma'''
import numpy as np
import matplotlib.pyplot as plt
# from readfile import *
from scipy.optimize import least_squares
#%%
def c_i(fwhm, niv=2):
    '''Función para calcular los coeficientes para la \
        Segunda Derivada generalizada'''
    sig = fwhm/2.355
    cis = np.array([0])
    i = 1
    if niv == 2:
        cis[0] = -100.0
        test = lambda i, sig: 100 * (i*i - sig*sig) * \
            np.exp(-i*i / 2 / sig / sig) / (sig*sig)
        test_results = test(i,sig)
        while True:
            cis = np.append(cis, test_results)
            i += 1
            test_results = test(i,sig)
            if np.absolute(test_results) < 1 and i > sig+1:
                break
        return np.append(np.flip(cis)[:len(cis)-1], cis)
    elif niv == 1:
        sig = 1*sig
        # test = lambda i, sig: -(i)*np.exp(-i*i/2/sig/sig)/sig
        test = lambda i, sig: -np.exp(-i*i/2/sig/sig)
        cis[0] = 0
        test_results = test(i,sig)
        while True:
            cis = np.append(cis, test_results)
            i += 1
            test_results = test(i,sig)
            if np.absolute(test_results) < 0.1:
                break
        return np.append(-np.flip(cis)[:len(cis)-1], cis)
    else:
        return None

#%%
def convolu(counts, fwhmc, channels, niv=2):
    n_step = channels//64
    loop = np.array([np.arange(n_step), np.arange(1, n_step+1)]).T*64
    dd = np.empty(0)
    std_dev = np.empty(0)
    start_ch = (len(c_i(np.mean(fwhmc[0:64]), niv)) - 1) // 2
    end_ch = (len(c_i(np.mean(fwhmc[channels - 64:channels]), niv)) - 1) // 2
    counts_2 = np.append(np.zeros(start_ch), counts)
    counts_2 = np.append(counts_2, np.zeros(end_ch))
    for i, j in loop:
        # Coeficientes para la Primera/Segunda Derivada de acuerdo a niv
        # Coef dependientes de FWHM promedio cada 64 canales
        cij = c_i(np.mean(fwhmc[i:j]), niv)  
        l = (len(cij) - 1) // 2
        # Ubicacion del array convolucionado
        COU = counts_2[i + start_ch - l : j + l + start_ch]
        ai = 2*l
        bi = ai + 64
        # Calculo de la Segunda derivada generalizada y su Desviación Estándar
        dd = np.append(dd, np.convolve(COU, cij)[ai:bi])
        std_dev = np.append(std_dev, np.sqrt(np.convolve(COU, cij*cij))[ai:bi])
    std_dev[std_dev == 0] = 1
    # Calculo de la función para evaluar significancia
    ss = dd/std_dev
    ss[0:start_ch] = 0
    ss[channels - end_ch:channels] = 0
    return ss

def peak_search(counts, fwhmc, signif, encal, channels=4096, \
                plot_q=False, ch_ini=120, ch_end=4096):
    ss = convolu(counts, fwhmc, channels)
    pp = convolu(counts, fwhmc, channels, niv=1)
    pks_found = []
    is_sum = 0
    s_sum = 0
    v_a = 0
    pend = 0
    pend_ant = 0
    k = 0
    iant = 0
    for i, j in enumerate(ss):
        pend = j - v_a
        if j < 0:
            if v_a >= 0:
                ch_i = i
            is_sum += (i+1)*j
            s_sum += j
            if 400<i+1<900:
                print(i+1)
            if pend*pend_ant <= 0:
                ubic = np.array([[i-1, v_a]])  #posicion del Canal, Signif
                if (i-iant) > 3:
                    k += 1
                    if k == 1:
                        dob = ubic
                    else: # elif n_p-np.floor(n_p)==0:
                        dob = np.concatenate((dob, ubic))
                else:
                    k -= 1
                    dob = dob[:-1]
                iant = i
        if v_a < 0 <= j:
            if k == 1:
                pk_center = is_sum/s_sum
                if 600<pk_center<900:
                    print(pk_center)
                pk_signif = -dob[0][1]
                if pk_signif >= signif and ch_ini <= pk_center <= ch_end:
                    peak = [[
                        pk_center,
                        np.polyval(encal, pk_center),
                        pk_signif
                    ]]
                    pks_found += peak
            else:
                n_p = (k+1)//2
                for l in range(n_p):
                    is_sum = 0
                    s_sum = 0
                    if 2*l == 0:
                        l_i = ch_i
                    else:
                        l_i = dob[2*l-1][0]
                    if 2*l+1 >= k:
                        LS = i-1
                    else:
                        LS = dob[2*l+1][0]
                    for m in range(int(l_i), int(LS+1)):
                        s_sum += ss[m]
                        is_sum += (m+1)*ss[m]
                    pk_center = is_sum/s_sum
                    # TODO! : AQUI
                    if 600<pk_center<900:
                        print(pk_center)
                    pk_signif = -dob[2*l][1]
                    if pk_signif >= signif and ch_ini <= pk_center <= ch_end:
                        peak = [[
                            pk_center,
                            np.polyval(encal,pk_center),
                            pk_signif
                        ]]
                        pks_found += peak
            is_sum = 0
            s_sum = 0
            k = 0
        pend_ant = pend
        v_a = j #Valor anterior
    
    if plot_q:
        for i in range(8):
            ste = channels//8
            plt.plot(np.arange(i*ste, (i+1)*ste), ss[i*ste:(i+1)*ste])
            plt.grid()
            plt.show()
            plt.plot(np.arange(i*ste, (i+1)*ste), counts[i*ste:(i+1)*ste])
            plt.grid()
            plt.show()
    return pks_found, ss, pp

#%%
if __name__ == "__main__":
    from readfile import read_cnf_file
    FILENAME = 'eu152'
    signif = 80
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
    c.peaks = np.array(c.peaks)
    cal = c.peaks.T[0]
    enin = np.polyval(enercal, cal)
    # ener_act = np.array([121.782, 244.697, 344.279, 411.117, 443.961,\
    #                      778.905, 964.057, 1085.837, 1112.076, 1408.013])
    # enercal2 = ener_fit(cal, ener_act)
    # enin2 = ener_from_ch(enercal2, cal)   
    cal2 = np.append(cal[:7],cal[-1])
    ener_act = np.array([121.782, 244.697, 344.279, 411.117, 443.961,\
                         778.905, 964.057, 1408.013])
    enercal3 = np.polyfit(cal2, ener_act,2)
    enin3 = np.polyval(enercal3, cal2)
                    
        
        
        
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

