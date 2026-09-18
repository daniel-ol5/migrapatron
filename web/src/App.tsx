import { BrowserRouter, Link, Navigate, Route, Routes } from 'react-router-dom';
import { almacen } from './core/almacen';
import { AVISO_NO_CAUSALIDAD } from './core/config';
import './App.css';

/**
 * Envuelve las rutas que exigen sesión iniciada.
 * Cuando exista la pantalla de acceso (HU-03), redirige a ella.
 */
function RutaPrivada({ children }: { children: React.ReactNode }) {
  return almacen.haySesion ? <>{children}</> : <Navigate to="/acceso" replace />;
}

function Andamiaje() {
  return (
    <main className="andamiaje">
      <p className="eyebrow">MigraPatrón IA · cliente web</p>
      <h1>El andamiaje está en pie</h1>
      <p>
        El proyecto compila y las rutas funcionan. Las pantallas se construyen
        en el Sprint&nbsp;1: acceso, bitácora diaria y episodios.
      </p>

      <ul className="rutas">
        <li>
          <code>/acceso</code> — iniciar sesión <span>HU-03 · CU-02</span>
        </li>
        <li>
          <code>/bitacora</code> — registrar el día <span>HU-05 · CU-05</span>
        </li>
        <li>
          <code>/episodios</code> — registrar episodio <span>HU-06 · CU-06</span>
        </li>
        <li>
          <code>/hallazgos</code> — patrones explicados <span>HU-15 · CU-10</span>
        </li>
        <li>
          <code>/reporte</code> — resumen clínico <span>HU-18 · CU-13</span>
        </li>
      </ul>

      <p className="aviso">{AVISO_NO_CAUSALIDAD}</p>

      <p className="pie">
        <Link to="/acceso">Ir a acceso</Link>
      </p>
    </main>
  );
}

function PorConstruir({ titulo, historia }: { titulo: string; historia: string }) {
  return (
    <main className="andamiaje">
      <p className="eyebrow">{historia}</p>
      <h1>{titulo}</h1>
      <p>Esta pantalla todavía no está construida.</p>
      <p className="pie">
        <Link to="/">Volver al inicio</Link>
      </p>
    </main>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Andamiaje />} />
        <Route
          path="/acceso"
          element={<PorConstruir titulo="Iniciar sesión" historia="HU-03 · CU-02" />}
        />
        <Route
          path="/bitacora"
          element={
            <RutaPrivada>
              <PorConstruir titulo="Bitácora del día" historia="HU-05 · CU-05" />
            </RutaPrivada>
          }
        />
        <Route
          path="/episodios"
          element={
            <RutaPrivada>
              <PorConstruir titulo="Episodios" historia="HU-06 · CU-06" />
            </RutaPrivada>
          }
        />
        <Route
          path="/hallazgos"
          element={
            <RutaPrivada>
              <PorConstruir titulo="Mis patrones" historia="HU-15 · CU-10" />
            </RutaPrivada>
          }
        />
        <Route
          path="/reporte"
          element={
            <RutaPrivada>
              <PorConstruir titulo="Resumen clínico" historia="HU-18 · CU-13" />
            </RutaPrivada>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
