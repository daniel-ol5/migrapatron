/**
 * Configuración de la aplicación web.
 *
 * Vite solo expone al navegador las variables que empiezan con VITE_.
 * El valor por defecto apunta al backend local: ver web/.env.example
 */
export const API_URL: string =
  import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000/api';

/** Días que analiza el motor por defecto (CU-08). */
export const PERIODO_ANALISIS_DIAS = 90;

/** Ventana de retraso por defecto: el día D se compara con el día D-1. */
export const LAG_DIAS = 1;

/** Reglas de suficiencia de datos (RN-02). Se usan solo para avisar al usuario;
 *  la validación real la hace el backend. */
export const MINIMO_DIAS = 14;
export const MINIMO_EPISODIOS = 3;

/** RNF-07: esta leyenda acompaña siempre a los hallazgos. */
export const AVISO_NO_CAUSALIDAD =
  'Una asociación no demuestra causalidad. Comenta estos resultados con tu médico.';
