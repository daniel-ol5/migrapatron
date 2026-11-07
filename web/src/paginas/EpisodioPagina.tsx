import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import {
  Cargando,
  Dialogo,
  Interruptor,
  Mensaje,
  TituloSeccion,
} from '../componentes';
import { SelectorEva } from '../componentes/Campos';
import {
  duracionLegible,
  episodioNuevo,
  type AlertaBanderaRoja,
  type Episodio,
} from '../modelos';
import { servicioAnalisis } from '../servicios/analisis';
import { detalleDeError, servicioBitacora } from '../servicios/bitacora';

/** HU-06 (alta), HU-08 (edición), HU-09 (eliminación) y HU-17 (bandera roja). */
export default function EpisodioPagina() {
  const navegar = useNavigate();
  const { id } = useParams<{ id: string }>();
  const esEdicion = id !== undefined && id !== 'nuevo';

  const [ep, setEp] = useState<Episodio | null>(esEdicion ? null : episodioNuevo());
  const [sigueEnCurso, setSigueEnCurso] = useState(false);
  const [cargando, setCargando] = useState(esEdicion);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmando, setConfirmando] = useState(false);
  const [alertaRoja, setAlertaRoja] = useState<AlertaBanderaRoja | null>(null);

  useEffect(() => {
    if (!esEdicion) return;
    let vigente = true;

    const cargar = async () => {
      try {
        const cargado = await servicioBitacora.episodioDe(Number(id));
        if (!vigente) return;
        setEp(cargado);
        setSigueEnCurso(cargado.duracion_min === null);
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
  }, [esEdicion, id]);

  const cambiar = <C extends keyof Episodio>(campo: C, valor: Episodio[C]) => {
    setEp((e) => (e === null ? e : { ...e, [campo]: valor }));
  };

  /**
   * Si marca vómitos, se activan las náuseas solas.
   *
   * El backend rechaza vómitos sin náuseas por coherencia clínica. Ajustarlo
   * aquí evita que el paciente reciba un error por algo que el sistema puede
   * deducir solo.
   */
  const cambiarVomitos = (valor: boolean) => {
    setEp((e) =>
      e === null ? e : { ...e, vomitos: valor, nauseas: valor ? true : e.nauseas },
    );
  };

  const guardar = async () => {
    if (ep === null) return;
    setGuardando(true);
    setError(null);

    // El backend rechaza un inicio futuro; se corrige antes de enviarlo para
    // que un desfase de minutos no produzca un error.
    const ahora = new Date();
    const inicio = new Date(ep.inicio);
    const aEnviar: Episodio = {
      ...ep,
      inicio: (inicio > ahora ? ahora : inicio).toISOString(),
      duracion_min: sigueEnCurso ? null : (ep.duracion_min ?? 60),
    };

    try {
      const guardado = await servicioBitacora.guardarEpisodio(aEnviar);
      if (guardado.alerta_bandera_roja) {
        setAlertaRoja(guardado.alerta_bandera_roja);
        setGuardando(false);
        return;
      }
      navegar('/', {
        state: { nota: esEdicion ? 'Episodio actualizado' : 'Episodio guardado' },
      });
    } catch (e) {
      setError(detalleDeError(e));
      setGuardando(false);
    }
  };

  const atenderAlertaRoja = async () => {
    if (alertaRoja) {
      try {
        await servicioAnalisis.confirmarAlertaBanderaRoja(alertaRoja.id);
      } catch {
        // Ignorar si ya fue confirmada previamente
      }
    }
    setAlertaRoja(null);
    navegar('/', {
      state: {
        nota: 'Episodio registrado. Por favor busca atención médica de urgencias.',
      },
    });
  };

  const eliminar = async () => {
    if (ep?.id == null) return;
    setConfirmando(false);
    setGuardando(true);
    try {
      await servicioBitacora.eliminarEpisodio(ep.id);
      navegar('/', { state: { nota: 'Episodio eliminado' } });
    } catch (e) {
      setError(detalleDeError(e));
      setGuardando(false);
    }
  };

  if (cargando) return <div className="pagina"><Cargando /></div>;

  if (ep === null) {
    return (
      <div className="pagina">
        <Mensaje tipo="error">{error ?? 'No se pudo cargar el episodio.'}</Mensaje>
      </div>
    );
  }

  return (
    <div className="pagina">
      <div className="fila-separada" style={{ marginBottom: 'var(--esp-md)' }}>
        <button type="button" className="boton-texto" onClick={() => navegar(-1)}>
          ← Volver
        </button>
        {esEdicion && (
          <button
            type="button"
            className="boton-texto"
            style={{ color: 'var(--error)' }}
            disabled={guardando}
            onClick={() => setConfirmando(true)}
          >
            Eliminar episodio
          </button>
        )}
      </div>

      <h1>{esEdicion ? 'Editar episodio' : 'Nuevo episodio'}</h1>

      <TituloSeccion>Cuándo empezó</TituloSeccion>
      <label className="tarjeta" style={{ display: 'block' }}>
        <span className="campo-etiqueta">Inicio</span>
        <input
          type="datetime-local"
          value={paraInput(ep.inicio)}
          max={paraInput(new Date().toISOString())}
          disabled={guardando}
          onChange={(e) => {
            if (e.target.value === '') return;
            cambiar('inicio', new Date(e.target.value).toISOString());
          }}
        />
      </label>

      <TituloSeccion>Cuánto duró</TituloSeccion>
      <div className="tarjeta-lista">
        <Interruptor
          titulo="Todavía me duele"
          detalle="Puedes volver después y completar la duración."
          valor={sigueEnCurso}
          desactivado={guardando}
          onCambio={setSigueEnCurso}
        />
        {!sigueEnCurso && (
          <div className="celda">
            <div className="fila-separada">
              <span>Duración</span>
              <span
                className="mono"
                style={{ color: 'var(--primario)', fontWeight: 600 }}
              >
                {duracionLegible(ep.duracion_min ?? 60)}
              </span>
            </div>
            <input
              type="range"
              min={15}
              max={1440}
              step={15}
              value={ep.duracion_min ?? 60}
              disabled={guardando}
              onChange={(e) => cambiar('duracion_min', Number(e.target.value))}
            />
          </div>
        )}
      </div>

      <TituloSeccion ayuda="Escala EVA, de 1 (muy leve) a 10 (el peor imaginable).">
        Intensidad
      </TituloSeccion>
      <SelectorEva
        valor={ep.intensidad}
        onCambio={(v) => cambiar('intensidad', v)}
      />

      <TituloSeccion ayuda="¿El dolor alcanzó el pico máximo en menos de 1 minuto?">
        Forma de comienzo
      </TituloSeccion>
      <div className="tarjeta-lista">
        <Interruptor
          titulo="Inicio repentino / súbito"
          detalle="El dolor comenzó con intensidad explosiva en cuestión de segundos o minutos."
          valor={ep.inicio_subito ?? false}
          desactivado={guardando}
          onCambio={(v) => cambiar('inicio_subito', v)}
        />
      </div>

      {ep.intensidad === 10 && ep.inicio_subito && (
        <div style={{ marginTop: 'var(--esp-sm)' }}>
          <Mensaje tipo="error">
            <strong>Atención:</strong> Has indicado intensidad máxima (10/10) e inicio súbito. Esto constituye un signo de alarma clínica prioritaria (Cefalea en trueno / Bandera Roja).
          </Mensaje>
        </div>
      )}

      <TituloSeccion>Síntomas que acompañaron</TituloSeccion>
      <div className="tarjeta-lista">
        <Interruptor
          titulo="Náuseas"
          detalle={ep.vomitos ? 'Implícitas si hubo vómitos.' : undefined}
          valor={ep.nauseas}
          // Con vómitos marcados, las náuseas quedan fijas.
          desactivado={guardando || ep.vomitos}
          onCambio={(v) => cambiar('nauseas', v)}
        />
        <Interruptor
          titulo="Vómitos"
          valor={ep.vomitos}
          desactivado={guardando}
          onCambio={cambiarVomitos}
        />
        <Interruptor
          titulo="Sensibilidad a la luz"
          valor={ep.sensibilidad_luz}
          desactivado={guardando}
          onCambio={(v) => cambiar('sensibilidad_luz', v)}
        />
        <Interruptor
          titulo="Sensibilidad al sonido"
          valor={ep.sensibilidad_sonido}
          desactivado={guardando}
          onCambio={(v) => cambiar('sensibilidad_sonido', v)}
        />
      </div>

      <TituloSeccion>Observación</TituloSeccion>
      <textarea
        value={ep.observacion}
        maxLength={500}
        disabled={guardando}
        placeholder="Algo que quieras recordar: dónde estabas, qué hiciste antes, qué te alivió…"
        onChange={(e) => cambiar('observacion', e.target.value)}
      />

      {error !== null && (
        <div style={{ marginTop: 'var(--esp-md)' }}>
          <Mensaje tipo="error">{error}</Mensaje>
        </div>
      )}

      <button
        type="button"
        className="boton boton-ancho"
        style={{ marginTop: 'var(--esp-lg)' }}
        disabled={guardando}
        onClick={guardar}
      >
        {guardando ? (
          <span className="girando" aria-hidden="true" />
        ) : esEdicion ? (
          'Actualizar episodio'
        ) : (
          'Guardar episodio'
        )}
      </button>

      {confirmando && (
        <Dialogo
          titulo="¿Eliminar este episodio?"
          mensaje="Se borra de forma permanente y deja de contar para el análisis."
          onAceptar={eliminar}
          onCancelar={() => setConfirmando(false)}
        />
      )}

      {alertaRoja !== null && (
        <Dialogo
          titulo="ALERTA MÉDICA PRIORITARIA (Bandera Roja)"
          mensaje={alertaRoja.mensaje}
          textoAceptar="Entendido, buscaré atención"
          onAceptar={() => void atenderAlertaRoja()}
          onCancelar={() => setAlertaRoja(null)}
        />
      )}
    </div>
  );
}

/** ISO a lo que espera datetime-local, en hora local y sin zona. */
function paraInput(iso: string): string {
  const d = new Date(iso);
  const p = (n: number) => `${n}`.padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`;
}
