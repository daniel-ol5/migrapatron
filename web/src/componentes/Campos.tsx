/**
 * Campos del formulario de bitácora.
 *
 * Todos aceptan y devuelven `null`, porque «sin registrar» es un estado
 * legítimo y distinto de cero: dormir 0 horas no es lo mismo que no haber
 * anotado cuánto dormiste, y el análisis de M2 los trata distinto.
 */

/** Deslizador para un valor continuo, con botón para volver a «sin registrar». */
export function CampoDeslizador({
  etiqueta,
  valor,
  maximo,
  paso = 1,
  sufijo = '',
  decimales = false,
  onCambio,
}: {
  etiqueta: string;
  valor: number | null;
  maximo: number;
  paso?: number;
  sufijo?: string;
  decimales?: boolean;
  onCambio: (v: number | null) => void;
}) {
  const sinDato = valor === null;
  const texto = sinDato
    ? 'Sin registrar'
    : `${decimales ? valor.toFixed(1) : Math.round(valor)} ${sufijo}`.trim();

  return (
    <div className="tarjeta" style={{ marginBottom: 'var(--esp-sm)' }}>
      <div className="fila-separada">
        <label htmlFor={`d-${etiqueta}`} className="crecer">
          {etiqueta}
        </label>
        <span
          className="mono"
          style={{
            color: sinDato ? 'var(--apagado)' : 'var(--primario)',
            fontWeight: 600,
          }}
        >
          {texto}
        </span>
        {!sinDato && (
          <button
            type="button"
            className="boton-icono"
            onClick={() => onCambio(null)}
            title="Borrar este dato"
            aria-label={`Borrar ${etiqueta}`}
          >
            ⌫
          </button>
        )}
      </div>
      <input
        id={`d-${etiqueta}`}
        type="range"
        min={0}
        max={maximo}
        step={paso}
        value={valor ?? 0}
        onChange={(e) => onCambio(Number(e.target.value))}
      />
    </div>
  );
}

/** Contador con más y menos, para valores pequeños y discretos. */
export function CampoContador({
  etiqueta,
  valor,
  maximo,
  onCambio,
}: {
  etiqueta: string;
  valor: number | null;
  maximo: number;
  onCambio: (v: number | null) => void;
}) {
  return (
    <div className="tarjeta" style={{ marginBottom: 'var(--esp-sm)' }}>
      <div className="fila-separada">
        <span className="crecer">{etiqueta}</span>
        <div className="fila">
          <button
            type="button"
            className="boton-icono"
            disabled={valor === null || valor <= 0}
            onClick={() => onCambio(valor !== null && valor > 0 ? valor - 1 : null)}
            aria-label={`Bajar ${etiqueta}`}
          >
            −
          </button>
          <span
            className="mono"
            style={{
              minWidth: 32,
              textAlign: 'center',
              fontWeight: 700,
              color: valor === null ? 'var(--apagado)' : 'var(--primario)',
            }}
          >
            {valor ?? '–'}
          </span>
          <button
            type="button"
            className="boton-icono"
            disabled={valor !== null && valor >= maximo}
            onClick={() => onCambio((valor ?? -1) + 1)}
            aria-label={`Subir ${etiqueta}`}
          >
            +
          </button>
        </div>
      </div>
    </div>
  );
}

/** Escala discreta de botones. Volver a pulsar el elegido lo deja sin registrar. */
export function CampoEscala({
  etiqueta,
  valor,
  minimo,
  maximo,
  extremos,
  onCambio,
}: {
  etiqueta: string;
  valor: number | null;
  minimo: number;
  maximo: number;
  extremos?: [string, string];
  onCambio: (v: number | null) => void;
}) {
  const numeros = Array.from(
    { length: maximo - minimo + 1 },
    (_, i) => minimo + i,
  );

  return (
    <fieldset
      className="tarjeta"
      style={{ marginBottom: 'var(--esp-sm)', border: '1px solid var(--borde)' }}
    >
      <legend style={{ padding: '0 var(--esp-xs)' }}>{etiqueta}</legend>
      <div className="fila" style={{ gap: 6, marginTop: 'var(--esp-sm)' }}>
        {numeros.map((n) => (
          <button
            key={n}
            type="button"
            className="opcion"
            aria-pressed={valor === n}
            onClick={() => onCambio(valor === n ? null : n)}
            style={{ flex: 1, borderRadius: 'var(--radio)' }}
          >
            {n}
          </button>
        ))}
      </div>
      {extremos !== undefined && (
        <div className="fila-separada" style={{ marginTop: 'var(--esp-xs)' }}>
          <span className="pequeno apagado">{extremos[0]}</span>
          <span className="pequeno apagado">{extremos[1]}</span>
        </div>
      )}
    </fieldset>
  );
}

/** Opciones mutuamente excluyentes. */
export function CampoOpciones<T extends string>({
  etiqueta,
  opciones,
  valor,
  onCambio,
}: {
  etiqueta: string;
  opciones: { valor: T; texto: string }[];
  valor: T | '';
  onCambio: (v: T | '') => void;
}) {
  return (
    <fieldset
      className="tarjeta"
      style={{ marginBottom: 'var(--esp-sm)', border: '1px solid var(--borde)' }}
    >
      <legend style={{ padding: '0 var(--esp-xs)' }}>{etiqueta}</legend>
      <div className="grupo-opciones" style={{ marginTop: 'var(--esp-sm)' }}>
        {opciones.map((o) => (
          <button
            key={o.valor}
            type="button"
            className="opcion"
            aria-pressed={valor === o.valor}
            onClick={() => onCambio(valor === o.valor ? '' : o.valor)}
          >
            {o.texto}
          </button>
        ))}
      </div>
    </fieldset>
  );
}

/**
 * Selector de intensidad EVA 1-10.
 *
 * Usa la rampa cálida de la paleta, nunca el verde azulado de marca.
 */
export function SelectorEva({
  valor,
  onCambio,
}: {
  valor: number;
  onCambio: (v: number) => void;
}) {
  const descripciones: Record<number, string> = {
    1: 'Apenas lo noto',
    2: 'Muy leve',
    3: 'Leve',
    4: 'Molesto',
    5: 'Moderado',
    6: 'Incómodo',
    7: 'Intenso',
    8: 'Muy intenso',
    9: 'Insoportable',
    10: 'El peor imaginable',
  };

  return (
    <div className="tarjeta">
      <div className="fila" style={{ marginBottom: 'var(--esp-md)' }}>
        <span
          className="eva eva-grande"
          style={{
            color: `var(--eva-${valor})`,
            background: `color-mix(in srgb, var(--eva-${valor}) 18%, transparent)`,
          }}
        >
          {valor}
        </span>
        <div>
          <strong style={{ color: `var(--eva-${valor})` }}>
            {descripciones[valor]}
          </strong>
          <div className="pequeno apagado">Intensidad {valor} de 10</div>
        </div>
      </div>

      <div className="fila" style={{ gap: 3 }}>
        {Array.from({ length: 10 }, (_, i) => i + 1).map((n) => (
          <button
            key={n}
            type="button"
            onClick={() => onCambio(n)}
            aria-pressed={valor === n}
            aria-label={`Intensidad ${n}`}
            style={{
              flex: 1,
              height: 38,
              borderRadius: 6,
              cursor: 'pointer',
              fontWeight: 700,
              fontSize: '0.8rem',
              background:
                n <= valor
                  ? `color-mix(in srgb, var(--eva-${n}) 85%, transparent)`
                  : 'var(--tarjeta-alta)',
              color: n <= valor ? '#14181a' : 'var(--apagado)',
              border:
                n === valor
                  ? '1.5px solid var(--texto)'
                  : '1px solid var(--borde)',
            }}
          >
            {n}
          </button>
        ))}
      </div>
    </div>
  );
}
