/**
 * Almacenamiento de los tokens de sesión.
 *
 * En web usamos localStorage. Es la opción práctica para el alcance del
 * proyecto, pero no es equivalente al almacén cifrado del móvil (RNF-05):
 * un XSS puede leerlo. Por eso el access token dura 15 minutos.
 */

const CLAVE_ACCESS = 'migrapatron.access';
const CLAVE_REFRESH = 'migrapatron.refresh';

function leer(clave: string): string | null {
  try {
    return localStorage.getItem(clave);
  } catch {
    return null;
  }
}

function escribir(clave: string, valor: string): void {
  try {
    localStorage.setItem(clave, valor);
  } catch {
    /* modo privado o almacenamiento bloqueado: la sesión vive solo en memoria */
  }
}

function borrar(clave: string): void {
  try {
    localStorage.removeItem(clave);
  } catch {
    /* nada que hacer */
  }
}

export const almacen = {
  get access() {
    return leer(CLAVE_ACCESS);
  },
  get refresh() {
    return leer(CLAVE_REFRESH);
  },
  guardarSesion(access: string, refresh: string): void {
    escribir(CLAVE_ACCESS, access);
    escribir(CLAVE_REFRESH, refresh);
  },
  actualizarAccess(access: string): void {
    escribir(CLAVE_ACCESS, access);
  },
  cerrarSesion(): void {
    borrar(CLAVE_ACCESS);
    borrar(CLAVE_REFRESH);
  },
  get haySesion(): boolean {
    return leer(CLAVE_ACCESS) !== null;
  },
};
