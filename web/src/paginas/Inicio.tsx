import { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';

import {
  AvisoNoCausalidad,
  Barra,
  Cargando,
  InsigniaEva,
  Mensaje,
  TituloSeccion,
} from '../componentes';
import { MINIMO_BITACORAS, MINIMO_EPISODIOS } from '../core/config';
import { useSesion } from '../estado/contextoSesion';
import {
  comoFecha,
  duracionLegible,
  sintomasLocales,
  type AlertaMedicacion,
  type Episodio,
  type Historial,
} from '../modelos';
import { servicioAnalisis } from '../servicios/analisis';
import { detalleDeError, servicioBitacora } from '../servicios/bitacora';

/** Pantalla de inicio: el estado de hoy y el avance hacia el análisis. */
export default function Inicio() {
  const { usuario } = useSesion();
  const navegar = useNavigate();
  const ubicacion = useLocation();
  const nota = (ubicacion.state as { nota?: string } | null)?.nota;

  const [historial, setHistorial] = useState<Historial | null>(null);
  const [alertaMedicacion, setAlertaMedicacion] = useState<AlertaMedicacion | null>(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let vigente = true;

    const cargar = async () => {
      try {
        const [datos, med] = await Promise.all([
          servicioBitacora.historial(30),
          servicioAnalisis.alertaMedicacion().catch(() => null),
        ]);
        if (vigente) {
          setHistorial(datos);
          setAlertaMedicacion(med);
        }
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
  }, []);

  // El mensaje de la navegación se limpia para que no reaparezca al volver.
  useEffect(() => {
    if (nota !== undefined) {
      navegar('.', { replace: true, state: null });
    }
  }, [nota, navegar]);

  const hoy = comoFecha(new Date());
  const diaDeHoy = historial?.dias.find((d) => d.fecha === hoy);
  const episodios = historial?.dias.flatMap((d) => d.episodios) ?? [];

  const bitacoras = historial?.bitacoras_completas ?? 0;
  const totalEpisodios = historial?.total_episodios ?? 0;
  const listo = bitacoras >= MINIMO_BITACORAS && totalEpisodios >= MINIMO_EPISODIOS;

  return (
    <div className="pagina">
      {nota !== undefined && (
        <div style={{ marginBottom: 'var(--esp-md)' }}>
          <Mensaje tipo="exito">{nota}</Mensaje>
        </div>
      )}

      <p className="pequeno apagado">{saludo()}</p>
      <h1>{usuario?.nombre ?? ''}</h1>

      <div style={{ marginTop: 'var(--esp-lg)' }}>
        <TarjetaHoy
          cargando={cargando}
          registrado={diaDeHoy?.tiene_bitacora ?? false}
          completo={diaDeHoy?.bitacora_completa ?? false}
        />
      </div>

      <Link
        to="/episodio/nuevo"
        className="boton boton-contorno boton-ancho"
        style={{ marginTop: 'var(--esp-sm)' }}
      >
        Registrar un episodio
      </Link>

      {cargando && <Cargando />}

      {error !== null && (
        <div style={{ marginTop: 'var(--esp-md)' }}>
          <Mensaje tipo="error">{error}</Mensaje>
        </div>
      )}

      {alertaMedicacion?.alerta_activa && (
        <div
          className="tarjeta"
          style={{
            marginTop: 'var(--esp-md)',
            borderLeft: '4px solid var(--aviso)',
          }}
        >
          <div className="fila">
            <span
              style={{
                width: 32,
                height: 32,
                borderRadius: 'var(--radio)',
                background: 'rgba(184, 124, 40, 0.15)',
                color: 'var(--aviso)',
                display: 'grid',
                placeItems: 'center',
                fontWeight: 700,
                fontSize: '0.8rem',
                flex: 'none',
              }}
              aria-hidden="true"
            >
              Rx
            </span>
            <div className="crecer">
              <strong style={{ color: 'var(--aviso)' }}>
                Alerta de Medicación de Rescate
              </strong>
              <p className="pequeno" style={{ marginTop: 'var(--esp-xs)' }}>
                {alertaMedicacion.mensaje}
              </p>
            </div>
          </div>
        </div>
      )}

      {historial !== null && (
        <>
          <TituloSeccion>Avance hacia el análisis</TituloSeccion>
          <div className="tarjeta">
            <p style={{ marginBottom: 'var(--esp-md)', fontWeight: 600 }}>
              {listo ? 'Datos suficientes para análisis IA' : 'Todavía faltan datos'}
            </p>

            <div className="columna" style={{ gap: 'var(--esp-md)' }}>
              <Barra
                etiqueta="Días completos (mínimo 60)"
                actual={bitacoras}
                meta={MINIMO_BITACORAS}
              />
              <Barra
                etiqueta="Episodios (mínimo 6)"
                actual={totalEpisodios}
                meta={MINIMO_EPISODIOS}
              />
            </div>

            {listo ? (
              <div style={{ marginTop: 'var(--esp-md)' }}>
                <p className="pequeno" style={{ marginBottom: 'var(--esp-sm)', color: 'var(--exito)' }}>
                  Cumples con el volumen y balance de 60 días para entrenar tu modelo supervisado de Regresión Logística L2.
                </p>
                <Link to="/analisis" className="boton boton-ancho">
                  Ver análisis y estimación de riesgo
                </Link>
              </div>
            ) : (
              <p
                className="pequeno apagado"
                style={{ marginTop: 'var(--esp-md)', lineHeight: 1.45 }}
              >
                {queFalta(bitacoras, totalEpisodios)}
              </p>
            )}
          </div>
        </>
      )}

      {episodios.length > 0 && (
        <>
          <TituloSeccion>Últimos episodios</TituloSeccion>
          <div className="tarjeta-lista">
            {episodios.slice(0, 4).map((ep) => (
              <FilaEpisodio key={ep.id} episodio={ep} />
            ))}
          </div>
        </>
      )}

      {usuario !== null && !usuario.consintio_analisis && (
        <div style={{ marginTop: 'var(--esp-lg)' }}>
          <Mensaje>
            <strong>El análisis está desactivado.</strong> Retiraste tu
            consentimiento, así que no buscamos patrones en tus datos. Tus
            registros se conservan y puedes volver a activarlo desde{' '}
            <Link to="/perfil">tu perfil</Link>.
          </Mensaje>
        </div>
      )}

      <div style={{ marginTop: 'var(--esp-lg)' }}>
        <AvisoNoCausalidad />
      </div>
    </div>
  );
}

function TarjetaHoy({
  cargando,
  registrado,
  completo,
}: {
  cargando: boolean;
  registrado: boolean;
  completo: boolean;
}) {
  const [icono, titulo, detalle, color] = cargando
    ? ['◌', 'Cargando tu día…', '', 'var(--apagado)']
    : !registrado
      ? ['✎', 'Hoy no has registrado', 'Toma menos de un minuto.', 'var(--primario)']
      : !completo
        ? [
            '◍',
            'Tu día está incompleto',
            'Faltan factores para que cuente en el análisis.',
            'var(--aviso)',
          ]
        : ['✓', 'Día registrado', 'Puedes editarlo si algo cambió.', 'var(--exito)'];

  return (
    <Link
      to="/bitacora"
      className="tarjeta"
      style={{ display: 'block', color: 'inherit', textDecoration: 'none' }}
    >
      <div className="fila">
        <span
          aria-hidden="true"
          style={{
            width: 44,
            height: 44,
            flex: 'none',
            display: 'grid',
            placeItems: 'center',
            borderRadius: 12,
            background: `color-mix(in srgb, ${color} 14%, transparent)`,
            color,
            fontSize: '1.2rem',
          }}
        >
          {icono}
        </span>
        <span className="crecer">
          <strong>{titulo}</strong>
          {detalle !== '' && <div className="pequeno apagado">{detalle}</div>}
        </span>
        <span className="apagado" aria-hidden="true">
          ›
        </span>
      </div>
    </Link>
  );
}

function FilaEpisodio({ episodio }: { episodio: Episodio }) {
  const sintomas =
    episodio.sintomas_presentes !== undefined &&
    episodio.sintomas_presentes.length > 0
      ? episodio.sintomas_presentes
      : sintomasLocales(episodio);

  return (
    <Link
      to={`/episodio/${episodio.id}`}
      className="celda-boton"
      style={{ color: 'inherit', textDecoration: 'none' }}
    >
      <div className="fila">
        <InsigniaEva intensidad={episodio.intensidad} />
        <span className="crecer">
          <div>{fechaCorta(episodio.inicio)}</div>
          <div className="pequeno apagado">
            {[duracionLegible(episodio.duracion_min), ...sintomas.slice(0, 2)].join(
              ' · ',
            )}
          </div>
        </span>
        <span className="apagado" aria-hidden="true">
          ›
        </span>
      </div>
    </Link>
  );
}

function saludo(): string {
  const h = new Date().getHours();
  if (h < 12) return 'Buenos días';
  if (h < 19) return 'Buenas tardes';
  return 'Buenas noches';
}

function queFalta(bitacoras: number, episodios: number): string {
  const partes: string[] = [];
  const faltanB = Math.max(MINIMO_BITACORAS - bitacoras, 0);
  const faltanE = Math.max(MINIMO_EPISODIOS - episodios, 0);

  if (faltanB > 0) {
    partes.push(faltanB === 1 ? '1 día completo' : `${faltanB} días completos`);
  }
  if (faltanE > 0) {
    partes.push(faltanE === 1 ? '1 episodio' : `${faltanE} episodios`);
  }
  return `Faltan ${partes.join(' y ')} para poder buscar patrones.`;
}

function fechaCorta(iso: string): string {
  const d = new Date(iso);
  const hoy = new Date();
  const ayer = new Date(hoy.getTime() - 86_400_000);
  const p = (n: number) => `${n}`.padStart(2, '0');
  const hora = `${p(d.getHours())}:${p(d.getMinutes())}`;

  const mismoDia = (a: Date, b: Date) =>
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate();

  if (mismoDia(d, hoy)) return `Hoy · ${hora}`;
  if (mismoDia(d, ayer)) return `Ayer · ${hora}`;
  return `${d.getDate()}/${d.getMonth() + 1} · ${hora}`;
}
