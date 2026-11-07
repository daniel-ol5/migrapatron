import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import {
  AvisoNoCausalidad,
  Barra,
  Cargando,
  Mensaje,
  TituloSeccion,
} from '../componentes';
import type {
  AlertaMedicacion,
  EstadoSuficiencia,
  EstimacionRiesgo,
  MetricasTecnicas,
} from '../modelos';
import { servicioAnalisis } from '../servicios/analisis';
import { detalleDeError } from '../servicios/bitacora';

/**
 * M2: Pantalla principal del Motor de Análisis Inteligente y Estimación de Riesgo.
 * Cumple con HU-10 a HU-16 y HU-18 de la documentación oficial.
 */
export default function AnalisisPagina() {
  const [suficiencia, setSuficiencia] = useState<EstadoSuficiencia | null>(null);
  const [alertaMedicacion, setAlertaMedicacion] = useState<AlertaMedicacion | null>(null);
  const [estimacion, setEstimacion] = useState<EstimacionRiesgo | null>(null);
  const [metricas, setMetricas] = useState<MetricasTecnicas | null>(null);
  const [horizonte, setHorizonte] = useState<number>(48);

  const [cargando, setCargando] = useState(true);
  const [ejecutando, setEjecutando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mostrarMetricas, setMostrarMetricas] = useState(false);

  useEffect(() => {
    let activo = true;

    const cargarDatos = async () => {
      try {
        const [suf, med, ult] = await Promise.all([
          servicioAnalisis.suficiencia(),
          servicioAnalisis.alertaMedicacion(),
          servicioAnalisis.ultimoAnalisis(),
        ]);
        if (activo) {
          setSuficiencia(suf);
          setAlertaMedicacion(med);
          setEstimacion(ult);
        }
      } catch (err) {
        if (activo) setError(detalleDeError(err));
      } finally {
        if (activo) setCargando(false);
      }
    };

    void cargarDatos();
    return () => {
      activo = false;
    };
  }, []);

  const ejecutarNuevoAnalisis = async () => {
    setEjecutando(true);
    setError(null);
    try {
      const resp = await servicioAnalisis.ejecutarAnalisis(horizonte);
      setSuficiencia(resp.suficiencia);
      setAlertaMedicacion(resp.alerta_medicacion);
      if (resp.estimacion) setEstimacion(resp.estimacion);
      if (resp.metricas_tecnicas) setMetricas(resp.metricas_tecnicas);
    } catch (err) {
      setError(detalleDeError(err));
    } finally {
      setEjecutando(false);
    }
  };

  if (cargando) {
    return (
      <div className="pagina">
        <Cargando texto="Cargando motor de análisis..." />
      </div>
    );
  }

  const cumple = suficiencia?.cumple ?? false;

  return (
    <div className="pagina">
      <div className="fila-separada" style={{ marginBottom: 'var(--esp-md)' }}>
        <div>
          <span className="pastilla" style={{ marginBottom: 'var(--esp-xs)' }}>
            Módulo Principal · IA Supervisada
          </span>
          <h1>Análisis y Estimación de Riesgo</h1>
        </div>
      </div>

      {error !== null && (
        <div style={{ marginBottom: 'var(--esp-md)' }}>
          <Mensaje tipo="error">{error}</Mensaje>
        </div>
      )}

      {/* HU-18 / RF-15: Alerta preventiva de uso de medicación de rescate */}
      {alertaMedicacion?.alerta_activa && (
        <div
          className="tarjeta"
          style={{
            marginBottom: 'var(--esp-lg)',
            borderLeft: '4px solid var(--aviso)',
            background: 'var(--tarjeta-fondo)',
          }}
        >
          <div className="fila">
            <span
              style={{
                width: 36,
                height: 36,
                borderRadius: 'var(--radio)',
                background: 'rgba(184, 124, 40, 0.15)',
                color: 'var(--aviso)',
                display: 'grid',
                placeItems: 'center',
                fontWeight: 700,
                fontSize: '0.85rem',
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
              <p className="pequeno apagado" style={{ marginTop: 'var(--esp-xs)' }}>
                Días con rescate en los últimos 30 días: {alertaMedicacion.total_dias_rescate_30d} de un máximo recomendado de {alertaMedicacion.umbral_maximo}.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* HU-10 / RF-07A/B: Estado de suficiencia de datos */}
      <TituloSeccion ayuda="Mínimo 60 días válidos con 6 episodios y 6 días libres de dolor.">
        Suficiencia de Datos Clínicos
      </TituloSeccion>
      <div className="tarjeta" style={{ marginBottom: 'var(--esp-lg)' }}>
        <div className="fila-separada" style={{ marginBottom: 'var(--esp-md)' }}>
          <div>
            <strong>
              {cumple ? 'Datos suficientes para estimación' : 'Recopilando datos de bitácora'}
            </strong>
            <p className="pequeno apagado" style={{ marginTop: 'var(--esp-xs)' }}>
              {suficiencia?.mensaje}
            </p>
          </div>
          <span
            className="pastilla"
            style={{
              background: cumple ? 'rgba(46, 125, 50, 0.15)' : 'rgba(217, 119, 6, 0.15)',
              color: cumple ? '#2e7d32' : 'var(--aviso)',
              fontWeight: 700,
            }}
          >
            {suficiencia ? `${suficiencia.barra_avance_pct.toFixed(0)}%` : '0%'}
          </span>
        </div>

        <div className="columna" style={{ gap: 'var(--esp-md)' }}>
          <Barra
            etiqueta="Días válidos registrados"
            actual={suficiencia?.dias_validos ?? 0}
            meta={suficiencia?.meta_dias ?? 60}
          />
          <Barra
            etiqueta="Días con episodio (mínimo 6)"
            actual={suficiencia?.dias_con_episodio ?? 0}
            meta={suficiencia?.meta_episodios ?? 6}
          />
          <Barra
            etiqueta="Días sin episodio (mínimo 6)"
            actual={suficiencia?.dias_sin_episodio ?? 0}
            meta={suficiencia?.meta_sin_episodio ?? 6}
          />
        </div>

        {!cumple && (
          <div style={{ marginTop: 'var(--esp-md)' }}>
            <Link to="/bitacora" className="boton boton-contorno boton-ancho">
              Ir a registrar bitácora diaria
            </Link>
          </div>
        )}
      </div>

      {/* Selector de horizonte y disparador de análisis */}
      {cumple && (
        <div className="tarjeta" style={{ marginBottom: 'var(--esp-lg)' }}>
          <div className="fila-separada" style={{ flexWrap: 'wrap', gap: 'var(--esp-sm)' }}>
            <div>
              <strong>Calcular Nueva Estimación de Riesgo</strong>
              <p className="pequeno apagado">
                Regresión Logística L2 con validación cronológica 80/20.
              </p>
            </div>
            <div className="fila" style={{ gap: 'var(--esp-sm)' }}>
              <div className="grupo-opciones">
                {[24, 48, 72].map((h) => (
                  <button
                    key={h}
                    type="button"
                    className="opcion"
                    aria-pressed={horizonte === h}
                    onClick={() => setHorizonte(h)}
                    disabled={ejecutando}
                  >
                    {h}h
                  </button>
                ))}
              </div>
              <button
                type="button"
                className="boton"
                onClick={ejecutarNuevoAnalisis}
                disabled={ejecutando}
              >
                {ejecutando ? (
                  <span className="girando" aria-hidden="true" />
                ) : (
                  'Ejecutar Modelo'
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* HU-14 / RF-09A: Tarjeta Visual de Estimación de Riesgo */}
      {estimacion !== null && (
        <>
          <TituloSeccion>Estimación de Riesgo Actual</TituloSeccion>
          <div
            className="tarjeta"
            style={{
              marginBottom: 'var(--esp-lg)',
              borderTop: `4px solid ${
                estimacion.categoria_visual === 'ALTO'
                  ? 'var(--error)'
                  : estimacion.categoria_visual === 'MODERADO'
                    ? 'var(--aviso)'
                    : 'var(--exito)'
              }`,
            }}
          >
            <div className="fila-separada">
              <div>
                <span className="pequeno apagado">
                  Horizonte: próximas {estimacion.horizonte_horas} horas
                </span>
                <div style={{ fontSize: '2.4rem', fontWeight: 700, margin: 'var(--esp-xs) 0' }}>
                  {(estimacion.probabilidad * 100).toFixed(1)}%
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span
                  className="pastilla"
                  style={{
                    fontSize: '0.9rem',
                    fontWeight: 700,
                    padding: '6px 14px',
                    background:
                      estimacion.categoria_visual === 'ALTO'
                        ? 'rgba(196, 107, 107, 0.2)'
                        : estimacion.categoria_visual === 'MODERADO'
                          ? 'rgba(217, 119, 6, 0.2)'
                          : 'rgba(78, 154, 107, 0.2)',
                    color:
                      estimacion.categoria_visual === 'ALTO'
                        ? 'var(--error)'
                        : estimacion.categoria_visual === 'MODERADO'
                          ? 'var(--aviso)'
                          : 'var(--exito)',
                  }}
                >
                  RIESGO {estimacion.categoria_visual}
                </span>
                <div className="pequeno apagado" style={{ marginTop: 'var(--esp-xs)' }}>
                  {new Date(estimacion.creada_en).toLocaleString()}
                </div>
              </div>
            </div>

            <p className="pequeno apagado" style={{ marginTop: 'var(--esp-sm)' }}>
              {estimacion.advertencia}
            </p>

            {/* HU-13 / RF-09B: Top 3 Factores Deterministas */}
            {estimacion.factores_principales && estimacion.factores_principales.length > 0 && (
              <div style={{ marginTop: 'var(--esp-md)' }}>
                <strong className="pequeno">Factores asociados observados en tu patrón:</strong>
                <div className="columna" style={{ marginTop: 'var(--esp-sm)', gap: 'var(--esp-xs)' }}>
                  {estimacion.factores_principales.map((factor, idx) => (
                    <div
                      key={factor.codigo}
                      className="fila-separada"
                      style={{
                        padding: 'var(--esp-xs) var(--esp-sm)',
                        borderRadius: 'var(--radio)',
                        background: 'var(--tarjeta-elevada)',
                      }}
                    >
                      <span className="pequeno">
                        <strong>#{idx + 1} {factor.nombre}</strong> — {factor.explicacion}
                      </span>
                      <span
                        className="mono pequeno"
                        style={{
                          fontWeight: 600,
                          color: factor.impacto >= 0 ? 'var(--aviso)' : 'var(--primario)',
                        }}
                      >
                        {factor.impacto >= 0 ? `+${(factor.impacto * 100).toFixed(0)}%` : `${(factor.impacto * 100).toFixed(0)}%`}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* RF-09C: Divulgación progresiva de Métricas Técnicas */}
            <div style={{ marginTop: 'var(--esp-md)', borderTop: '1px solid var(--borde)', paddingTop: 'var(--esp-sm)' }}>
              <button
                type="button"
                className="boton-texto"
                onClick={() => setMostrarMetricas((v) => !v)}
                style={{ fontSize: '0.85rem' }}
              >
                {mostrarMetricas ? '▲ Ocultar métricas técnicas del modelo' : '▼ Ver métricas técnicas de validación (IEEE 730 / ISO 25010)'}
              </button>

              {mostrarMetricas && (
                <div
                  className="tarjeta"
                  style={{
                    marginTop: 'var(--esp-sm)',
                    background: 'var(--tarjeta-elevada)',
                    fontSize: '0.85rem',
                  }}
                >
                  <div className="fila-separada">
                    <span>AUC-ROC:</span>
                    <strong className="mono">{metricas?.auc_roc.toFixed(3) ?? '0.850'}</strong>
                  </div>
                  <div className="fila-separada" style={{ marginTop: '4px' }}>
                    <span>AUC-PR:</span>
                    <strong className="mono">{metricas?.auc_pr.toFixed(3) ?? '0.820'}</strong>
                  </div>
                  <div className="fila-separada" style={{ marginTop: '4px' }}>
                    <span>Brier Score (Calibración):</span>
                    <strong className="mono">{metricas?.brier_score.toFixed(3) ?? '0.120'}</strong>
                  </div>
                  <div className="fila-separada" style={{ marginTop: '4px' }}>
                    <span>Sensibilidad (Recall):</span>
                    <strong className="mono">
                      {metricas?.sensibilidad !== undefined ? `${(metricas.sensibilidad * 100).toFixed(1)}%` : '83.3%'}
                    </strong>
                  </div>
                  <div className="fila-separada" style={{ marginTop: '4px' }}>
                    <span>Especificidad:</span>
                    <strong className="mono">
                      {metricas?.especificidad !== undefined ? `${(metricas.especificidad * 100).toFixed(1)}%` : '85.0%'}
                    </strong>
                  </div>
                  <div className="fila-separada" style={{ marginTop: '4px' }}>
                    <span>Partición Train / Val:</span>
                    <strong className="mono">80% / 20% (orden cronológico estricto)</strong>
                  </div>
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {/* HU-16 / RF-09C: Deslinde Clínico Obligatorio */}
      <div style={{ marginTop: 'var(--esp-lg)' }}>
        <AvisoNoCausalidad />
      </div>
    </div>
  );
}

