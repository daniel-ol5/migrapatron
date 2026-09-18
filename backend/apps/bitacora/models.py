"""
Módulo M1 - captura estructurada.

Tablas que van aquí (HU-01, ver docs/diagramas/02_modelo_datos.puml):

    catalogo_factor        Metadatos de los 11 factores: qué columna es cada
                           uno, tipo, unidad, rango y si admite ventana de lag.
    regla_discretizacion   Cortes de cada factor + la frase en español que usa
                           el explicador (descripcion_humana).
    registro_diario        Un día de bitácora. UQ(usuario_id, fecha) -- RN-05.
    alimento               Catálogo de disparadores alimentarios.
    registro_alimento      N:M entre registro_diario y alimento.
    episodio_migrana       El episodio: EVA 1-10, aura, localización, alivio.
    sintoma                Catálogo de síntomas.
    episodio_sintoma       N:M entre episodio_migrana y sintoma.

La decisión de diseño clave: registro_diario tiene COLUMNAS FIJAS (simples de
validar y de consumir desde los clientes), y catalogo_factor guarda los
METADATOS que el motor recorre para saber qué columna leer y cómo
discretizarla. Agregar un factor nuevo es insertar filas, no reescribir el
algoritmo.
"""
