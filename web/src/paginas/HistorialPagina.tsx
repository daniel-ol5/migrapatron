import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import {
  Cargando,
  EstadoVacio,
  InsigniaEva,
  Mensaje,
} from '../componentes';
import {
  duracionLegible,
  sintomasLocales,
  tuvoEpisodio,
  type DiaHistorial,
  type Historial,
} from '../modelos';
import { detalleDeError, servicioBitacora } from '../servicios/bitacora';

/**
 * HU-07. Historial propio ordenado cronológicamente.
 *
 * Muestra también los días SIN registrar, y eso es deliberado: ver los huecos
 * es parte del valor. El paciente necesita saber qué le falta para que el
 * análisis tenga datos suficientes, no solo qué ya hizo.
 */
export default function HistorialPagina() {
  const [dias, setDias] = useState(30);
  const [soloConRegistro, setSoloConRegistro] = useState(false);
  const [historial, setHistorial] = useState<Historial | null>(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let vigente = true;

    const cargar = async () => {
      setError(null);
      try {
        const datos = await servicioBitacora.historial(dias);
        if (vigente) setHistorial(datos);
      } catch (e) {
        if (vigente) setError(detalleDeError(e));
      } finally {
        if (vigente) setCargando(false);
      }
    };

    void cargar();
    return () => {
      vigente = false;
    };
  }, [dias]);

  const visibles = (historial?.dias ?? []).filter(
    (d) => !soloConRegistro || d.tiene_bitacora || tuvoEpisodio(d),
  );

  return (
    <div className="pagina">
      <div className="fila-separada">
        <h1>Historial</h1>
        <Link to="/episodio/nuevo" className="boton">
          Registrar episodio
        </Link>
      </div>

      <div
        className="fila"
        style={{ marginTop: 'var(--esp-md)', flexWrap: 'wrap' }}
      >
        <div className="grupo-opciones">
          {[7, 30, 90].map((n) => (
            <button
              key={n}
              type="button"
              className="opcion"
              aria-pressed={dias === n}
              onClick={() => {
                setDias(n);
                setCargando(true);
              }}
            >
              {n} días
            </button>
          ))}
        </div>
        <button
          type="button"
          className="opcion"
          aria-pressed={soloConRegistro}
          onClick={() => setSoloConRegistro((v) => !v)}
          style={{ marginLeft: 'auto' }}
        >
          {soloConRegistro ? 'Mostrando solo con datos' : 'Ocultar días vacíos'}
        </button>
      </div>

      {historial !== null && (
        <div className="fila" style={{ marginTop: 'var(--esp-md)' }}>
          <span className="pastilla">
            {historial.bitacoras_completas} días completos
          </span>
          <span className="pastilla">{historial.total_episodios} episodios</span>
        </div>
      )}

      {cargando && <Cargando />}

      {error !== null && (
        <div style={{ marginTop: 'var(--esp-md)' }}>
          <Mensaje tipo="error">{error}</Mensaje>
        </div>
      )}

      {!cargando && error === null && visibles.length === 0 && (
        <EstadoVacio
          icono=""
          titulo="Nada registrado en este periodo"
          detalle="Registra tu día desde la pantalla de inicio."
        />
      )}

      <div
        className="columna"
        style={{ marginTop: 'var(--esp-md)', gap: 'var(--esp-sm)' }}
      >
        {visibles.map((dia) => (
          <FilaDia key={dia.fecha} dia={dia} />
        ))}
      </div>
    </div>
  );
}

const DIAS_SEMANA = ['dom', 'lun', 'mar', 'mié', 'jue', 'vie', 'sáb'];

function FilaDia({ dia }: { dia: DiaHistorial }) {
  const [a, m, d] = dia.fecha.split('-').map(Number);
  const fecha = new Date(a, m - 1, d);
  const vacio = !dia.tiene_bitacora && !tuvoEpisodio(dia);

  const estado = !dia.tiene_bitacora
    ? 'Sin registrar'
    : !dia.bitacora_completa
      ? 'Registro incompleto'
      : 'Día completo';

  return (
    // Los días sin nada se atenúan, pero siguen visibles: el hueco es
    // información, no basura que haya que esconder.
    <div className="tarjeta-lista" style={{ opacity: vacio ? 0.6 : 1 }}>
      <Link
        to={`/bitacora?fecha=${dia.fecha}`}
        className="celda-boton"
        style={{ color: 'inherit', textDecoration: 'none' }}
      >
        <div className="fila">
          <span
            style={{
              width: 40,
              flex: 'none',
              textAlign: 'center',
              lineHeight: 1.1,
            }}
          >
            <strong className="mono" style={{ fontSize: '1.05rem' }}>
              {d}
            </strong>
            <div className="pequeno apagado" style={{ fontSize: '0.72rem' }}>
              {DIAS_SEMANA[fecha.getDay()]}
            </div>
          </span>
          <span
            aria-hidden="true"
            style={{
              width: 1,
              height: 30,
              background: 'var(--borde)',
              flex: 'none',
            }}
          />
          <span className="crecer">
            <div className={dia.tiene_bitacora ? '' : 'apagado'}>{estado}</div>
            {dia.medicacion_rescate && (
              <div
                className="pequeno"
                style={{ color: 'var(--aviso)', fontSize: '0.78rem' }}
              >
                Medicación de rescate
              </div>
            )}
          </span>
          <span
            aria-hidden="true"
            style={{
              color: dia.tiene_bitacora
                ? dia.bitacora_completa
                  ? 'var(--exito)'
                  : 'var(--aviso)'
                : 'var(--apagado)',
            }}
          >
            {dia.tiene_bitacora ? (dia.bitacora_completa ? '✓' : '◍') : '+'}
          </span>
        </div>
      </Link>

      {dia.episodios.map((ep) => {
        const sintomas =
          ep.sintomas_presentes !== undefined && ep.sintomas_presentes.length > 0
            ? ep.sintomas_presentes
            : sintomasLocales(ep);
        return (
          <Link
            key={ep.id}
            to={`/episodio/${ep.id}`}
            className="celda-boton"
            style={{ color: 'inherit', textDecoration: 'none' }}
          >
            <div className="fila">
              <InsigniaEva intensidad={ep.intensidad} />
              <span className="crecer">
                <div>{duracionLegible(ep.duracion_min)}</div>
                {sintomas.length > 0 && (
                  <div className="pequeno apagado">{sintomas.join(', ')}</div>
                )}
              </span>
              <span className="apagado" aria-hidden="true">
                ›
              </span>
            </div>
          </Link>
        );
      })}
    </div>
  );
}
