# RPA local para consultar servicios de ARCA

## Usar el ejecutable (Windows x64)

En la entrega completa, abrir `2- RPA Arca/ARCA-RPA.exe` después de extraer todo el ZIP. No requiere Python ni Git. Al primer inicio comprueba sus componentes y descarga Chromium oficial si falta. Se necesitan Internet, espacio y permisos de escritura en el perfil de Windows.

El ejecutable entregado es **rpa-v1.0.2**. El autor confirmó su funcionamiento en otro equipo sin dependencias previamente instaladas. No está firmado digitalmente; Windows puede mostrar una advertencia. No desactivar las protecciones del sistema.

## Consultar servicios

**Ingreso manual**
1. Seleccionar **Ingresar manualmente** y pulsar **Abrir ARCA**.
2. Completar CUIT y clave en el navegador oficial. Resolver personalmente cualquier verificación adicional.
3. Al llegar al portal, el robot abre **Ver todos / Mis servicios**, obtiene las tarjetas y muestra los resultados en la aplicación. No hay que confirmar cada pantalla.

**Con un perfil guardado**
1. Seleccionar **Usar un perfil guardado en Windows** y **Agregar perfil…**.
2. Ingresar alias, CUIT y clave; confirmar el almacenamiento local. Se pueden guardar varios perfiles.
3. Seleccionar el perfil, pulsar **Abrir ARCA** y aceptar el aviso. El robot completa CUIT, pulsa Siguiente, reconoce la pantalla de contraseña, completa la clave y pulsa Ingresar.
4. Si ARCA solicita CAPTCHA u otra comprobación, resolverla personalmente. El robot no intenta eludirla.
5. El robot entra a Mis servicios y muestra el listado. Para borrar un perfil, usar **Eliminar**; no cambia la clave fiscal en ARCA.

Después de obtener los resultados, la aplicación intenta volver al frente. El navegador sigue disponible si se necesita intervenir. Algunas etiquetas de la versión 1.0.2 todavía indican revisar/enviar el formulario; el comportamiento implementado en el modo con perfil ya incluye el envío automático.

**Finalizar:** pulsar **Cerrar sesión y finalizar**. El RPA intenta cerrar la sesión en ARCA y comprobar la salida antes de cerrar su navegador. Si no consigue confirmarla, informa ese límite y cierra el navegador local; no afirma que la sesión del servidor haya terminado. Cancelar antes de obtener resultados no garantiza verificar una salida en el servidor.

## Si algo falla

- Si falla la descarga de Chromium: revisar conexión, espacio y permisos; volver a abrir el ejecutable.
- Si cambia el portal o no se obtiene el listado: leer el estado en la aplicación y usar **Reintentar consulta** cuando esté disponible.
- Si ARCA rechaza el acceso: revisar los datos y las verificaciones en el navegador oficial. El robot no prueba claves alternativas.
- La lista muestra servicios de la cuenta activa; no recorre automáticamente todas las cuentas guardadas ni cambia representados.

## Seguridad y alcance

- La CUIT y la clave se completan únicamente en el formulario HTTPS oficial validado por el código.
- Los perfiles opcionales se almacenan en Windows Credential Manager para el usuario local. No viajan en el ZIP. La aplicación accede a la clave en memoria durante el alta y el uso; este modo no equivale a que el programa nunca maneje la contraseña.
- El selector enumera metadatos separados del secreto. No se guardan credenciales en código, archivos de configuración, argumentos ni logs.
- El navegador usa un contexto efímero: no importa el perfil personal, no exporta cookies ni produce capturas, videos o trazas.
- El programa lee tarjetas de **Mis servicios** y no ejecuta trámites. No exporta los resultados.
- El reconocimiento se basa en dominio, rutas y estructura observada del portal. Cambios de ARCA pueden requerir mantenimiento; no se garantiza compatibilidad permanente.
- La estabilidad de tarjetas no demuestra por sí sola que no exista carga diferida. La paginación reconocible se rechaza; no se combinan páginas. No es una auditoría de permisos ni servicios delegados.
- Python no garantiza borrado forense de todas las copias de una clave en memoria.
- Para eliminar perfiles fuera de la aplicación: Administrador de credenciales de Windows, entradas `PruebaTecnicaMHLM/ARCA/...`.

## Ejecutar desde código (solo revisión técnica)

En el repo, abrir PowerShell en `2- RPA Arca`; en el ZIP completo, en `2- RPA Arca/codigo`.

Usar Python 3.11 o superior compatible con las versiones fijadas en `requirements.txt`. No hay una exigencia exclusiva de Python 3.12. Comprobar la versión instalada con `py --list` y seleccionar una que disponga de las dependencias necesarias. Sustituir `py -3` si apunta a otra versión.

Ejecutar cada comando por separado y detenerse ante un error:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe .\main.py
```

No hace falta activar el entorno ni cambiar la política de ejecución. Si `.venv` ya usa otro Python, renombrarlo antes de recrearlo. La ejecución por código requiere preparar dependencias; la entrega EXE ya contiene Python y las bibliotecas.

## Archivos y verificaciones

- `main.py`: interfaz local.
- `arca_browser.py`: navegación, autenticación, extracción y cierre.
- `credential_store.py`: perfiles locales.
- `launcher.py`: comprobación e instalación de Chromium para el EXE.
- `test_*.py`: pruebas automatizadas con escenarios controlados.
- `app_smoke.py`: prueba de interfaz con perfiles ficticios.
- `build.ps1`, `requirements-build.txt`: reconstrucción con PyInstaller.

Para ejecutar las pruebas:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
```

Para reconstruir, con el entorno preparado, ejecutar `build.ps1` desde PowerShell. La salida es `dist/ARCA-RPA.exe`. Una nueva compilación requiere validación antes de sustituir el binario entregado.

Los ensayos automatizados y la prueba informada por el autor no garantizan el comportamiento de todas las cuentas ni de cambios futuros en ARCA.
