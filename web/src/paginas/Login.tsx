import { useState } from 'react';
import { Link } from 'react-router-dom';

import { Mensaje } from '../componentes';
import { useSesion } from '../estado/contextoSesion';

/** HU-02. Inicio de sesión. */
export default function Login() {
  const { ingresar, ocupado } = useSesion();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [verPassword, setVerPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const enviar = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email.includes('@') || !email.includes('.')) {
      setError('Ese email no parece válido.');
      return;
    }
    if (password === '') {
      setError('Escribe tu contraseña.');
      return;
    }

    const mensaje = await ingresar(email, password);
    if (mensaje !== null) setError(mensaje);
  };

  return (
    <div className="centrado">
      <div className="panel-acceso">
        <div style={{ textAlign: 'center', marginBottom: 'var(--esp-xl)' }}>
          <div
            style={{
              width: 56,
              height: 56,
              margin: '0 auto var(--esp-md)',
              display: 'grid',
              placeItems: 'center',
              borderRadius: 16,
              background: 'var(--tarjeta-alta)',
              border: '1px solid var(--borde)',
              fontSize: '1.5rem',
            }}
            aria-hidden="true"
          >
            ◉
          </div>
          <h1>MigraPatrón</h1>
          <p className="pequeno apagado">Tu diario de migraña</p>
        </div>

        <form onSubmit={enviar} noValidate>
          <h2 style={{ marginBottom: 'var(--esp-xs)' }}>Entrar</h2>
          <p className="pequeno apagado" style={{ marginBottom: 'var(--esp-lg)' }}>
            Tu diario es privado y solo tú lo ves.
          </p>

          <label className="campo">
            <span className="campo-etiqueta">Email</span>
            <input
              type="email"
              autoComplete="email"
              value={email}
              disabled={ocupado}
              onChange={(e) => setEmail(e.target.value)}
            />
          </label>

          <label className="campo">
            <span className="campo-etiqueta">Contraseña</span>
            <div style={{ position: 'relative' }}>
              <input
                type={verPassword ? 'text' : 'password'}
                autoComplete="current-password"
                value={password}
                disabled={ocupado}
                onChange={(e) => setPassword(e.target.value)}
                style={{ paddingRight: 48 }}
              />
              <button
                type="button"
                onClick={() => setVerPassword((v) => !v)}
                aria-label={verPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                style={{
                  position: 'absolute',
                  right: 6,
                  top: 5,
                  width: 36,
                  height: 34,
                  border: 0,
                  background: 'none',
                  color: 'var(--apagado)',
                  cursor: 'pointer',
                }}
              >
                {verPassword ? '◡' : '◉'}
              </button>
            </div>
          </label>

          {error !== null && (
            <div style={{ marginBottom: 'var(--esp-md)' }}>
              <Mensaje tipo="error">{error}</Mensaje>
            </div>
          )}

          <button type="submit" className="boton boton-ancho" disabled={ocupado}>
            {ocupado ? <span className="girando" aria-hidden="true" /> : 'Entrar'}
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: 'var(--esp-md)' }}>
          <Link to="/registro" className="boton-texto">
            No tengo cuenta, quiero crear una
          </Link>
        </p>
      </div>
    </div>
  );
}
