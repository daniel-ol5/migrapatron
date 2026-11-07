import {
  BrowserRouter,
  Navigate,
  NavLink,
  Outlet,
  Route,
  Routes,
} from 'react-router-dom';

import { Cargando } from './componentes';
import { useSesion } from './estado/contextoSesion';
import { ProveedorSesion } from './estado/SesionContext';
import AnalisisPagina from './paginas/AnalisisPagina';
import Bitacora from './paginas/Bitacora';
import EpisodioPagina from './paginas/EpisodioPagina';
import HistorialPagina from './paginas/HistorialPagina';
import Inicio from './paginas/Inicio';
import Login from './paginas/Login';
import Perfil from './paginas/Perfil';
import Registro from './paginas/Registro';

import './estilos/tokens.css';
import './estilos/base.css';

/**
 * Envuelve las rutas que exigen sesión iniciada.
 *
 * Mientras se resuelve el arranque muestra un cargando, porque redirigir al
 * login antes de saber si hay sesión haría parpadear la pantalla de acceso a
 * quien ya está dentro.
 */
function RutaPrivada() {
  const { fase } = useSesion();

  if (fase === 'cargando') {
    return (
      <div className="centrado">
        <Cargando texto="Entrando…" />
      </div>
    );
  }
  if (fase === 'fuera') return <Navigate to="/login" replace />;

  return (
    <>
      <Cabecera />
      <Outlet />
    </>
  );
}

/** Solo para quien NO tiene sesión: evita volver al login estando dentro. */
function RutaPublica({ children }: { children: React.ReactNode }) {
  const { fase } = useSesion();

  if (fase === 'cargando') {
    return (
      <div className="centrado">
        <Cargando />
      </div>
    );
  }
  if (fase === 'dentro') return <Navigate to="/" replace />;

  return <>{children}</>;
}

function Cabecera() {
  return (
    <header className="cabecera">
      <div className="cabecera-interior">
        <NavLink to="/" className="marca">
          <span aria-hidden="true">◉</span>
          <span>MigraPatrón</span>
        </NavLink>

        <nav className="nav" aria-label="Navegación principal">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `nav-enlace${isActive ? ' activo' : ''}`
            }
          >
            Hoy
          </NavLink>
          <NavLink
            to="/historial"
            className={({ isActive }) =>
              `nav-enlace${isActive ? ' activo' : ''}`
            }
          >
            Historial
          </NavLink>
          <NavLink
            to="/analisis"
            className={({ isActive }) =>
              `nav-enlace${isActive ? ' activo' : ''}`
            }
          >
            Análisis
          </NavLink>
          <NavLink
            to="/perfil"
            className={({ isActive }) =>
              `nav-enlace${isActive ? ' activo' : ''}`
            }
          >
            Perfil
          </NavLink>
        </nav>
      </div>
    </header>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <ProveedorSesion>
        <Routes>
          <Route
            path="/login"
            element={
              <RutaPublica>
                <Login />
              </RutaPublica>
            }
          />
          <Route
            path="/registro"
            element={
              <RutaPublica>
                <Registro />
              </RutaPublica>
            }
          />

          <Route element={<RutaPrivada />}>
            <Route path="/" element={<Inicio />} />
            <Route path="/bitacora" element={<Bitacora />} />
            <Route path="/historial" element={<HistorialPagina />} />
            <Route path="/analisis" element={<AnalisisPagina />} />
            <Route path="/episodio/:id" element={<EpisodioPagina />} />
            <Route path="/perfil" element={<Perfil />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </ProveedorSesion>
    </BrowserRouter>
  );
}
