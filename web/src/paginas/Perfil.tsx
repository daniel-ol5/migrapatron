import { useEffect, useState } from 'react';

import {
  AvisoNoCausalidad,
  Dialogo,
  Interruptor,
  Mensaje,
  TituloSeccion,
} from '../componentes';
import { useNotificacion } from '../componentes/useNotificacion';
import { useSesion } from '../estado/contextoSesion';
import {
  ETIQUETAS_TIPO,
  type EstadoConsentimiento,
  type PerfilClinico,
  type TipoMigrana,
} from '../modelos';
import { servicioAuth } from '../servicios/auth';
import { detalleDeError } from '../servicios/bitacora';

/** HU-04 (perfil y consentimiento), HU-03 (cierre de sesión) y M0.4 (baja). */
export default function Perfil() {
  const { usuario, refrescar, salir, eliminarCuenta, ocupado } = useSesion();
  const { avisar, vista } = useNotificacion();

  const [consentimiento, setConsentimiento] =
    useState<EstadoConsentimiento | null>(null);
  const [editando, setEditando] = useState(false);
  const [confirmando, setConfirmando] = useState<'salir' | 'retirar' | null>(null);
  const [mostrarBaja, setMostrarBaja] = useState(false);

  const cargarConsentimiento = async () => {
    try {
      setConsentimiento(await servicioAuth.consentimiento());
    } catch {
      // Un fallo acá no debe romper la página: el resto del perfil sirve.
    }
  };

  useEffect(() => {
    let vigente = true;

    const traer = async () => {
      try {
        const estado = await servicioAuth.consentimiento();
        if (vigente) setConsentimiento(estado);
      } catch {
        // Un fallo aca no debe romper la pagina: el resto del perfil sirve.
      }
    };

    void traer();
    return () => {
      vigente = false;
    };
  }, []);

  if (usuario === null) return null;

  const cambiarConsentimiento = async (activar: boolean) => {
    if (!activar) {
      setConfirmando('retirar');
      return;
    }
    try {
      const aviso = await servicioAuth.avisoVigente();
      await servicioAuth.cambiarConsentimiento(true, aviso.version);
      await refrescar();
      await cargarConsentimiento();
      avisar('Consentimiento activado');
    } catch (e) {
      avisar(detalleDeError(e), true);
    }
  };

  const retirar = async () => {
    setConfirmando(null);
    try {
      await servicioAuth.cambiarConsentimiento(false);
      await refrescar();
      await cargarConsentimiento();
      avisar('Consentimiento retirado');
    } catch (e) {
      avisar(detalleDeError(e), true);
    }
  };

  return (
    <div className="pagina">
      {vista}

      <div className="fila">
        <span
          style={{
            width: 52,
            height: 52,
            flex: 'none',
            display: 'grid',
            placeItems: 'center',
            borderRadius: '50%',
            background: 'var(--tarjeta-alta)',
            border: '1px solid var(--borde)',
            color: 'var(--primario)',
            fontWeight: 700,
          }}
          aria-hidden="true"
        >
          {iniciales(usuario.nombre, usuario.apellido)}
        </span>
        <div>
          <h1 style={{ fontSize: '1.3rem' }}>{usuario.nombre_completo}</h1>
          <p className="pequeno apagado">{usuario.email}</p>
        </div>
      </div>

      <TituloSeccion>Datos clínicos</TituloSeccion>
      {editando ? (
        <FormularioPerfil
          usuario={usuario}
          onListo={async () => {
            setEditando(false);
            await refrescar();
            avisar('Datos actualizados');
          }}
          onCancelar={() => setEditando(false)}
        />
      ) : (
        <div className="tarjeta-lista">
          <Dato etiqueta="Tipo de migraña" valor={ETIQUETAS_TIPO[usuario.perfil.tipo_migrana]} />
          <Dato
            etiqueta="Años con migraña"
            valor={usuario.perfil.anios_con_migrana?.toString() ?? 'Sin dato'}
          />
          <Dato
            etiqueta="Diagnóstico médico previo"
            valor={usuario.perfil.diagnostico_previo ? 'Sí' : 'No'}
          />
          <Dato
            etiqueta="Hora de corte habitual"
            valor={usuario.perfil.hora_corte_preferida.slice(0, 5)}
          />
          <Dato
            etiqueta="Registro contexto menstrual"
            valor={usuario.perfil.registra_ciclo_menstrual ? 'Sí' : 'No'}
          />
          <button
            type="button"
            className="celda-boton"
            onClick={() => setEditando(true)}
          >
            <span className="fila-separada">
              <span style={{ color: 'var(--primario)' }}>Editar mis datos</span>
              <span className="apagado" aria-hidden="true">
                ›
              </span>
            </span>
          </button>
        </div>
      )}

      <TituloSeccion ayuda="Cada cambio queda registrado con su fecha. El historial no se sobrescribe nunca.">
        Consentimiento
      </TituloSeccion>
      <div className="tarjeta-lista">
        <Interruptor
          titulo="Analizar mis datos"
          detalle={
            usuario.consintio_analisis
              ? 'Buscamos patrones solo en tu propio diario.'
              : 'El análisis está desactivado.'
          }
          valor={usuario.consintio_analisis}
          desactivado={ocupado}
          onCambio={cambiarConsentimiento}
        />

        {consentimiento !== null && consentimiento.historial.length > 0 && (
          <div className="celda">
            <p
              className="pequeno apagado"
              style={{ marginBottom: 'var(--esp-sm)' }}
            >
              Historial
            </p>
            <div className="columna" style={{ gap: 6 }}>
              {consentimiento.historial.slice(0, 8).map((h) => (
                <div key={h.id} className="fila-separada">
                  <span className="pequeno">
                    <span
                      aria-hidden="true"
                      style={{
                        color: h.aceptado ? 'var(--exito)' : 'var(--apagado)',
                      }}
                    >
                      {h.aceptado ? '✓' : '✕'}
                    </span>{' '}
                    {h.aceptado
                      ? `Aceptado (aviso ${h.aviso_version})`
                      : 'Retirado'}
                  </span>
                  <span className="pequeno apagado mono">
                    {fechaHora(h.otorgado_en)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <TituloSeccion>Sesión</TituloSeccion>
      <div className="tarjeta-lista">
        <button
          type="button"
          className="celda-boton"
          disabled={ocupado}
          onClick={() => setConfirmando('salir')}
        >
          Cerrar sesión
        </button>
        <button
          type="button"
          className="celda-boton"
          disabled={ocupado}
          onClick={() => setMostrarBaja(true)}
          style={{ color: 'var(--error)' }}
        >
          Eliminar mi cuenta
          <span className="interruptor-detalle">
            Borra todos tus datos. No se deshace.
          </span>
        </button>
      </div>

      {mostrarBaja && (
        <FormularioBaja
          onCancelar={() => setMostrarBaja(false)}
          onConfirmar={async (password) => {
            const error = await eliminarCuenta(password);
            if (error !== null) {
              avisar(error, true);
              setMostrarBaja(false);
            }
          }}
        />
      )}

      {confirmando === 'salir' && (
        <Dialogo
          titulo="¿Cerrar sesión?"
          mensaje="Tus datos se quedan guardados. Vas a tener que entrar de nuevo."
          textoAceptar="Cerrar sesión"
          onAceptar={() => {
            setConfirmando(null);
            void salir();
          }}
          onCancelar={() => setConfirmando(null)}
        />
      )}

      {confirmando === 'retirar' && (
        <Dialogo
          titulo="¿Retirar el consentimiento?"
          mensaje="Dejaremos de buscar patrones en tus datos. Tus registros se conservan y puedes volver a activarlo cuando quieras."
          textoAceptar="Retirar"
          onAceptar={retirar}
          onCancelar={() => setConfirmando(null)}
        />
      )}

      <div style={{ marginTop: 'var(--esp-lg)' }}>
        <AvisoNoCausalidad />
      </div>
    </div>
  );
}

function Dato({ etiqueta, valor }: { etiqueta: string; valor: string }) {
  return (
    <div className="celda fila-separada">
      <span className="apagado">{etiqueta}</span>
      <span>{valor}</span>
    </div>
  );
}

/** HU-04. Edición del perfil. El email no se edita: identifica la cuenta. */
function FormularioPerfil({
  usuario,
  onListo,
  onCancelar,
}: {
  usuario: { nombre: string; apellido: string; email: string; perfil: PerfilClinico };
  onListo: () => Promise<void>;
  onCancelar: () => void;
}) {
  const [nombre, setNombre] = useState(usuario.nombre);
  const [apellido, setApellido] = useState(usuario.apellido);
  const [anios, setAnios] = useState(
    usuario.perfil.anios_con_migrana?.toString() ?? '',
  );
  const [tipo, setTipo] = useState<TipoMigrana>(usuario.perfil.tipo_migrana);
  const [medicacion, setMedicacion] = useState(usuario.perfil.medicacion_habitual);
  const [diagnostico, setDiagnostico] = useState(usuario.perfil.diagnostico_previo);
  const [ciclo, setCiclo] = useState(usuario.perfil.registra_ciclo_menstrual);
  const [hora, setHora] = useState(usuario.perfil.hora_corte_preferida.slice(0, 5));
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const guardar = async (e: React.FormEvent) => {
    e.preventDefault();
    setGuardando(true);
    setError(null);
    try {
      await servicioAuth.actualizarPerfil({
        nombre,
        apellido,
        clinico: {
          anios_con_migrana: anios === '' ? null : Number(anios),
          tipo_migrana: tipo,
          diagnostico_previo: diagnostico,
          medicacion_habitual: medicacion,
          registra_ciclo_menstrual: ciclo,
          hora_corte_preferida: hora,
        },
      });
      await onListo();
    } catch (err) {
      setError(detalleDeError(err));
    } finally {
      setGuardando(false);
    }
  };

  return (
    <form className="tarjeta" onSubmit={guardar}>
      <div className="fila" style={{ alignItems: 'flex-start' }}>
        <label className="campo crecer">
          <span className="campo-etiqueta">Nombre</span>
          <input value={nombre} onChange={(e) => setNombre(e.target.value)} />
        </label>
        <label className="campo crecer">
          <span className="campo-etiqueta">Apellido</span>
          <input value={apellido} onChange={(e) => setApellido(e.target.value)} />
        </label>
      </div>

      <label className="campo">
        <span className="campo-etiqueta">Email</span>
        <input value={usuario.email} disabled />
        <span className="campo-ayuda">El email no se puede cambiar.</span>
      </label>

      <label className="campo">
        <span className="campo-etiqueta">Tipo de migraña</span>
        <select value={tipo} onChange={(e) => setTipo(e.target.value as TipoMigrana)}>
          {Object.entries(ETIQUETAS_TIPO).map(([valor, texto]) => (
            <option key={valor} value={valor}>
              {texto}
            </option>
          ))}
        </select>
      </label>

      <label className="campo">
        <span className="campo-etiqueta">Años con migraña</span>
        <input
          type="number"
          min={0}
          max={100}
          value={anios}
          onChange={(e) => setAnios(e.target.value)}
        />
      </label>

      <label className="campo">
        <span className="campo-etiqueta">Medicación habitual</span>
        <textarea
          value={medicacion}
          style={{ minHeight: 70 }}
          onChange={(e) => setMedicacion(e.target.value)}
        />
      </label>

      <label className="campo">
        <span className="campo-etiqueta">Hora de corte habitual</span>
        <input type="time" value={hora} onChange={(e) => setHora(e.target.value)} />
      </label>

      <Interruptor
        titulo="Tengo diagnóstico médico"
        valor={diagnostico}
        onCambio={setDiagnostico}
      />
      <Interruptor
        titulo="Quiero registrar contexto menstrual"
        valor={ciclo}
        onCambio={setCiclo}
      />

      {error !== null && (
        <div style={{ margin: 'var(--esp-sm) 0' }}>
          <Mensaje tipo="error">{error}</Mensaje>
        </div>
      )}

      <div className="fila" style={{ marginTop: 'var(--esp-md)' }}>
        <button type="submit" className="boton crecer" disabled={guardando}>
          {guardando ? <span className="girando" aria-hidden="true" /> : 'Guardar'}
        </button>
        <button
          type="button"
          className="boton boton-contorno"
          onClick={onCancelar}
          disabled={guardando}
        >
          Cancelar
        </button>
      </div>
    </form>
  );
}

/** M0.4. Baja de cuenta: contraseña más confirmación escrita. */
function FormularioBaja({
  onConfirmar,
  onCancelar,
}: {
  onConfirmar: (password: string) => Promise<void>;
  onCancelar: () => void;
}) {
  const [password, setPassword] = useState('');
  const [confirmacion, setConfirmacion] = useState('');
  const puede = password !== '' && confirmacion.trim().toUpperCase() === 'ELIMINAR';

  return (
    <div
      className="capa-dialogo"
      role="dialog"
      aria-modal="true"
      aria-label="Eliminar mi cuenta"
    >
      <form
        className="dialogo"
        onSubmit={(e) => {
          e.preventDefault();
          if (puede) void onConfirmar(password);
        }}
      >
        <h3 style={{ color: 'var(--error)' }}>⚠ Eliminar mi cuenta</h3>
        <p className="apagado" style={{ margin: 'var(--esp-md) 0' }}>
          Se borran tu cuenta, tu perfil, tus bitácoras y tus episodios. Esta
          acción no se puede deshacer y no hay forma de recuperar los datos.
        </p>

        <label className="campo">
          <span className="campo-etiqueta">Tu contraseña</span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>

        <label className="campo">
          <span className="campo-etiqueta">Escribe ELIMINAR para confirmar</span>
          <input
            value={confirmacion}
            onChange={(e) => setConfirmacion(e.target.value)}
          />
        </label>

        <div className="columna">
          <button type="submit" className="boton boton-peligro" disabled={!puede}>
            Eliminar mi cuenta definitivamente
          </button>
          <button type="button" className="boton boton-contorno" onClick={onCancelar}>
            Cancelar
          </button>
        </div>
      </form>
    </div>
  );
}

function iniciales(nombre: string, apellido: string): string {
  return `${nombre.at(0) ?? ''}${apellido.at(0) ?? ''}`.toUpperCase();
}

function fechaHora(iso: string): string {
  const d = new Date(iso);
  const p = (n: number) => `${n}`.padStart(2, '0');
  return `${p(d.getDate())}/${p(d.getMonth() + 1)} ${p(d.getHours())}:${p(d.getMinutes())}`;
}
