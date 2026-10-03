import { api } from '../core/api';
import { almacen } from '../core/almacen';
import type {
  AvisoPrivacidad,
  EstadoConsentimiento,
  PerfilClinico,
  RespuestaSesion,
  Usuario,
} from '../modelos';

/** Servicio de M0: registro, sesión, perfil y consentimiento. */
export const servicioAuth = {
  /** El aviso vigente. Es público: hay que poder leerlo antes de registrarse. */
  async avisoVigente(): Promise<AvisoPrivacidad> {
    const { data } = await api.get<AvisoPrivacidad>('/auth/aviso-privacidad/');
    return data;
  },

  /** HU-01. Registro con aceptación del aviso y conservación de su versión. */
  async registrar(datos: {
    email: string;
    password: string;
    nombre: string;
    apellido: string;
    versionAviso: string;
  }): Promise<Usuario> {
    const { data } = await api.post<RespuestaSesion>('/auth/registro/', {
      email: datos.email.trim().toLowerCase(),
      password: datos.password,
      nombre: datos.nombre.trim(),
      apellido: datos.apellido.trim(),
      acepta_aviso: true,
      version_aviso: datos.versionAviso,
    });
    almacen.guardarSesion(data.access, data.refresh);
    return data.usuario;
  },

  /** HU-02. Inicio de sesión. */
  async ingresar(email: string, password: string): Promise<Usuario> {
    const { data } = await api.post<RespuestaSesion>('/auth/login/', {
      email: email.trim().toLowerCase(),
      password,
    });
    almacen.guardarSesion(data.access, data.refresh);
    return data.usuario;
  },

  /**
   * HU-03. Cierre de sesión por POST.
   *
   * Los tokens locales se borran incluso si el servidor falla: si no, el
   * usuario pulsó «salir» y se quedaría dentro, que es lo peor que puede pasar
   * en una computadora compartida.
   */
  async salir(): Promise<void> {
    const refresh = almacen.refresh;
    try {
      if (refresh) await api.post('/auth/logout/', { refresh });
    } catch {
      // Sin red o token ya vencido: igual se cierra en local.
    } finally {
      almacen.cerrarSesion();
    }
  },

  /** HU-04. Perfil propio. */
  async perfil(): Promise<Usuario> {
    const { data } = await api.get<Usuario>('/auth/perfil/');
    return data;
  },

  /** HU-04. Actualización del perfil. El email no se cambia por esta vía. */
  async actualizarPerfil(cambios: {
    nombre?: string;
    apellido?: string;
    clinico?: Partial<PerfilClinico>;
  }): Promise<Usuario> {
    const { data } = await api.patch<Usuario>('/auth/perfil/', {
      ...(cambios.nombre !== undefined ? { nombre: cambios.nombre.trim() } : {}),
      ...(cambios.apellido !== undefined
        ? { apellido: cambios.apellido.trim() }
        : {}),
      ...(cambios.clinico ?? {}),
    });
    return data;
  },

  /** HU-04. Historial de consentimiento: cada cambio es un hecho nuevo. */
  async consentimiento(): Promise<EstadoConsentimiento> {
    const { data } = await api.get<EstadoConsentimiento>('/auth/consentimiento/');
    return data;
  },

  /** HU-04. Otorgar o retirar el consentimiento. */
  async cambiarConsentimiento(
    aceptado: boolean,
    versionAviso?: string,
  ): Promise<void> {
    await api.post('/auth/consentimiento/', {
      aceptado,
      ...(aceptado && versionAviso ? { version_aviso: versionAviso } : {}),
    });
  },

  /** M0.4. Baja de cuenta. Exige contraseña y confirmación escrita. */
  async eliminarCuenta(password: string): Promise<void> {
    await api.post('/auth/baja/', { password, confirmacion: 'ELIMINAR' });
    almacen.cerrarSesion();
  },
};
