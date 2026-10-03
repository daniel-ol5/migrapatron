import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import {
  AvisoNoCausalidad,
  Cargando,
  EstadoVacio,
  Mensaje,
  TituloSeccion,
} from '../componentes';
import { useSesion } from '../estado/contextoSesion';
import type { AvisoPrivacidad } from '../modelos';
import { servicioAuth } from '../servicios/auth';
import { detalleDeError } from '../servicios/bitacora';

/**
 * HU-01. Registro con aceptación del aviso de privacidad.
 *
 * La página carga el aviso vigente antes de permitir crear la cuenta, y envía
 * su versión junto al registro. Si el aviso cambió mientras la persona llenaba
 * el formulario, el backend rechaza el alta: aceptar un texto que ya no rige
 * no es consentir.
 */
export default function Registro() {
  const { registrar, ocupado } = useSesion();

  const [aviso, setAviso] = useState<AvisoPrivacidad | null>(null);
  const [cargandoAviso, setCargandoAviso] = useState(true);
  const [errorAviso, setErrorAviso] = useState<string | null>(null);
  const [verAvisoCompleto, setVerAvisoCompleto] = useState(false);

  const [nombre, setNombre] = useState('');
  const [apellido, setApellido] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [acepta, setAcepta] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // El estado ya arranca en «cargando», asi que el efecto no necesita
  // reiniciarlo: hacerlo provocaria un render de mas en el montaje.
  const traerAviso = async () => {
    try {
      setAviso(await servicioAuth.avisoVigente());
      setErrorAviso(null);
    } catch (e) {
      setErrorAviso(detalleDeError(e));
    } finally {
      setCargandoAviso(false);
    }
  };

  const reintentar = () => {
    setCargandoAviso(true);
    void traerAviso();
  };

  useEffect(() => {
    void traerAviso();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const enviar = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (nombre.trim() === '' || apellido.trim() === '') {
      setError('El nombre y el apellido son obligatorios.');
      return;
    }
    if (!email.includes('@') || !email.includes('.')) {
      setError('Ese email no parece válido.');
      return;
    }
    if (password.length < 8) {
      setError('La contraseña necesita al menos 8 caracteres.');
      return;
    }
    if (!acepta) {
      setError('Hay que aceptar el aviso de privacidad para crear la cuenta.');
      return;
    }
    if (aviso === null) return;

    const mensaje = await registrar({
      email,
      password,
      nombre,
      apellido,
      versionAviso: aviso.version,
    });
    if (mensaje !== null) setError(mensaje);
  };

  if (cargandoAviso) {
    return (
      <div className="centrado">
        <Cargando texto="Cargando el aviso de privacidad…" />
      </div>
    );
  }

  if (errorAviso !== null || aviso === null) {
    return (
      <div className="centrado">
        <EstadoVacio
          icono="⚠"
          titulo="No se pudo cargar el aviso de privacidad"
          detalle={
            errorAviso ??
            'Sin un aviso publicado no se puede crear una cuenta. ' +
              'Si eres del equipo: falta correr «manage.py seed_privacidad».'
          }
          accion={
            <button type="button" className="boton boton-contorno" onClick={reintentar}>
              Reintentar
            </button>
          }
        />
      </div>
    );
  }

  return (
    <div className="pagina">
      <p style={{ marginBottom: 'var(--esp-md)' }}>
        <Link to="/login" className="boton-texto">
          ← Volver
        </Link>
      </p>

      <h1>Crear cuenta</h1>

      <form onSubmit={enviar} noValidate style={{ marginTop: 'var(--esp-lg)' }}>
        <div className="fila" style={{ alignItems: 'flex-start' }}>
          <label className="campo crecer">
            <span className="campo-etiqueta">Nombre</span>
            <input
              type="text"
              value={nombre}
              disabled={ocupado}
              onChange={(e) => setNombre(e.target.value)}
            />
          </label>
          <label className="campo crecer">
            <span className="campo-etiqueta">Apellido</span>
            <input
              type="text"
              value={apellido}
              disabled={ocupado}
              onChange={(e) => setApellido(e.target.value)}
            />
          </label>
        </div>

        <label className="campo">
          <span className="campo-etiqueta">Email</span>
          <input
            type="email"
            autoComplete="email"
            value={email}
            disabled={ocupado}
            onChange={(e) => setEmail(e.target.value)}
          />
          <span className="campo-ayuda">Con este email vas a entrar.</span>
        </label>

        <label className="campo">
          <span className="campo-etiqueta">Contraseña</span>
          <input
            type="password"
            autoComplete="new-password"
            value={password}
            disabled={ocupado}
            onChange={(e) => setPassword(e.target.value)}
          />
          <span className="campo-ayuda">
            Mínimo 8 caracteres. Evita algo fácil de adivinar.
          </span>
        </label>

        <TituloSeccion>Privacidad</TituloSeccion>

        <div className="tarjeta">
          <h3 style={{ fontSize: '0.98rem' }}>{aviso.titulo}</h3>
          <p
            className="pequeno apagado"
            style={{ margin: 'var(--esp-sm) 0', lineHeight: 1.5 }}
          >
            Tus datos se usan solo para buscar patrones en tu propio diario. No
            se venden, no se comparten y nadie más los ve.
          </p>
          <button
            type="button"
            className="boton-texto"
            style={{ padding: 0 }}
            onClick={() => setVerAvisoCompleto((v) => !v)}
          >
            {verAvisoCompleto ? 'Ocultar el aviso' : 'Leer el aviso completo'}
          </button>

          {verAvisoCompleto && (
            <pre
              style={{
                marginTop: 'var(--esp-md)',
                padding: 'var(--esp-md)',
                background: 'var(--tarjeta-alta)',
                borderRadius: 'var(--radio)',
                maxHeight: 320,
                overflow: 'auto',
                whiteSpace: 'pre-wrap',
                fontFamily: 'var(--fuente)',
                fontSize: '0.84rem',
                lineHeight: 1.55,
                margin: 0,
              }}
            >
              {aviso.contenido}
            </pre>
          )}
        </div>

        <label
          className="casilla"
          style={{ marginTop: 'var(--esp-md)', marginBottom: 'var(--esp-md)' }}
        >
          <input
            type="checkbox"
            checked={acepta}
            disabled={ocupado}
            onChange={(e) => setAcepta(e.target.checked)}
          />
          <span>
            Leí y acepto el aviso de privacidad versión {aviso.version}
            <span className="interruptor-detalle">
              Puedes retirar este consentimiento después, sin perder la cuenta.
            </span>
          </span>
        </label>

        {error !== null && (
          <div style={{ marginBottom: 'var(--esp-md)' }}>
            <Mensaje tipo="error">{error}</Mensaje>
          </div>
        )}

        <button type="submit" className="boton boton-ancho" disabled={ocupado}>
          {ocupado ? (
            <span className="girando" aria-hidden="true" />
          ) : (
            'Crear mi cuenta'
          )}
        </button>
      </form>

      <div style={{ marginTop: 'var(--esp-lg)' }}>
        <AvisoNoCausalidad />
      </div>
    </div>
  );
}
