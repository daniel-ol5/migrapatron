# MigraPatrón IA

Minería de datos explicable para pacientes con migraña.

El sistema analiza el diario personal de un paciente y descubre qué factores se
repitieron antes de sus episodios. **No diagnostica**: encuentra asociaciones en
los datos del propio paciente, las explica con números y con palabras, y prepara
un resumen que el paciente lleva a consulta.

> **Límite del producto.** MigraPatrón no diagnostica, no determina causas y no
> recomienda medicación. Toda pantalla de hallazgos muestra de forma permanente:
> *«Una asociación no demuestra causalidad. Comenta estos resultados con tu médico.»*

Proyecto de la materia **Ingeniería de la Calidad** · metodología SCRUM ·
3 sprints × 3 semanas · 4 integrantes.

---

## Estructura del repositorio

```
Calidad/
├─ backend/     Django 6.1 + DRF + el motor de patrones (Python)
│  └─ apps/
│     ├─ m0_usuarios/   Gestión de Usuarios y Privacidad
│     ├─ m1_bitacora/   Seguimiento y Bitácora Diaria
│     ├─ m2_analisis/   Análisis Inteligente de Datos
│     ├─ m3_reportes/   Explicabilidad y Reportes
│     └─ comun/         Permisos de aislamiento y auditoría
├─ movil/       App Flutter (cliente principal del paciente)
├─ web/         Cliente web React + TypeScript + Vite
└─ docs/        Plan de proyecto, diagramas PlantUML, plan de pruebas
```

### Los cuatro módulos

| Módulo | Qué administra | Estado |
|---|---|---|
| **M0** Gestión de Usuarios y Privacidad | Identidad, sesión, consentimiento versionado, baja de cuenta | Implementado (HU-01 a HU-04) |
| **M1** Seguimiento y Bitácora Diaria | Hábitos cotidianos, episodios, historial, edición y borrado | Implementado (HU-05 a HU-09) |
| **M2** Análisis Inteligente de Datos | Apriori, ventana de 48 h, Fisher y Benjamini-Hochberg | Modelos listos, motor pendiente |
| **M3** Explicabilidad y Reportes | Plantillas controladas, advertencia obligatoria, resumen imprimible | Modelos listos, generación pendiente |

El **backend es la fuente de verdad**. Los dos clientes hablan con él por REST
usando `Authorization: Bearer <access_token>`.

```
   Móvil (Flutter)        Web (React)
          \                  /
           \                /
        API REST (Django + DRF)
                  |
        Motor de patrones (Python puro)
                  |
            PostgreSQL 16
```

---

## Puesta en marcha

Se necesita: **Python 3.12+**, **Node 20+**, **Flutter 3.x**, **PostgreSQL 16**.

### 1. Base de datos

```sql
CREATE DATABASE migrapatron;
```

### 2. Backend

**Windows (PowerShell):**

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate

pip install -r requirements.txt
Copy-Item .env.example .env
# Editar .env: poner DB_PASSWORD y, si hace falta, DB_NAME
python manage.py migrate
python manage.py seed_privacidad    # publica el aviso de privacidad v1.0
python manage.py createsuperuser
python manage.py runserver          # http://127.0.0.1:8000
```

**Linux / Mac:**

```bash
cd backend
python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Editar .env: poner DB_PASSWORD y, si hace falta, DB_NAME
python manage.py migrate
python manage.py seed_privacidad
python manage.py createsuperuser
python manage.py runserver
```

> **No hace falta exportar variables de entorno.** Todo sale del `.env`. Si
> alguna vez quieres correr contra SQLite sin levantar PostgreSQL, cambia
> `DB_ENGINE=sqlite` dentro del `.env` — no uses `export` ni `$env:`.

> `seed_privacidad` **no es opcional**: sin un aviso de privacidad publicado,
> el registro de usuarios (HU-01) rechaza toda petición con un 400. Es una
> precondición del modelo de consentimiento, no un dato de adorno.

Documentación de la API en `http://127.0.0.1:8000/api/docs/`.

### 3. Web

```bash
cd web
npm install
cp .env.example .env            # PowerShell: Copy-Item .env.example .env
npm run dev                     # http://localhost:5173
```

### 4. Móvil

```bash
cd movil
flutter pub get
flutter run
```

Pantallas implementadas (HU-01 a HU-09):

| Pantalla | Historia |
|---|---|
| Login | HU-02 |
| Registro con aviso de privacidad | HU-01 |
| Inicio: estado de hoy y avance hacia M2 | HU-07 |
| Bitácora del día (11 factores) | HU-05, HU-08, HU-09 |
| Episodio (EVA 1-10 y 4 síntomas) | HU-06, HU-08, HU-09 |
| Historial con los días sin registrar | HU-07 |
| Perfil, consentimiento y baja de cuenta | HU-03, HU-04, M0.4 |

### Diseño

Paleta **«Teal sereno»**, definida en [movil/lib/core/tema.dart](movil/lib/core/tema.dart).

| | Oscuro | Claro |
|---|---|---|
| Fondo | `#101719` | `#F2F7F7` |
| Tarjeta | `#182124` | `#FFFFFF` |
| Borde | `#2D3B3E` | `#D8E6E5` |
| Texto | `#E2EDEE` | `#0E1A1B` |
| Apagado | `#9BB0B2` | `#4B6362` |
| Primario | `#5FB8B0` | `#2B7A73` |

Toda la paleta es de baja luminancia y cromatismo moderado **a propósito**: la
fotofobia es uno de los cuatro síntomas que la app registra, así que quien abre
esta pantalla puede estar en medio de un episodio. El tema sigue la preferencia
del sistema (`ThemeMode.system`).

La escala de intensidad del dolor usa una rampa cálida aparte, nunca el verde
azulado de marca — así «botón principal» y «dolor intenso» no se confunden.
Hay una prueba que lo verifica.

La URL base del backend está en `lib/core/config.dart`. Para el emulador de
Android se usa `10.0.2.2` (el alias del `localhost` de la máquina anfitriona);
para un dispositivo físico hay que poner la IP LAN.

---

## Flujo de trabajo

Ramas: `main` (estable) ← `develop` (integración) ← `feature/HU-xx-descripcion`.

`develop` está protegida: nada entra sin Pull Request aprobado por otra persona
y con el pipeline en verde.

```bash
git checkout develop
git pull
git checkout -b feature/HU-05-bitacora-diaria
# ... trabajar ...
git push -u origin feature/HU-05-bitacora-diaria
# abrir Pull Request hacia develop
```

### Definition of Done

Una historia está terminada cuando cumple las ocho:

1. PR a `develop` con al menos una revisión aprobada.
2. Criterios de aceptación verificados por el Product Owner.
3. Pruebas unitarias nuevas que cubren la lógica agregada.
4. Cobertura ≥ 80% backend, ≥ 90% en `backend/apps/analisis/motor/`, ≥ 60% Flutter.
5. Quality Gate de SonarCloud en verde.
6. Lint sin errores (`ruff`, `black --check`, `dart analyze`, `eslint`).
7. Endpoints documentados en OpenAPI y en la colección Postman.
8. La suite completa pasa: sin regresiones.

---

## Comandos de calidad

```bash
# Backend  (las pruebas corren sobre SQLite en memoria; CI usa PostgreSQL real)
cd backend
pytest --cov=apps --cov-report=term-missing
ruff check .
black --check .
python manage.py spectacular --fail-on-warn --file /dev/null

# Web
cd web
npm run lint
npm run build

# Móvil
cd movil
flutter analyze
flutter test --coverage
```

---

## Documentación

| Documento | Qué contiene |
|---|---|
| [docs/diagramas/PLAN_PROYECTO.txt](docs/diagramas/PLAN_PROYECTO.txt) | Plan completo: alcance, 13 casos de uso, 10 RNF, 7 reglas de negocio, 21 historias, 3 sprints, plan de calidad |
| [docs/diagramas/01_casos_de_uso.puml](docs/diagramas/01_casos_de_uso.puml) | Diagrama de casos de uso |
| [docs/diagramas/02_modelo_datos.puml](docs/diagramas/02_modelo_datos.puml) | Modelo entidad-relación (17 tablas) |
| [docs/diagramas/03_arquitectura.puml](docs/diagramas/03_arquitectura.puml) | Vista de componentes |
| [docs/diagramas/04_secuencia_analisis.puml](docs/diagramas/04_secuencia_analisis.puml) | Secuencia de CU-08 (analizar mis patrones) |

Los `.puml` se renderizan en [plantuml.com](https://www.plantuml.com/plantuml/uml/)
o con la extensión PlantUML de VS Code.

---

## Equipo

| Integrante | Rol SCRUM | Frente técnico |
|---|---|---|
| Integrante 1 | Tech Lead | Backend y motor de patrones |
| Integrante 2 | Scrum Master | Arquitectura Flutter |
| Integrante 3 | Product Owner | Pantallas móvil y web |
| Integrante 4 | QA Engineer | Pruebas, métricas, CRUD backend |
