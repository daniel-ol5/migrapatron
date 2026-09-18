import axios, {
  AxiosError,
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from 'axios';
import { API_URL } from './config';
import { almacen } from './almacen';

/**
 * Cliente HTTP único de la aplicación.
 *
 * Adjunta el access token a cada petición y, cuando el backend responde 401,
 * intenta renovarlo una sola vez con el refresh token antes de rendirse.
 * Las peticiones que llegan mientras se renueva esperan en cola, para no
 * disparar varios refresh a la vez.
 */
export const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = almacen.access;
  if (token) {
    config.headers.set('Authorization', `Bearer ${token}`);
  }
  return config;
});

type Reintento = InternalAxiosRequestConfig & { _yaReintentado?: boolean };

let renovando: Promise<string> | null = null;

async function renovarAccess(): Promise<string> {
  const refresh = almacen.refresh;
  if (!refresh) throw new Error('sin refresh token');

  // Instancia limpia: si usáramos `api` entraríamos en bucle de interceptores.
  const { data } = await axios.post<{ access: string }>(
    `${API_URL}/auth/refresh/`,
    { refresh },
    { headers: { 'Content-Type': 'application/json' } },
  );
  almacen.actualizarAccess(data.access);
  return data.access;
}

api.interceptors.response.use(
  (respuesta) => respuesta,
  async (error: AxiosError) => {
    const original = error.config as Reintento | undefined;

    const esAuthExpirada =
      error.response?.status === 401 &&
      original &&
      !original._yaReintentado &&
      !original.url?.includes('/auth/');

    if (!esAuthExpirada) {
      return Promise.reject(error);
    }

    original._yaReintentado = true;

    try {
      renovando ??= renovarAccess().finally(() => {
        renovando = null;
      });
      const nuevoToken = await renovando;
      original.headers.set('Authorization', `Bearer ${nuevoToken}`);
      return api(original);
    } catch {
      almacen.cerrarSesion();
      window.location.assign('/acceso');
      return Promise.reject(error);
    }
  },
);

/** Traduce un error de axios al mensaje que se le muestra a la persona. */
export function mensajeDeError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    if (!error.response) {
      return 'No se pudo conectar con el servidor. Revisa tu conexión.';
    }
    const datos = error.response.data as Record<string, unknown> | undefined;
    const detalle = datos?.detail ?? datos?.mensaje;
    if (typeof detalle === 'string') return detalle;

    if (error.response.status >= 500) {
      return 'El servidor tuvo un problema. Vuelve a intentarlo en un momento.';
    }
  }
  return 'Ocurrió un error inesperado.';
}
