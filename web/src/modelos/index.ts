/**
 * Tipos del dominio, espejo de los serializadores del backend.
 *
 * Referencia: backend/apps/m0_usuarios/serializers.py
 *             backend/apps/m1_bitacora/serializers.py
 */

/**
 * Convierte a número lo que el backend envía como texto.
 *
 * DecimalField de DRF se serializa como string ("6.50"), no como número. Sin
 * esta conversión cada campo decimal llega como texto y las comparaciones
 * fallan en silencio.
 */
export function aNumero(valor: unknown): number | null {
  if (valor === null || valor === undefined || valor === '') return null;
  const n = typeof valor === 'number' ? valor : Number(valor);
  return Number.isFinite(n) ? n : null;
}

/** Una fecha en el formato que espera el backend: AAAA-MM-DD. */
export function comoFecha(d: Date): string {
  const mes = `${d.getMonth() + 1}`.padStart(2, '0');
  const dia = `${d.getDate()}`.padStart(2, '0');
  return `${d.getFullYear()}-${mes}-${dia}`;
}

/** Respuesta paginada de DRF. */
export interface Pagina<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// ================================================================== M0
export type TipoMigrana =
  | 'CON_AURA'
  | 'SIN_AURA'
  | 'CRONICA'
  | 'DESCONOCIDA';

export const ETIQUETAS_TIPO: Record<TipoMigrana, string> = {
  CON_AURA: 'Con aura',
  SIN_AURA: 'Sin aura',
  CRONICA: 'Crónica',
  DESCONOCIDA: 'Desconocida',
};

export interface PerfilClinico {
  anios_con_migrana: number | null;
  diagnostico_previo: boolean;
  tipo_migrana: TipoMigrana;
  medicacion_habitual: string;
  registra_ciclo_menstrual: boolean;
  /** Hora a la que el paciente cierra su bitácora, formato HH:MM:SS. */
  hora_corte_preferida: string;
  actualizado_en?: string;
}

export interface Usuario {
  id: number;
  email: string;
  nombre: string;
  apellido: string;
  nombre_completo: string;
  fecha_nacimiento: string | null;
  sexo: string;
  fecha_registro: string;
  /** Sin esto en true, M2 no ejecuta el análisis. */
  consintio_analisis: boolean;
  perfil: PerfilClinico;
}

export interface RespuestaSesion {
  access: string;
  refresh: string;
  usuario: Usuario;
}

export interface AvisoPrivacidad {
  version: string;
  titulo: string;
  contenido: string;
  vigente_desde: string;
}

/** Un hecho del historial de consentimiento. El historial es de solo adición. */
export interface HechoConsentimiento {
  id: number;
  aceptado: boolean;
  aviso_version: string;
  otorgado_en: string;
}

export interface EstadoConsentimiento {
  vigente: boolean;
  historial: HechoConsentimiento[];
}

// ================================================================== M1
export type Hidratacion = 'BAJA' | 'MEDIA' | 'ALTA' | '';

export const OPCIONES_HIDRATACION: { valor: Hidratacion; texto: string }[] = [
  { valor: 'BAJA', texto: 'Baja' },
  { valor: 'MEDIA', texto: 'Media' },
  { valor: 'ALTA', texto: 'Alta' },
];

export type ContextoMenstrual =
  | 'NO_APLICA'
  | 'MENSTRUACION'
  | 'FOLICULAR'
  | 'OVULACION'
  | 'LUTEA'
  | '';

export const OPCIONES_CICLO: { valor: ContextoMenstrual; texto: string }[] = [
  { valor: 'NO_APLICA', texto: 'No aplica' },
  { valor: 'MENSTRUACION', texto: 'Menstruación' },
  { valor: 'FOLICULAR', texto: 'Folicular' },
  { valor: 'OVULACION', texto: 'Ovulación' },
  { valor: 'LUTEA', texto: 'Lútea' },
];

export interface RegistroDiario {
  id: number | null;
  /** AAAA-MM-DD. Único por usuario y fecha. */
  fecha: string;
  /** HH:MM o HH:MM:SS. M2 la usa para la ventana temporal de 48 h. */
  hora_corte: string;
  horas_sueno: number | null;
  hidratacion: Hidratacion;
  comida_omitida: number | null;
  estres: number | null;
  horas_pantalla: number | null;
  minutos_actividad: number | null;
  cafeina_tazas: number | null;
  contexto_menstrual: ContextoMenstrual;
  medicacion_rescate: boolean;
  sensaciones_premonitorias: boolean;
  /** Solo los días completos cuentan para la suficiencia de datos de M2. */
  completado: boolean;
}

/** Los siete factores que el backend exige para marcar el día completo. */
export const FACTORES_REQUERIDOS = [
  'horas_sueno',
  'hidratacion',
  'comida_omitida',
  'estres',
  'horas_pantalla',
  'minutos_actividad',
  'cafeina_tazas',
] as const satisfies readonly (keyof RegistroDiario)[];

export const TOTAL_FACTORES = FACTORES_REQUERIDOS.length;

/**
 * Cuenta los factores llenos.
 *
 * Se replica la regla del backend para poder mostrar el avance mientras se
 * llena el formulario, sin esperar la respuesta del servidor. Si las dos
 * reglas se desincronizan, manda la del backend.
 */
export function factoresCompletos(r: RegistroDiario): number {
  return FACTORES_REQUERIDOS.filter((campo) => {
    const valor = r[campo];
    return valor !== null && valor !== undefined && valor !== '';
  }).length;
}

export function registroVacio(fecha: string, horaCorte = '22:00'): RegistroDiario {
  return {
    id: null,
    fecha,
    hora_corte: horaCorte,
    horas_sueno: null,
    hidratacion: '',
    comida_omitida: null,
    estres: null,
    horas_pantalla: null,
    minutos_actividad: null,
    cafeina_tazas: null,
    contexto_menstrual: '',
    medicacion_rescate: false,
    sensaciones_premonitorias: false,
    completado: false,
  };
}

/** Normaliza lo que llega del backend: los decimales vienen como texto. */
export function registroDesdeApi(json: Record<string, unknown>): RegistroDiario {
  return {
    id: (json.id as number) ?? null,
    fecha: json.fecha as string,
    hora_corte: ((json.hora_corte as string) ?? '22:00').slice(0, 5),
    horas_sueno: aNumero(json.horas_sueno),
    hidratacion: ((json.hidratacion as Hidratacion) ?? '') || '',
    comida_omitida: aNumero(json.comida_omitida),
    estres: aNumero(json.estres),
    horas_pantalla: aNumero(json.horas_pantalla),
    minutos_actividad: aNumero(json.minutos_actividad),
    cafeina_tazas: aNumero(json.cafeina_tazas),
    contexto_menstrual: ((json.contexto_menstrual as ContextoMenstrual) ?? '') || '',
    medicacion_rescate: Boolean(json.medicacion_rescate),
    sensaciones_premonitorias: Boolean(json.sensaciones_premonitorias),
    completado: Boolean(json.completado),
  };
}

/**
 * El cuerpo que se envía al backend.
 *
 * `fecha` se omite al editar: el serializador la rechaza si cambia, y enviarla
 * igual solo invita a un 400 accidental.
 */
export function registroHaciaApi(
  r: RegistroDiario,
  incluirFecha = true,
): Record<string, unknown> {
  return {
    ...(incluirFecha ? { fecha: r.fecha } : {}),
    hora_corte: r.hora_corte,
    horas_sueno: r.horas_sueno === null ? null : r.horas_sueno.toFixed(2),
    hidratacion: r.hidratacion,
    comida_omitida: r.comida_omitida,
    estres: r.estres,
    horas_pantalla: r.horas_pantalla === null ? null : r.horas_pantalla.toFixed(2),
    minutos_actividad: r.minutos_actividad,
    cafeina_tazas: r.cafeina_tazas,
    contexto_menstrual: r.contexto_menstrual,
    medicacion_rescate: r.medicacion_rescate,
    sensaciones_premonitorias: r.sensaciones_premonitorias,
  };
}

export interface Episodio {
  id: number | null;
  /** ISO 8601 con zona. */
  inicio: string;
  duracion_min: number | null;
  /** Escala EVA de 1 a 10. */
  intensidad: number;
  nauseas: boolean;
  vomitos: boolean;
  sensibilidad_luz: boolean;
  sensibilidad_sonido: boolean;
  observacion: string;
  en_curso?: boolean;
  /** Los síntomas ya traducidos por el backend. */
  sintomas_presentes?: string[];
  fecha_bitacora?: string | null;
}

export function episodioNuevo(): Episodio {
  return {
    id: null,
    inicio: new Date().toISOString(),
    duracion_min: 60,
    intensidad: 5,
    nauseas: false,
    vomitos: false,
    sensibilidad_luz: false,
    sensibilidad_sonido: false,
    observacion: '',
  };
}

/** Los síntomas calculados en local, para el formulario antes de guardar. */
export function sintomasLocales(e: Episodio): string[] {
  const mapa: [boolean, string][] = [
    [e.nauseas, 'náuseas'],
    [e.vomitos, 'vómitos'],
    [e.sensibilidad_luz, 'sensibilidad a la luz'],
    [e.sensibilidad_sonido, 'sensibilidad al sonido'],
  ];
  return mapa.filter(([presente]) => presente).map(([, nombre]) => nombre);
}

export function duracionLegible(minutos: number | null): string {
  if (minutos === null) return 'En curso';
  const h = Math.floor(minutos / 60);
  const m = minutos % 60;
  if (h === 0) return `${m} min`;
  if (m === 0) return `${h} h`;
  return `${h} h ${m} min`;
}

export function episodioHaciaApi(e: Episodio): Record<string, unknown> {
  return {
    inicio: e.inicio,
    duracion_min: e.duracion_min,
    intensidad: e.intensidad,
    nauseas: e.nauseas,
    vomitos: e.vomitos,
    sensibilidad_luz: e.sensibilidad_luz,
    sensibilidad_sonido: e.sensibilidad_sonido,
    observacion: e.observacion,
  };
}

// ============================================================ historial
export interface DiaHistorial {
  fecha: string;
  tiene_bitacora: boolean;
  bitacora_completa: boolean;
  bitacora_id: number | null;
  medicacion_rescate: boolean;
  episodios: Episodio[];
}

export interface Historial {
  desde: string;
  hasta: string;
  bitacoras_completas: number;
  total_episodios: number;
  dias: DiaHistorial[];
}

export function tuvoEpisodio(d: DiaHistorial): boolean {
  return d.episodios.length > 0;
}
