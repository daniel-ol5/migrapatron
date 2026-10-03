import { useEffect, useState } from 'react';

import { Mensaje } from './index';

/**
 * Un mensaje breve que se desvanece.
 *
 * Vive en su propio archivo porque mezclar hooks y componentes en uno rompe el
 * fast refresh de Vite.
 */
export function useNotificacion() {
  const [nota, setNota] = useState<{ texto: string; esError: boolean } | null>(
    null,
  );

  useEffect(() => {
    if (nota === null) return;
    const t = setTimeout(() => setNota(null), nota.esError ? 6000 : 3000);
    return () => clearTimeout(t);
  }, [nota]);

  const avisar = (texto: string, esError = false) => setNota({ texto, esError });

  const vista =
    nota === null ? null : (
      <div style={{ marginBottom: 'var(--esp-md)' }}>
        <Mensaje tipo={nota.esError ? 'error' : 'exito'}>{nota.texto}</Mensaje>
      </div>
    );

  return { avisar, vista };
}
