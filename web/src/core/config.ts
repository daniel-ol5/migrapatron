/**
 * Configuración del cliente web.
 *
 * Vite solo expone al navegador las variables que empiezan con VITE_.
 * El valor por defecto apunta al backend local: ver web/.env.example
 */
export const API_URL: string =
  import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000/api';

/** Días que analiza el motor por defecto (M2). */
export const PERIODO_ANALISIS_DIAS = 90;

/**
 * M2.2. Ventana temporal: cuánto hacia atrás se buscan factores previos a un
 * episodio, contando desde la hora de corte de cada bitácora.
 */
export const VENTANA_HORAS = 48;

/**
 * M2.1. Criterios mínimos de evidencia antes de analizar.
 *
 * Se replican aquí solo para mostrarle al paciente cuánto le falta. La
 * validación que decide es la del backend: si estos valores se desincronizan,
 * manda el servidor.
 */
export const MINIMO_BITACORAS = 20;
export const MINIMO_EPISODIOS = 3;

/** Esta leyenda acompaña siempre a los hallazgos y a los reportes. */
export const AVISO_NO_CAUSALIDAD =
  'Una asociación no demuestra causalidad. Comenta estos resultados con tu médico.';
