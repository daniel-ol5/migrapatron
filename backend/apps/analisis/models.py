"""
Módulos M2 y M3 - análisis, hallazgos y reporte.

Tablas que van aquí (HU-01, ver docs/diagramas/02_modelo_datos.puml):

    analisis             Una corrida del motor: periodo, lag, versión, los
                         parámetros usados y el estado
                         (OK / DATOS_INSUFICIENTES / ERROR).
    hallazgo             Cada patrón encontrado, con soporte, confianza, lift,
                         p-valor, episodios relacionados y su explicación.
    valoracion_hallazgo  El paciente marca si le resultó útil (CU-11).
    riesgo_diario        Semáforo del día. UPSERT por (usuario, fecha).
    reporte_clinico      El resumen para la consulta (CU-13).
    evento_auditoria     Rastro de accesos a datos clínicos (RNF-06).

`hallazgo` cuelga de `analisis`, no del usuario: un hallazgo solo significa
algo en el contexto de la corrida que lo produjo (periodo, umbrales, versión
del motor). Los hallazgos no se editan nunca, se regeneran -- RN-06.
"""
