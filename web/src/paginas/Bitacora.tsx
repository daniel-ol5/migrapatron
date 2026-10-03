import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import {
  Cargando,
  Dialogo,
  EstadoVacio,
  Interruptor,
  Mensaje,
  TituloSeccion,
} from '../componentes';
import {
  CampoContador,
  CampoDeslizador,
  CampoEscala,
  CampoOpciones,
} from '../componentes/Campos';
import { useSesion } from '../estado/contextoSesion';
import {
  comoFecha,
  factoresCompletos,
  OPCIONES_CICLO,
  OPCIONES_HIDRATACION,
  registroVacio,
  TOTAL_FACTORES,
  type ContextoMenstrual,
  type Hidratacion,
  type RegistroDiario,
} from '../modelos';
import { detalleDeError, servicioBitacora } from '../servicios/bitacora';

/**
 * HU-05 (alta), HU-08 (edición) y HU-09 (eliminación) de la bitácora.
 *
 * Al cargarse busca si ese día ya tiene registro. Si existe entra en modo
 * edición, porque la unicidad (usuario, fecha) haría fallar un alta. El
 * paciente nunca ve ese error: ve el formulario con sus valores cargados.
 */
export default function Bitacora() {
  const navegar = useNavigate();
  const [params] = useSearchParams();
  const { usuario } = useSesion();

  const fecha = params.get('fecha') ?? comoFecha(new Date());

  const [registro, setRegistro] = useState<RegistroDiario | null>(null);
  const [cargando, setCargando] = useState(true);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmando, setConfirmando] = useState(false);

  useEffect(() => {
    let vigente = true;

    const cargar = async () => {
      setCargando(true);
      setError(null);
      try {
        const existente = await servicioBitacora.bitacoraDe(fecha);
        if (!vigente) return;
        const horaPreferida = (
          usuario?.perfil.hora_corte_preferida ?? '22:00:00'
        ).slice(0, 5);
        setRegistro(existente ?? registroVacio(fecha, horaPreferida));
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
  }, [fecha, usuario]);

  const cambiar = <C extends keyof RegistroDiario>(
    campo: C,
    valor: RegistroDiario[C],
  ) => {
    setRegistro((r) => (r === null ? r : { ...r, [campo]: valor }));
  };

  const guardar = async () => {
    if (registro === null) return;
    setGuardando(true);
    setError(null);
    try {
      await servicioBitacora.guardarBitacora(registro);
      navegar('/', { state: { nota: 'Día guardado' } });
    } catch (e) {
      setError(detalleDeError(e));
    } finally {
      setGuardando(false);
    }
  };

  const eliminar = async () => {
    if (registro?.id === null || registro === null) return;
    setConfirmando(false);
    setGuardando(true);
    try {
      await servicioBitacora.eliminarBitacora(registro.id!);
      navegar('/', { state: { nota: 'Día eliminado' } });
    } catch (e) {
      setError(detalleDeError(e));
      setGuardando(false);
    }
  };

  if (cargando) return <div className="pagina"><Cargando /></div>;

  if (registro === null) {
    return (
      <div className="pagina">
        <EstadoVacio
          icono="⚠"
          titulo="No se pudo cargar el día"
          detalle={error ?? undefined}
          accion={
            <button
              type="button"
              className="boton boton-contorno"
              onClick={() => navegar(0)}
            >
              Reintentar
            </button>
          }
        />
      </div>
    );
  }

  const esEdicion = registro.id !== null;
  const completos = factoresCompletos(registro);
  const faltan = TOTAL_FACTORES - completos;

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
            Eliminar este día
          </button>
        )}
      </div>

      <h1>{esEdicion ? 'Editar el día' : 'Registrar el día'}</h1>

      <div className="tarjeta" style={{ marginTop: 'var(--esp-md)' }}>
        <div className="fila-separada">
          <div>
            <strong>{fechaLegible(registro.fecha)}</strong>
            <div className="pequeno apagado">
              {completos} de {TOTAL_FACTORES} factores
            </div>
          </div>
          <span
            className="mono"
            style={{
              color: completos === TOTAL_FACTORES ? 'var(--exito)' : 'var(--apagado)',
              fontWeight: 700,
            }}
          >
            {Math.round((completos / TOTAL_FACTORES) * 100)}%
          </span>
        </div>
      </div>

      <TituloSeccion ayuda="A qué hora cierras tu día. El análisis la usa para saber qué factores ocurrieron antes de un episodio.">
        Hora de corte
      </TituloSeccion>
      <label className="tarjeta" style={{ display: 'block' }}>
        <span className="campo-etiqueta">Cierro mi día a las</span>
        <input
          type="time"
          value={registro.hora_corte}
          disabled={guardando}
          onChange={(e) => cambiar('hora_corte', e.target.value)}
        />
      </label>

      <TituloSeccion>Sueño y alimentación</TituloSeccion>
      <CampoDeslizador
        etiqueta="Horas de sueño"
        valor={registro.horas_sueno}
        maximo={14}
        paso={0.5}
        sufijo="h"
        decimales
        onCambio={(v) => cambiar('horas_sueno', v)}
      />
      <CampoOpciones<Exclude<Hidratacion, ''>>
        etiqueta="Hidratación"
        opciones={
          OPCIONES_HIDRATACION as { valor: Exclude<Hidratacion, ''>; texto: string }[]
        }
        valor={registro.hidratacion}
        onCambio={(v) => cambiar('hidratacion', v)}
      />
      <CampoContador
        etiqueta="Comidas que te saltaste"
        valor={registro.comida_omitida}
        maximo={3}
        onCambio={(v) => cambiar('comida_omitida', v)}
      />
      <CampoContador
        etiqueta="Tazas de café o té"
        valor={registro.cafeina_tazas}
        maximo={10}
        onCambio={(v) => cambiar('cafeina_tazas', v)}
      />

      <TituloSeccion>Estrés y actividad</TituloSeccion>
      <CampoEscala
        etiqueta="Estrés percibido"
        valor={registro.estres}
        minimo={1}
        maximo={5}
        extremos={['Tranquilo', 'Muy estresado']}
        onCambio={(v) => cambiar('estres', v)}
      />
      <CampoDeslizador
        etiqueta="Horas frente a pantallas"
        valor={registro.horas_pantalla}
        maximo={16}
        paso={0.5}
        sufijo="h"
        decimales
        onCambio={(v) => cambiar('horas_pantalla', v)}
      />
      <CampoDeslizador
        etiqueta="Minutos de actividad física"
        valor={registro.minutos_actividad}
        maximo={180}
        paso={5}
        sufijo="min"
        onCambio={(v) => cambiar('minutos_actividad', v)}
      />

      <TituloSeccion>Contexto clínico</TituloSeccion>
      {usuario?.perfil.registra_ciclo_menstrual === true && (
        <CampoOpciones<Exclude<ContextoMenstrual, ''>>
          etiqueta="Contexto menstrual"
          opciones={
            OPCIONES_CICLO as {
              valor: Exclude<ContextoMenstrual, ''>;
              texto: string;
            }[]
          }
          valor={registro.contexto_menstrual}
          onCambio={(v) => cambiar('contexto_menstrual', v)}
        />
      )}
      <div className="tarjeta-lista">
        <Interruptor
          titulo="Tomé medicación de rescate"
          detalle="Tu médico necesita ver con qué frecuencia la usas."
          valor={registro.medicacion_rescate}
          desactivado={guardando}
          onCambio={(v) => cambiar('medicacion_rescate', v)}
        />
        <Interruptor
          titulo="Tuve sensaciones premonitorias"
          detalle="Bostezos, antojos, irritabilidad, cuello tenso."
          valor={registro.sensaciones_premonitorias}
          desactivado={guardando}
          onCambio={(v) => cambiar('sensaciones_premonitorias', v)}
        />
      </div>

      {error !== null && (
        <div style={{ marginTop: 'var(--esp-md)' }}>
          <Mensaje tipo="error">{error}</Mensaje>
        </div>
      )}

      <div style={{ marginTop: 'var(--esp-lg)' }}>
        {faltan > 0 && (
          <p
            className="pequeno apagado"
            style={{ textAlign: 'center', marginBottom: 'var(--esp-sm)' }}
          >
            {faltan === 1
              ? 'Falta 1 factor para que el día cuente en el análisis.'
              : `Faltan ${faltan} factores para que el día cuente en el análisis.`}
          </p>
        )}
        <button
          type="button"
          className="boton boton-ancho"
          disabled={guardando}
          onClick={guardar}
        >
          {guardando ? (
            <span className="girando" aria-hidden="true" />
          ) : esEdicion ? (
            'Actualizar'
          ) : (
            'Guardar el día'
          )}
        </button>
      </div>

      {confirmando && (
        <Dialogo
          titulo="¿Eliminar este día?"
          mensaje="Se borran los factores que registraste. Los episodios de ese día se conservan."
          onAceptar={eliminar}
          onCancelar={() => setConfirmando(false)}
        />
      )}
    </div>
  );
}

const MESES = [
  'enero',
  'febrero',
  'marzo',
  'abril',
  'mayo',
  'junio',
  'julio',
  'agosto',
  'septiembre',
  'octubre',
  'noviembre',
  'diciembre',
];

function fechaLegible(iso: string): string {
  const [a, m, d] = iso.split('-').map(Number);
  const hoy = new Date();
  if (a === hoy.getFullYear() && m === hoy.getMonth() + 1 && d === hoy.getDate()) {
    return 'Hoy';
  }
  return `${d} de ${MESES[m - 1]} de ${a}`;
}
