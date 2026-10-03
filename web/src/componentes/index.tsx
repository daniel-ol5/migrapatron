import { useEffect, type ReactNode } from 'react';

import { AVISO_NO_CAUSALIDAD } from '../core/config';

/**
 * El aviso de no causalidad.
 *
 * No es letra chica legal: es un requisito funcional verificable. Acompaña a
 * todo lugar donde se muestren patrones o resultados del análisis.
 */
export function AvisoNoCausalidad() {
  return (
    <p className="aviso">
      <span className="aviso-icono" aria-hidden="true">
        ⓘ
      </span>
      <span>{AVISO_NO_CAUSALIDAD}</span>
    </p>
  );
}

export function Mensaje({
  tipo = 'aviso',
  children,
}: {
  tipo?: 'aviso' | 'error' | 'exito';
  children: ReactNode;
}) {
  const icono = tipo === 'error' ? '⚠' : tipo === 'exito' ? '✓' : 'ⓘ';
  return (
    <p className={`aviso ${tipo === 'aviso' ? '' : `aviso-${tipo}`}`} role={tipo === 'error' ? 'alert' : undefined}>
      <span className="aviso-icono" aria-hidden="true">
        {icono}
      </span>
      <span>{children}</span>
    </p>
  );
}

/**
 * Insignia de intensidad EVA.
 *
 * El color sale de la rampa cálida, nunca del verde azulado de marca: así
 * «botón principal» y «dolor intenso» no compiten visualmente.
 */
export function InsigniaEva({
  intensidad,
  grande = false,
}: {
  intensidad: number;
  grande?: boolean;
}) {
  const nivel = Math.min(Math.max(intensidad, 1), 10);
  return (
    <span
      className={`eva${grande ? ' eva-grande' : ''}`}
      style={{
        color: `var(--eva-${nivel})`,
        background: `color-mix(in srgb, var(--eva-${nivel}) 18%, transparent)`,
      }}
      title={`Intensidad ${nivel} de 10`}
    >
      {nivel}
    </span>
  );
}

export function TituloSeccion({
  children,
  ayuda,
}: {
  children: ReactNode;
  ayuda?: string;
}) {
  return (
    <div className="seccion">
      <h2 className="titulo-seccion">{children}</h2>
      {ayuda !== undefined && <p className="ayuda-seccion">{ayuda}</p>}
    </div>
  );
}

export function EstadoVacio({
  icono,
  titulo,
  detalle,
  accion,
}: {
  icono: string;
  titulo: string;
  detalle?: string;
  accion?: ReactNode;
}) {
  return (
    <div className="estado-vacio">
      <div className="estado-vacio-icono" aria-hidden="true">
        {icono}
      </div>
      <h3>{titulo}</h3>
      {detalle !== undefined && (
        <p className="pequeno" style={{ marginTop: 'var(--esp-sm)' }}>
          {detalle}
        </p>
      )}
      {accion !== undefined && (
        <div style={{ marginTop: 'var(--esp-lg)' }}>{accion}</div>
      )}
    </div>
  );
}

export function Cargando({ texto = 'Cargando…' }: { texto?: string }) {
  return (
    <div className="estado-vacio">
      <div className="fila" style={{ justifyContent: 'center' }}>
        <span className="girando" aria-hidden="true" />
        <span className="pequeno">{texto}</span>
      </div>
    </div>
  );
}

export function Interruptor({
  titulo,
  detalle,
  valor,
  onCambio,
  desactivado = false,
}: {
  titulo: string;
  detalle?: string;
  valor: boolean;
  onCambio: (v: boolean) => void;
  desactivado?: boolean;
}) {
  return (
    <label className="interruptor">
      <input
        type="checkbox"
        role="switch"
        checked={valor}
        disabled={desactivado}
        onChange={(e) => onCambio(e.target.checked)}
      />
      <span className="interruptor-texto">
        <span className="interruptor-titulo">{titulo}</span>
        {detalle !== undefined && (
          <span className="interruptor-detalle">{detalle}</span>
        )}
      </span>
    </label>
  );
}

/**
 * Pide confirmación antes de una acción irreversible.
 *
 * HU-09 lo exige: un solo clic no borra datos clínicos.
 */
export function Dialogo({
  titulo,
  mensaje,
  textoAceptar = 'Eliminar',
  onAceptar,
  onCancelar,
}: {
  titulo: string;
  mensaje: string;
  textoAceptar?: string;
  onAceptar: () => void;
  onCancelar: () => void;
}) {
  useEffect(() => {
    const alPulsar = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCancelar();
    };
    window.addEventListener('keydown', alPulsar);
    return () => window.removeEventListener('keydown', alPulsar);
  }, [onCancelar]);

  return (
    <div
      className="capa-dialogo"
      role="dialog"
      aria-modal="true"
      aria-label={titulo}
      onClick={(e) => {
        if (e.target === e.currentTarget) onCancelar();
      }}
    >
      <div className="dialogo">
        <h3>{titulo}</h3>
        <p className="apagado" style={{ margin: 'var(--esp-sm) 0 var(--esp-lg)' }}>
          {mensaje}
        </p>
        <div className="fila" style={{ justifyContent: 'flex-end' }}>
          <button type="button" className="boton boton-contorno" onClick={onCancelar}>
            Cancelar
          </button>
          <button type="button" className="boton boton-peligro" onClick={onAceptar}>
            {textoAceptar}
          </button>
        </div>
      </div>
    </div>
  );
}

/** Barra de avance con su meta a la vista. */
export function Barra({
  etiqueta,
  actual,
  meta,
}: {
  etiqueta: string;
  actual: number;
  meta: number;
}) {
  const listo = actual >= meta;
  const proporcion = Math.min(actual / meta, 1) * 100;

  return (
    <div>
      <div className="fila-separada" style={{ marginBottom: 'var(--esp-xs)' }}>
        <span className="pequeno apagado">{etiqueta}</span>
        <span
          className="pequeno mono"
          style={{
            color: listo ? 'var(--exito)' : 'var(--texto)',
            fontWeight: 600,
          }}
        >
          {actual} / {meta}
        </span>
      </div>
      <div
        className="barra"
        role="progressbar"
        aria-valuenow={actual}
        aria-valuemin={0}
        aria-valuemax={meta}
        aria-label={etiqueta}
      >
        <div
          className={`barra-relleno${listo ? ' listo' : ''}`}
          style={{ width: `${proporcion}%` }}
        />
      </div>
    </div>
  );
}
