/**
 * Tipos del dominio, espejo de los serializadores del backend.
 *
 * Referencia: docs/diagramas/02_modelo_datos.puml
 */

// ---------------------------------------------------------------- M0
export interface Usuario {
  id: number;
  email: string;
  nombre: string;
  apellido: string;
  fecha_nacimiento: string | null;
  sexo: 'F' | 'M' | 'OTRO' | 'NS' | '';
}

export interface PerfilClinico {
  anios_con_migrana: number | null;
  diagnostico_previo: boolean;
  tipo_migrana: 'CON_AURA' | 'SIN_AURA' | 'CRONICA' | 'DESCONOCIDA';
  medicacion_habitual: string;
  ciclo_menstrual_aplica: boolean;
  consentimiento_analisis: boolean;
  fecha_consentimiento: string | null;
}

export interface RespuestaAcceso {
  access: string;
  refresh: string;
  usuario: Usuario;
}

// ---------------------------------------------------------------- M1
export type Hidratacion = 'BAJA' | 'MEDIA' | 'ALTA';

export type FaseCiclo =
  | 'NO_APLICA'
  | 'MENSTRUACION'
  | 'FOLICULAR'
  | 'OVULACION'
  | 'LUTEA';

export interface RegistroDiario {
  id: number;
  /** ISO 8601, formato AAAA-MM-DD. Único por usuario y fecha (RN-05). */
  fecha: string;
  horas_sueno: number | null;
  calidad_sueno: number | null;
  hidratacion: Hidratacion | null;
  comidas_omitidas: number | null;
  estres_percibido: number | null;
  horas_pantalla: number | null;
  minutos_actividad: number | null;
  cafeina_tazas: number | null;
  consumo_alcohol: boolean | null;
  fase_ciclo: FaseCiclo | null;
  alimentos: number[];
  /** Solo los días completos cuentan para la suficiencia de datos (RN-02). */
  completado: boolean;
}

export type Localizacion =
  | 'UNILATERAL_IZQ'
  | 'UNILATERAL_DER'
  | 'BILATERAL'
  | 'OCCIPITAL'
  | 'DIFUSA';

export interface Episodio {
  id: number;
  inicio: string;
  fin: string | null;
  duracion_min: number | null;
  /** Escala EVA, de 1 a 10. */
  intensidad_eva: number;
  localizacion: Localizacion | null;
  tuvo_aura: boolean;
  medicacion_tomada: string;
  minutos_hasta_alivio: number | null;
  alivio_percibido: number | null;
  limito_actividad: boolean;
  sintomas: number[];
  notas: string;
}

// ---------------------------------------------------------------- M2 y M3
export type EstadoAnalisis = 'OK' | 'DATOS_INSUFICIENTES' | 'ERROR';
export type NivelConfianza = 'ALTA' | 'MEDIA' | 'BAJA';
export type TipoHallazgo = 'ASOCIACION' | 'ARBOL' | 'CORRELACION' | 'FRECUENCIA';

export interface Hallazgo {
  id: number;
  tipo: TipoHallazgo;
  /** Ítems del antecedente, p. ej. ["SUENO_BAJO", "COMIDA_OMITIDA"]. */
  antecedente: string[];
  soporte: number;
  confianza: number;
  lift: number;
  p_valor: number | null;
  episodios_relacionados: number;
  total_episodios: number;
  nivel_confianza: NivelConfianza;
  /** Frase en español compuesta por el explicador. */
  texto_explicacion: string;
  ranking: number;
}

export interface Analisis {
  id: number;
  ejecutado_en: string;
  periodo_inicio: string;
  periodo_fin: string;
  dias_analizados: number;
  episodios_analizados: number;
  lag_dias: number;
  version_motor: string;
  estado: EstadoAnalisis;
  mensaje_estado: string;
  hallazgos: Hallazgo[];
}

export type NivelRiesgo = 'BAJO' | 'MEDIO' | 'ALTO';

export interface RiesgoDiario {
  fecha: string;
  nivel: NivelRiesgo;
  score: number;
  factores_activos: string[];
}

export interface ReporteClinico {
  id: number;
  generado_en: string;
  periodo_inicio: string;
  periodo_fin: string;
  resumen: string;
  formato: 'PDF' | 'TEXTO';
}
