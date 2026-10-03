import axios from 'axios';

import { api } from '../core/api';
import {
  episodioHaciaApi,
  registroDesdeApi,
  registroHaciaApi,
  type Episodio,
  type Historial,
  type Pagina,
  type RegistroDiario,
} from '../modelos';

/** Servicio de M1: bitácora diaria, episodios e historial. */
export const servicioBitacora = {
  /**
   * HU-05. Busca la bitácora de un día. Devuelve null si ese día no tiene.
   *
   * La página la llama al cargarse: si existe, entra en modo edición en lugar
   * de intentar un alta que la unicidad va a rechazar con un 400.
   */
  async bitacoraDe(fecha: string): Promise<RegistroDiario | null> {
    try {
      const { data } = await api.get<Record<string, unknown>>(
        `/bitacora/fecha/${fecha}/`,
      );
      return registroDesdeApi(data);
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  },

  /** HU-05 (alta) y HU-08 (edición). Decide el método según si ya tiene id. */
  async guardarBitacora(registro: RegistroDiario): Promise<RegistroDiario> {
    const esNuevo = registro.id === null;
    const { data } = esNuevo
      ? await api.post<Record<string, unknown>>(
          '/bitacora/',
          registroHaciaApi(registro),
        )
      : await api.patch<Record<string, unknown>>(
          `/bitacora/${registro.id}/`,
          // Al editar no se envía la fecha: el backend la rechaza si cambia.
          registroHaciaApi(registro, false),
        );
    return registroDesdeApi(data);
  },

  /** HU-09. Eliminación de la bitácora. Los episodios del día se conservan. */
  async eliminarBitacora(id: number): Promise<void> {
    await api.delete(`/bitacora/${id}/`);
  },

  /** HU-07. Lista paginada de bitácoras. */
  async listarBitacoras(): Promise<RegistroDiario[]> {
    const { data } = await api.get<Pagina<Record<string, unknown>>>('/bitacora/');
    return data.results.map(registroDesdeApi);
  },

  // ------------------------------------------------------------- episodios
  /** HU-06. Un episodio por id, para editarlo. */
  async episodioDe(id: number): Promise<Episodio> {
    const { data } = await api.get<Episodio>(`/episodios/${id}/`);
    return data;
  },

  /** HU-06 (alta) y HU-08 (edición). */
  async guardarEpisodio(episodio: Episodio): Promise<Episodio> {
    const esNuevo = episodio.id === null;
    const { data } = esNuevo
      ? await api.post<Episodio>('/episodios/', episodioHaciaApi(episodio))
      : await api.patch<Episodio>(
          `/episodios/${episodio.id}/`,
          episodioHaciaApi(episodio),
        );
    return data;
  },

  /** HU-09. Eliminación del episodio. */
  async eliminarEpisodio(id: number): Promise<void> {
    await api.delete(`/episodios/${id}/`);
  },

  // ------------------------------------------------------------- historial
  /** HU-07. Historial propio, con los días sin registrar incluidos. */
  async historial(dias = 30): Promise<Historial> {
    const { data } = await api.get<Historial>('/historial/', {
      params: { dias },
    });
    return data;
  },
};

/**
 * Saca el mensaje del campo que el backend rechazó.
 *
 * Si el backend dice «ya registraste este día», eso es mucho más útil que un
 * «ocurrió un error» genérico.
 */
export function detalleDeError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    if (!error.response) {
      return 'No se pudo conectar con el servidor. Revisa tu conexión.';
    }
    const datos = error.response.data as Record<string, unknown> | undefined;
    if (datos) {
      for (const valor of Object.values(datos)) {
        if (Array.isArray(valor) && valor.length > 0) return String(valor[0]);
        if (typeof valor === 'string') return valor;
      }
    }
    if (error.response.status >= 500) {
      return 'El servidor tuvo un problema. Vuelve a intentarlo.';
    }
  }
  return 'Ocurrió un error inesperado.';
}
