# RPA local para consultar servicios de ARCA

Aplicación local para Windows que abre el portal oficial de ARCA, permite autenticarte manualmente o completar el formulario con un perfil de Windows Credential Manager y muestra los enlaces de servicios visibles en la sección que abriste. El robot no envía formularios, no opera trámites ni guarda resultados.

## Requisitos

- Windows 10/11.
- Python 3.11 o superior, en una rama estable que todavía reciba actualizaciones de seguridad y con dependencias disponibles para esa versión y arquitectura.
- Conexión a Internet para instalar dependencias y abrir ARCA.
- Chromium de Playwright, instalado siguiendo los pasos inferiores.

No se exige Python 3.12: el código no contiene una restricción a esa versión. Python 3.9 y 3.10 quedan fuera de la recomendación por haber terminado su soporte de seguridad. Las versiones futuras deben comprobarse con las dependencias fijadas; no se presupone compatibilidad ilimitada. Se verificó la resolución de dependencias para Python 3.15 de 64 bits mediante `pip --dry-run`; esto no sustituye la prueba funcional del RPA.

## Instalación en PowerShell

Abre PowerShell en esta carpeta (`2- RPA Arca`) y comprueba el intérprete seleccionado:

```powershell
py -3 --version
py --list
```

Si `py -3` muestra una versión estable compatible (3.11 o superior), crea el entorno:

```powershell
py -3 -m venv .venv
```

Si selecciona una versión antigua aunque tengas otra instalada, elige una de las versiones compatibles de `py --list`. Por ejemplo, si tienes 3.15:

```powershell
py -3.15 -m venv .venv
```

El número de ese ejemplo se sustituye por tu versión instalada; no es un requisito exclusivo. Si no tienes el lanzador `py`, usa `python --version` y `python -m venv .venv`, comprobando igualmente la versión. Si no tienes ninguna versión compatible, instala una versión estable con soporte desde https://www.python.org/downloads/windows/ y vuelve a abrir PowerShell.

Si ya existe `.venv`, comprueba su versión con `.\.venv\Scripts\python.exe --version`. Un entorno creado con una versión antigua no se actualiza automáticamente: renómbralo antes de crear uno nuevo con el intérprete elegido.

Instala las dependencias y el navegador, ejecutando cada comando por separado y deteniéndote si falla:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
```

No hace falta activar el entorno ni cambiar la política de ejecución de PowerShell. Si pip informa que no encuentra una distribución compatible, revisa la versión y arquitectura del intérprete; no elimines las versiones fijadas de dependencias para forzar la instalación.

## Ejecutar

Con el entorno virtual activado:

```powershell
python .\main.py
```

Sin activarlo:

```powershell
.\.venv\Scripts\python.exe .\main.py
```

## Modo manual

1. Selecciona **Ingresar manualmente** y pulsa **Abrir ARCA**.
2. Ingresa tus datos únicamente en el navegador oficial y resuelve personalmente cualquier desafío de seguridad.
3. Al llegar al portal, el robot detecta la ruta de inicio, sigue el enlace **Ver todos** hacia **Mis servicios** y lee los títulos de las tarjetas. No hay checkbox ni confirmación manual para iniciar la lectura.
4. Revisa el listado. Si la estructura no coincide o la lectura falla, el navegador sigue abierto y puedes pulsar **Reintentar consulta**.
5. Pulsa **Cerrar sesión y finalizar**. El robot abre el menú de usuario, pulsa Salir y verifica que ARCA vuelva a pedir el ingreso antes de cerrar su navegador. Si no confirma la salida, conserva la ventana y permite reintentar.

El reconocimiento se basa en el host `portalcf.cloud.afip.gob.ar`, las rutas observadas `/portal/app/` y `/portal/app/mis-servicios`, el título **Mis servicios** y tarjetas con rol de botón y encabezado. No requiere que «Salir» esté visible. La URL por sí sola no se considera prueba suficiente del contenido.

## Modo con perfil de Windows

1. Selecciona **Usar un perfil guardado en Windows** y pulsa **Agregar perfil…**.
2. Asigna un nombre, escribe la CUIT y la clave fiscal en el campo enmascarado. Lee el aviso y marca la confirmación para guardar. Windows Credential Manager conserva la credencial localmente; la aplicación recibe la clave durante el alta y al usarla.
3. Selecciona el perfil y pulsa **Abrir ARCA**. Confirma el aviso de uso. La aplicación completa primero solo la CUIT en el paso oficial de `auth.afip.gob.ar`.
4. Verifica el dominio y pulsa **Siguiente** en ARCA. Cuando aparezca el paso de clave, vuelve a la aplicación y confirma. Solo entonces el RPA valida el host y el campo de clave, recupera la clave del perfil elegido y la completa. No pulsa el botón de ingreso.
5. Revisa el dominio, envía el formulario y resuelve manualmente los desafíos. El robot detectará el portal y abrirá **Mis servicios** para leer las tarjetas automáticamente.
6. Para borrar una cuenta guardada, selecciona el perfil y pulsa **Eliminar**. Esto borra la credencial de Windows; no modifica la clave en ARCA.

La opción con perfiles es voluntaria. Windows cifra el almacén bajo la sesión del usuario, pero la aplicación maneja la clave en memoria durante el alta y el login. No la uses en un equipo que no controles.

## Alcance y límites conocidos

- La interfaz deja la autenticación, el envío del formulario y los desafíos de seguridad en manos de la persona.
- El navegador es visible y usa un contexto efímero. No se importa un perfil personal de Chrome/Edge, no se exportan cookies y no se generan capturas, videos o trazas.
- La aplicación lee títulos de tarjetas dentro de la sección Mis servicios. Las reglas se contrastaron con capturas del HTML aportadas por el usuario y se probaron con páginas sintéticas en Chromium; falta confirmar el recorrido actualizado con una sesión real. No se incorporaron datos personales a las pruebas.
- No se ha validado todavía la extracción contra una cuenta real. La primera ejecución debe servir para revisar el selector del login y la región HTML en la que ARCA presenta **Ver todos**. No compartas claves, cookies, capturas con datos de contribuyentes ni archivos de diagnóstico; comunica solo el texto de error y, si hace falta, una captura censurada.
- La lista representa tarjetas renderizadas en Mis servicios. El robot limpia el buscador local y espera que los títulos se estabilicen; esa estabilidad no garantiza detectar cargas diferidas no observadas. Rechaza paginación reconocible, pero no combina páginas. No es una auditoría de permisos, representaciones ni servicios delegados.
- La aplicación no escribe logs ni exporta el resultado. La instalación de dependencias contacta PyPI; durante la consulta, el navegador accede al sitio de ARCA.

Python no garantiza el borrado físico de todas las copias de una contraseña que hayan existido en memoria. La aplicación elimina referencias y cierra el contexto al terminar, pero no puede prometer una limpieza forense de memoria.

## Seguridad y administración de perfiles

Los perfiles usan dos tipos de credenciales genéricas en el almacén de Windows: metadatos (alias y CUIT) y una entrada separada para la clave. El selector enumera solo los metadatos, de modo que no lee todas las contraseñas al listar cuentas. La clave del perfil seleccionado se recupera después de que la persona avanza desde la pantalla de CUIT y la aplicación reconoce la pantalla oficial de contraseña. No se guardan secretos en el código, `.env`, archivos de configuración, argumentos de proceso ni logs.

Si la aplicación se cierra inesperadamente, comprueba en el navegador que la sesión haya terminado. Para borrar perfiles también puedes usar **Administrador de credenciales de Windows → Credenciales de Windows** y quitar las entradas `PruebaTecnicaMHLM/ARCA/...`.

## Archivos

- `main.py`: interfaz local.
- `arca_browser.py`: automatización visible con Playwright y validación de página.
- `credential_store.py`: perfiles locales sobre Windows Credential Manager.
- `requirements.txt`: dependencias fijadas.

## Referencias de instalación y seguridad

- [Estado de soporte de Python](https://devguide.python.org/versions/)
- [Playwright 1.65.2](https://pypi.org/project/playwright/1.65.2/)
- [pywin32 312](https://pypi.org/project/pywin32/312/)


### Cierre y foco de la ventana

Después de obtener resultados, la aplicación vuelve al frente sin permanecer siempre por encima de otras ventanas. El cierre automático usa los controles observados `header #iconoChicoContribuyenteAFIP` y `#contBtnContribuyente button[title="Salir"]`. Si el portal no vuelve directamente al ingreso, se verifica el acceso a Mis servicios desde otra pestaña del mismo contexto efímero, sin copiar cookies ni credenciales. No se considera suficiente el simple cierre de una ventana. Esta validación del cierre pasó pruebas sintéticas; queda pendiente comprobar la redirección real. La cancelación antes de obtener resultados mantiene el comportamiento anterior de cerrar el navegador sin confirmar una salida del servidor.
