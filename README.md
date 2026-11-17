# Prueba técnica MHLM

Tres ejercicios: un perfil de Mauricio Hugo López Martín, un robot para consultar los servicios de ARCA y un análisis de operaciones de importación con SQL.

## Empezar por la entrega completa

El paquete **PruebaTecnicaMHLM-Completa.zip** reúne informes, programas y código. [Descargar el ZIP completo](https://github.com/SrBizco/PruebaTecnicaMHLM/releases/download/entrega-v1.0.0/PruebaTecnicaMHLM-Completa.zip) o consultar la [entrega v1.0.0](https://github.com/SrBizco/PruebaTecnicaMHLM/releases/tag/entrega-v1.0.0). Los ZIP automáticos de GitHub llamados **Source code** no incluyen los ejecutables ni el visor SQL.

1. Extraer **todo** el ZIP en una carpeta del equipo. No ejecutar los programas desde el comprimido.
2. Abrir `LEEME.txt` para una guía breve, o seguir esta tabla.

| Ejercicio | Qué abrir en el ZIP | Para qué sirve |
|---|---|---|
| 1. Perfil profesional | [Informe de Mauricio](1-%20informe/informe-mhlm.pdf) | Leer el perfil de tres páginas. |
| 2. Automatización ARCA | `2- RPA Arca/ARCA-RPA.exe` | Ingresar y consultar los servicios de la cuenta activa. Ver `INSTRUCCIONES.txt` en esa carpeta. |
| 3. Operaciones SQL | `3- Operaciones SQL/Informe-operaciones.pdf` | Leer los totales mensuales, inconsistencias y su tratamiento. |
| 3. Consultas propias | `3- Operaciones SQL/CONSULTAR_SQL.cmd` | Abrir el visor con siete consultas SQL preparadas y escribir otras. |

## Requisitos para usar el ZIP

- **Windows 10/11 de 64 bits** para el RPA y el visor SQL. Los PDF y archivos de texto se pueden leer en otros sistemas.
- No hace falta instalar Python, Git ni un servidor de base de datos para usar los programas incluidos.
- **RPA:** requiere Internet. Al primer inicio comprueba el navegador Chromium y lo descarga si falta; puede tardar varios minutos. Los perfiles se crean en cada equipo y no se incluyen en la entrega. CAPTCHA y verificaciones adicionales se resuelven personalmente.
- **SQL:** funciona localmente sin Internet ni instalación. El visor abre la base en modo lectura para proteger los datos entregados. En la pestaña **Ejecutar SQL**, elegir una consulta y pulsar el botón triangular; también se puede modificar el texto para hacer consultas propias.
- Extraer en una carpeta con permisos de escritura. El RPA no tiene firma digital; Windows puede mostrar una advertencia. No es necesario desactivar las protecciones de Windows.

## Dónde está el material de revisión

En el ZIP:

- `1- informe/informe-mhlm.md`: versión textual editable del perfil. `referencias/`: biblia de investigación y matriz con fuentes y límites de evidencia.
- `2- RPA Arca/codigo/`: código Python, pruebas, dependencias e instrucciones para ejecutar o reconstruir el RPA. El ejecutable incluido corresponde a **rpa-v1.0.2**, probado por el autor en otro equipo sin dependencias previamente instaladas.
- `3- Operaciones SQL/codigo/datos/`: planilla original sin modificar.
- `3- Operaciones SQL/codigo/sql/`: consultas y esquema. `01_pagos_mensuales.sql` responde la pregunta principal; `esquema.sql` es para crear la base, no una consulta de resultados.
- `3- Operaciones SQL/codigo/resultados/operaciones.sqlite`: base entregada. En esa misma carpeta se conservan CSV como exportaciones técnicas; para una lectura cómoda usar el PDF o el visor.
- `3- Operaciones SQL/codigo/`: scripts de carga y generación, pruebas e instrucciones de reproducción.
- `3- Operaciones SQL/terceros/` y `visor/licenses/`: procedencia, licencias y materiales de terceros necesarios para distribuir el visor.
- `MANIFIESTO.json`: versiones y hashes SHA-256 de los archivos para verificar integridad; no hace falta abrirlo para evaluar la prueba.

**Criterio SQL:** el mes corresponde a la fecha de oficialización, porque la planilla no contiene fecha de pago. La respuesta suma `Total pagado USD`. Se conservan 61 filas originales y se excluye una copia exacta del cálculo: 60 operaciones incluidas, por USD 1.381.267,38. El PDF es una instantánea; ejecutar nuevas consultas no lo actualiza.

## Organización del repositorio

El repositorio conserva además los planes, bitácoras y diagnósticos como antecedentes. El ZIP omite esos documentos de trabajo, entornos virtuales, cachés y compilaciones anteriores.

| Carpeta del repo | Documentación / resultado |
|---|---|
| `1- informe` | [Perfil PDF](1-%20informe/informe-mhlm.pdf) y [fuentes](1-%20informe/matriz-fuentes.csv). |
| `2- RPA Arca` | [Guía técnica](2-%20RPA%20Arca/README.md) y código del RPA. |
| `3- Operaciones SQL` | [Guía SQL](3-%20Operaciones%20SQL/README.md) y [PDF de resultados](3-%20Operaciones%20SQL/resultados/Informe-operaciones.pdf). |
| `entrega` | Empaquetador y notas para preparar la entrega completa. |

## Preparar la entrega (solo autor)

1. Tener el EXE validado `2- RPA Arca/dist/ARCA-RPA.exe` de rpa-v1.0.2 (extraído del release o conservado tras su compilación).
2. Regenerar SQL: ejecutar `3- Operaciones SQL/preparar_entrega.py` con un Python que tenga las dependencias de `requirements-informe.txt`. `--offline` permite reutilizar los recursos oficiales ya verificados en caché.
3. Ejecutar `python entrega/preparar.py`. Solo necesita la biblioteca estándar de Python 3.9 o posterior.
4. Ejecutar `python entrega/verificar.py`: extrae en una ruta con espacios, comprueba integridad y ejecuta las siete consultas en modo lectura, sin abrir cuentas de ARCA.
5. Revisar `entrega/dist/PruebaTecnicaMHLM-Completa.zip` y su archivo `.sha256`. Adjuntarlos al release con las notas de `entrega/RELEASE.md`.

El empaquetador no instala software, no usa credenciales, no hace commits ni publica releases.
