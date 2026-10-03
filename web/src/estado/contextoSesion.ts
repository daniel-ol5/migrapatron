import { createContext, useContext } from 'react';

import type { Usuario } from '../modelos';

export type FaseSesion = 'cargando' | 'fuera' | 'dentro';

export interface Sesion {
  fase: FaseSesion;
  usuario: Usuario | null;
  ocupado: boolean;
  ingresar: (email: string, password: string) => Promise<string | null>;
  registrar: (datos: {
    email: string;
    password: string;
    nombre: string;
    apellido: string;
    versionAviso: string;
  }) => Promise<string | null>;
  salir: () => Promise<void>;
  refrescar: () => Promise<void>;
  eliminarCuenta: (password: string) => Promise<string | null>;
}

/**
 * El contexto y su hook viven aparte del proveedor a propósito: un archivo que
 * exporta componentes y hooks a la vez rompe el fast refresh de Vite.
 */
export const ContextoSesion = createContext<Sesion | null>(null);

export function useSesion(): Sesion {
  const contexto = useContext(ContextoSesion);
  if (contexto === null) {
    throw new Error('useSesion necesita estar dentro de <ProveedorSesion>.');
  }
  return contexto;
}
