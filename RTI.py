import pandas as pd
import numpy as np


RTI = pd.read_excel("CM_-_Riesgo_de_tasas_diciembre_19.xlsx")
RTI['fc_periodo'] = pd.to_datetime(RTI['fc_periodo'])
RTI = RTI[(RTI['cd_cons'] == 0) | (RTI['cd_cons'] == 1)]

FF_pesos = RTI[(RTI['fc_periodo'] == "2019-12-31") & (RTI['cd_partida'] == 50100) & 
                (RTI['cd_mar_com'] == 2) & (RTI['cd_banda'] > 0)]
FF_pesos = FF_pesos.sort_values(by=['cd_entidad', 'cd_escenario', 'cd_banda'])


pto_medio = np.array([0.0028,0.0417,0.1667,0.375,0.625,0.875,1.25,1.75,2.5,3.5,
                       4.5,5.5,6.5,7.5,8.5,9.5,12.5,17.5,25])
curva_pesos = np.array([38.83,39.78,42.25,44.72,45.69,45.23,43.01,38.83,32.35,25.34,
                         20.35,16.83,14.29,12.40,10.94,9.79,7.44,6.32,3.72])
curvas_rendimientos_pesos = pd.DataFrame({
    "Pto_medio_bandas_temporales": pto_medio,
    "curva_rend_pesos": curva_pesos
})


shock_paralelo_pesos = 400 / 100
shock_corto_plazo_pesos = 500 / 100
shock_largo_plazo_pesos = 300 / 100

def calcular_curvas(curva_base, pto_medio):
    curva_paralelo_pos = curva_base + shock_paralelo_pesos
    curva_paralelo_neg = curva_base - shock_paralelo_pesos
    curva_pend_empinada = curva_base + (-0.65 * np.abs(shock_corto_plazo_pesos * np.exp(-pto_medio / 4)) +
                                         0.9 * np.abs(shock_largo_plazo_pesos * (1 - np.exp(-pto_medio / 4))))
    curva_pend_aplanada = curva_base + (0.8 * np.abs(shock_corto_plazo_pesos * np.exp(-pto_medio / 4)) -
                                         0.6 * np.abs(shock_largo_plazo_pesos * (1 - np.exp(-pto_medio / 4))))
    curva_subida = curva_base + shock_corto_plazo_pesos * np.exp(-pto_medio / 4)
    curva_bajada = curva_base - shock_corto_plazo_pesos * np.exp(-pto_medio / 4)
    
    return pd.DataFrame({
        "curva_paralelo_pos": curva_paralelo_pos,
        "curva_paralelo_neg": curva_paralelo_neg,
        "curva_pend_empinada": curva_pend_empinada,
        "curva_pend_aplanada": curva_pend_aplanada,
        "curva_subida": curva_subida,
        "curva_bajada": curva_bajada
    })

curvas_extra = calcular_curvas(curvas_rendimientos_pesos['curva_rend_pesos'], curvas_rendimientos_pesos['Pto_medio_bandas_temporales'])
curvas_rendimientos_pesos = pd.concat([curvas_rendimientos_pesos, curvas_extra], axis=1)

def calcular_factor_descuento(curvas, pto_medio):
    return np.exp(-curvas / 100 * pto_medio[:, np.newaxis])

descuentos = calcular_factor_descuento(curvas_rendimientos_pesos.iloc[:, 1:], curvas_rendimientos_pesos['Pto_medio_bandas_temporales'].values)
Factor_descuento = pd.DataFrame(descuentos, columns=["factor_descuento_0", "factor_descuento_1", "factor_descuento_2", "factor_descuento_3", "factor_descuento_4", "factor_descuento_5", "factor_descuento_6"])


FF_pesos['f_descuento'] = FF_pesos.apply(lambda row: Factor_descuento.iloc[int(row['cd_banda']) - 1, int(row['cd_escenario'])], axis=1)
FF_pesos['EVE'] = FF_pesos['nu_importe'] * FF_pesos['f_descuento']


Base_EVE = FF_pesos.groupby(['cd_entidad', 'cd_escenario'])['EVE'].sum().unstack().reset_index()
Base_EVE.columns = ["Entidad", "Escenario_Base", "Escenario_1", "Escenario_2", "Escenario_3", "Escenario_4", "Escenario_5", "Escenario_6"]


variaciones = Base_EVE.iloc[:, 1:].apply(lambda col: Base_EVE['Escenario_Base'] - col)
variaciones.columns = ["Var_EVE_pesos_" + str(i) for i in range(1, 7)]
Var_EVE_pesos = pd.concat([Base_EVE[['Entidad']], variaciones], axis=1)
Var_EVE_pesos.iloc[:, 1:] = Var_EVE_pesos.iloc[:, 1:].applymap(lambda x: max(x, 0))


display(Var_EVE_pesos)
