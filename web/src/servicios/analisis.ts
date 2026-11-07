import { api } from '../core/api';
import type {
  AlertaBanderaRoja,
  AlertaMedicacion,
  EstadoSuficiencia,
  EstimacionRiesgo,
  RespuestaAnalisis,
} from '../modelos';

/** Servicio de M2: Análisis de patrones, estimación de riesgo y alertas clínicas. */
export const servicioAnalisis = {
  /** RF-07A/B. Consulta el estado de suficiencia de datos (60 días, balance de clases). */
  async suficiencia(): Promise<EstadoSuficiencia> {
    const { data } = await api.get<EstadoSuficiencia>('/analisis/suficiencia/');
    return data;
  },

  /** HU-18 / RF-15. Consulta el estado de alerta por uso de medicación de rescate en 30 días. */
  async alertaMedicacion(): Promise<AlertaMedicacion> {
    const { data } = await api.get<AlertaMedicacion>('/analisis/medicacion/');
    return data;
  },

  /** Obtiene la última estimación de riesgo calculada. */
  async ultimoAnalisis(): Promise<EstimacionRiesgo | null> {
    const { data } = await api.get<EstimacionRiesgo | null>('/analisis/ultimo/');
    return data;
  },

  /** HU-10 a HU-16. Ejecuta el entrenamiento de Regresión Logística L2 y estimación de riesgo. */
  async ejecutarAnalisis(horizonteHoras = 48): Promise<RespuestaAnalisis> {
    const { data } = await api.post<RespuestaAnalisis>('/analisis/ejecutar/', {
      horizonte_horas: horizonteHoras,
    });
    return data;
  },

  /** HU-17 / RF-14. Confirma y atiende una alerta médica prioritaria de bandera roja. */
  async confirmarAlertaBanderaRoja(id: number): Promise<AlertaBanderaRoja> {
    const { data } = await api.post<AlertaBanderaRoja>(`/alertas/${id}/confirmar/`);
    return data;
  },
};

