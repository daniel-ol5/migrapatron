import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

import { almacen } from '../core/almacen';
import type { Usuario } from '../modelos';
import { servicioAuth } from '../servicios/auth';
import { detalleDeError } from '../servicios/bitacora';
import { ContextoSesion, type FaseSesion, type Sesion } from './contextoSesion';

/**
 * Estado de la sesión del paciente.
 *
 * Es la única fuente de verdad sobre quién está dentro. Las páginas no guardan
 * copias del usuario: lo leen de aquí, para que un cambio de perfil se refleje
 * en todas a la vez.
 */
export function ProveedorSesion({ children }: { children: ReactNode }) {
  // La fase inicial se deduce del almacén, sin pasar por un efecto: si no hay
  // token guardado ya sabemos que estamos fuera, y arrancar en «cargando» para
  // corregirlo en el primer efecto provocaría un render de más.
  const [fase, setFase] = useState<FaseSesion>(() =>
    almacen.haySesion ? 'cargando' : 'fuera',
  );
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [ocupado, setOcupado] = useState(false);

  /**
   * Verifica que el token guardado siga sirviendo.
   *
   * Tenerlo no garantiza que sea válido, así que se comprueba pidiendo el
   * perfil. Si venció y el refresh también, el interceptor cierra la sesión y
   * aquí se cae a la pantalla de acceso.
   */
  useEffect(() => {
    if (!almacen.haySesion) return;
    let vigente = true;

    const verificar = async () => {
      try {
        const perfil = await servicioAuth.perfil();
        if (!vigente) return;
        setUsuario(perfil);
        setFase('dentro');
      } catch {
        if (!vigente) return;
        almacen.cerrarSesion();
        setUsuario(null);
        setFase('fuera');
      }
    };

    void verificar();
    return () => {
      vigente = false;
    };
  }, []);

  const intentar = useCallback(
    async (accion: () => Promise<Usuario>): Promise<string | null> => {
      setOcupado(true);
      try {
        setUsuario(await accion());
        setFase('dentro');
        return null;
      } catch (error) {
        return detalleDeError(error);
      } finally {
        setOcupado(false);
      }
    },
    [],
  );

  const valor = useMemo<Sesion>(
    () => ({
      fase,
      usuario,
      ocupado,

      ingresar: (email, password) =>
        intentar(() => servicioAuth.ingresar(email, password)),

      registrar: (datos) => intentar(() => servicioAuth.registrar(datos)),

      salir: async () => {
        setOcupado(true);
        await servicioAuth.salir();
        setUsuario(null);
        setFase('fuera');
        setOcupado(false);
      },

      refrescar: async () => {
        try {
          setUsuario(await servicioAuth.perfil());
        } catch {
          // Se conserva lo que ya había: un fallo de red no debe vaciar la
          // pantalla que el paciente está mirando.
        }
      },

      eliminarCuenta: async (password) => {
        setOcupado(true);
        try {
          await servicioAuth.eliminarCuenta(password);
          setUsuario(null);
          setFase('fuera');
          return null;
        } catch (error) {
          return detalleDeError(error);
        } finally {
          setOcupado(false);
        }
      },
    }),
    [fase, usuario, ocupado, intentar],
  );

  return (
    <ContextoSesion.Provider value={valor}>{children}</ContextoSesion.Provider>
  );
}
