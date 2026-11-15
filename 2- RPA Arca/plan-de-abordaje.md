# Plan de abordaje — RPA local para consultar servicios de ARCA

**Versión:** 0.3
**Fecha:** 15 de noviembre de 2026  
**Estado:** diseño aprobado; primera implementación escrita, pendiente de validación local del portal.

## 1. Objetivo y alcance

Desarrollar una aplicación local para Windows que abra el acceso oficial de ARCA, permita dos modalidades de inicio de sesión —manual o con credencial local de Windows— y muestre los servicios disponibles para la cuenta activa. La primera entrega será código Python ejecutable localmente, con instalación documentada. El empaquetado como `.exe` se evaluará después de que el RPA funcione.

El proceso será de solo lectura. No dará de alta ni de baja servicios, no cambiará relaciones, no operará con CUIT representadas y no abrirá otros trámites. El alcance inicial será la lista visible para la cuenta activa en el panel de servicios de ARCA, incluida la opción «Ver todos» cuando esté disponible.

## 2. Enfoque acordado

**Python + Playwright con Chromium visible y un contexto aislado no persistente.** La interfaz local (Tkinter) tendrá dos opciones claramente separadas:

1. **Ingresar manualmente (recomendado y seleccionado por defecto).** El navegador abre el portal oficial; la persona escribe CUIT y clave directamente en ARCA y resuelve cualquier control adicional. La aplicación no accede a esos campos ni a la clave.
2. **Usar un perfil guardado en Windows (opcional, más automatizado).** La persona elige esta opción en cada ejecución y selecciona uno de sus perfiles. Si todavía no tiene perfiles, la interfaz ofrece «Agregar perfil» y guía el alta sin exigir que conozca Credential Manager. El alta solicita un nombre descriptivo, CUIT y clave en un diálogo propio con la clave enmascarada, explica que se guardará localmente en Windows Credential Manager y exige confirmación explícita. La aplicación escribe la credencial directamente en el almacén del sistema, nunca en archivos, configuración, línea de comandos ni logs. Cada perfil usa destinos separados para permitir varias cuentas. En cada uso, la aplicación completa primero solo la CUIT en el formulario oficial; la persona pulsa «Siguiente» y confirma en la app cuando ve el paso de clave. Solo después de validar HTTPS, host y formulario, el RPA recupera la clave del perfil seleccionado y la completa. La persona revisa y envía el formulario; CAPTCHA, segundo factor y cualquier decisión de seguridad quedan manuales. La interfaz también permite eliminar perfiles guardados.

La segunda modalidad reduce la escritura repetitiva y permite manejar varias cuentas desde una interfaz simple, pero **amplía la responsabilidad del programa**: durante el alta recibe la clave en memoria y la persiste en el almacén local; durante el uso la vuelve a recuperar. Windows Credential Manager cifra credenciales bajo la sesión de usuario; esto es mejor que un archivo plano o código, pero no protege frente a malware o código malicioso ejecutado con los mismos permisos del usuario. ARCA recomienda no almacenar la clave en el navegador y deshabilitar el autocompletado; no encontramos una recomendación expresa sobre Credential Manager ni autorización específica para que esta aplicación la almacene. El modo manual seguirá siendo el predeterminado, y la opción de guardar deberá ser optativa, clara y reversible.

Flujo propuesto:

1. La persona abre la aplicación y elige «Ingresar manualmente» o «Usar perfil guardado en Windows».
2. Se abre la página oficial de Clave Fiscal de ARCA (`https://www.arca.gob.ar/claveFiscal/`) y el RPA sigue el enlace «Ingresar al portal con clave fiscal» que esa página ofrece. En la consulta del 15/11/2026, ese enlace conduce a `https://auth.afip.gob.ar/contribuyente_/login.xhtml`.
3. En modo manual, la persona ingresa sus datos. En modo perfil, elige una cuenta guardada o la agrega en ese momento. Antes de guardar, ve qué datos se conservarán, dónde se almacenarán y cómo borrarlos. El RPA completa la CUIT; la persona avanza al paso de clave y confirma en la aplicación. El RPA valida el formulario de clave y recién entonces recupera/completa la contraseña. El login público observado está dividido en dos etapas; la persona debe pulsar «Siguiente» entre ambas.
4. La persona revisa y envía el formulario, resuelve cualquier CAPTCHA o segundo factor y navega hasta Servicios / «Ver todos».
5. La persona confirma en la aplicación que abrió «Ver todos» sin filtros; el RPA valida host HTTPS, señal visible de sesión, título completo de la lista, un contenedor semántico bajo la región principal y contenido de servicios. Si detecta paginación, filtro activo, pantalla de login, dominio inesperado o estructura ambigua, se detiene sin declarar éxito. La extracción del DOM aún debe contrastarse en una ejecución local.
6. La interfaz muestra enlaces de servicio visibles y su cantidad. No guarda el resultado por defecto.
7. La persona cierra sesión en ARCA desde el propio sitio. Al cerrar la aplicación, se descartan el contexto y sus cookies temporales.
## 3. Alternativas consideradas

| Alternativa | Ventajas | Costos y límites | Decisión |
|---|---|---|---|
| **Python + Playwright + Chromium visible** | Código mantenible; sesión aislada; esperas y selectores semánticos; resultados reproducibles; ofrece ingreso manual y perfiles optativos de Windows Credential Manager. | La interfaz del portal puede cambiar; hay que instalar Python y el navegador de Playwright. El modo de perfiles requiere un diálogo de alta que recibe la clave en memoria. El proceso conserva acceso a la sesión autenticada mientras está abierta. | **Elegida.** Mejor balance para entregar código local, control de seguridad y manejo explícito de estados. |
| **Power Automate Desktop** | Visual y local; el usuario puede observar los pasos; reduce código inicial. | Clics y selectores visuales más frágiles; dependencia del entorno/licencia de Windows; entrega y revisión técnica menos reproducibles. | No elegida para la primera versión. |
| **Ingreso de contraseña en la app, automatización invisible o llamadas a endpoints no documentados** | Puede parecer más automático o estable al comienzo. | Expone credenciales o sesión, complica el consentimiento y puede eludir controles o depender de APIs internas. | **Descartada.** No satisface el requisito de seguridad. |

## 4. Seguridad y datos

En modo manual, la clave fiscal no se solicitará, leerá, copiará ni registrará en la aplicación. En modo perfil, la aplicación la recibirá en un diálogo de alta/edición, la guardará en Windows Credential Manager tras consentimiento y la recuperará en memoria al usarla. ARCA la define como personal e intransferible, recomienda no almacenarla en el navegador y pide verificar el sitio antes de autenticarse. Por eso, la app debe abrir una dirección oficial conocida, dejar visible la barra del navegador y pedir a la persona que compruebe el dominio y HTTPS antes de ingresar datos.

El contexto de Playwright será no persistente: no se usará un perfil personal de Chrome/Edge, `launch_persistent_context`, almacenamiento de sesión ni exportación de cookies. La documentación de Playwright indica que un contexto no persistente no escribe datos de navegación al disco. La sesión seguirá siendo sensible mientras viva en memoria: el proceso automatizado puede leer contenido de la página autenticada y un equipo comprometido puede observar pantalla o memoria. Esta limitación no se puede eliminar manteniendo la automatización; solo reducir con alcance mínimo y cierre diligente.

Controles propuestos:

- No incluir claves, CUIT, cookies, tokens ni datos personales en código, `.env`, archivos de configuración o ejemplos. En el modo de perfiles, almacenar cada credencial directamente en Windows Credential Manager con destinos separados y sin archivos intermedios. Nunca poner contraseñas en argumentos de procesos. La aplicación debe permitir borrar perfiles del almacén y explicar que la eliminación de un perfil no cambia la clave de ARCA.
- No usar servicios externos, telemetría, APIs de terceros ni almacenamiento en nube. En ejecución, la conexión web será la del navegador con ARCA; la instalación descarga dependencias públicas, sin transmitir credenciales.
- No registrar HTML, cuerpos de página, nombres de servicios, capturas, videos, trazas, variables de credencial ni consola del navegador. En modo Windows, eliminar referencias a los valores de credencial al terminar el uso, con la salvedad de que Python y el proceso del navegador no ofrecen garantía de borrado físico de toda copia en memoria. Los errores locales podrán indicar etapa y tipo de fallo, nunca contenido de la cuenta o query strings.
- Mantener validación TLS activa; no ignorar certificados ni aceptar dominios inesperados. Si el acceso redirige el formulario de login fuera de `auth.afip.gob.ar`, detenerse antes de ingresar credenciales. Tras el login, detenerse si el contenido o el dominio no corresponden a ARCA/AFIP según los sufijos oficiales autorizados.
- En modo manual, no leer ni completar los campos de login. En modo perfil, solo completar el formulario visible en `auth.afip.gob.ar` tras validar host y controles; no reintentar credenciales, resolver CAPTCHA, interceptar controles, extraer tokens ni continuar ante un desafío no previsto. La persona resuelve cualquier CAPTCHA, segundo factor y envío del formulario.
- No usar un contexto guardado entre ejecuciones. Al finalizar, indicar que se cierre sesión con «Salir» dentro de ARCA y cerrar el navegador temporal. Si el navegador se cae, cerrar y descartar el contexto como medida de limpieza.
- Mostrar únicamente nombres de servicios que ARCA presenta en la pantalla solicitada. No recolectar identificadores tributarios, mensajes, actividad ni datos de otros contribuyentes.

## 5. Puntos débiles identificados y mitigaciones

| Debilidad | Impacto posible | Mitigación / riesgo residual |
|---|---|---|
| **El proceso administra perfiles de credenciales y controla una sesión autenticada.** | La app recibe la clave durante el alta y la usa en memoria; malware local o código con los mismos permisos podría observarla. | Modo manual por defecto; alta solo por acción expresa con consentimiento informado; almacén cifrado de Windows, destinos aislados, listado y eliminación de perfiles; contexto efímero, sin logs/capturas/persistencia adicional. No hay garantía de borrar toda copia de memoria. |
| **La interfaz de ARCA puede cambiar sin aviso.** | Selectores dejan de coincidir o una pantalla distinta puede parecer un resultado válido. | Usar roles, etiquetas y texto visibles; verificar encabezado, estado y contenedor antes de extraer; ante ambigüedad, abortar con un mensaje claro, no adivinar. El mantenimiento periódico será necesario. |
| **Autenticación y redirecciones variables.** | 2FA, CAPTCHA, ventanas nuevas, expiración o flujos de representación pueden interrumpir la sesión. | Navegador visible, pausa humana, límites de tiempo por etapa y manejo de páginas emergentes. No reintentar el login automáticamente ni sortear desafíos. |
| **Lista visible versus habilitaciones efectivas.** | El panel podría mostrar accesos/atajos y no representar todas las relaciones o permisos de la cuenta. | Primera versión definida como lista que ARCA muestra bajo «Ver todos» para la cuenta activa. No afirmar que audita todas las autorizaciones administrativas. |
| **El selector DOM puede no exponer todos los elementos.** | Contenido en iframe, carga dinámica o paginación puede producir un listado incompleto. | Esperas por estado visible, contar filas, detectar paginación y estados vacíos; validar que el resultado coincide con el panel mostrado. Si no se puede validar, no presentar éxito. |
| **No se encontró en la documentación revisada una API pública documentada para este listado ni una promesa de estabilidad de la interfaz. La documentación oficial de WSAA describe autenticación por certificado X.509 y asociación a un Web Service de negocio; no es una API genérica para leer los servicios visibles de una cuenta.** | El RPA depende de la UI y puede romperse; no sabemos todavía si existen condiciones específicas para automatizar el uso ordinario. | Antes de ejecutar con una cuenta real, revisar cualquier término o condición de acceso aplicable. No confundir la política del programa de reporte de vulnerabilidades de ARCA —que limita automatización para buscar vulnerabilidades— con una autorización general para automatizar trámites. Si no se aclara el permiso o ARCA bloquea el flujo, detenerse y reevaluar. |
| **Falsos positivos o datos incompletos.** | La pantalla de login, un error de red o un estado vacío podrían confundirse con una lista válida. | Máquina de estados y reglas de éxito explícitas; verificar título de sesión, sección de servicios y lista (o mensaje vacío explícito). Mostrar «no se pudo verificar» ante duda. |

## 6. Esperas, errores y validación

La automatización no dependerá de pausas fijas como `sleep(5)`. Usará esperas explícitas sobre elementos observables y los auto-waits de Playwright. Cada etapa tendrá un límite de tiempo y un resultado: `INICIANDO`, `ESPERANDO_AUTENTICACION`, `VALIDANDO_SESION`, `LEYENDO_SERVICIOS`, `RESULTADO`, `ERROR`.

Errores previstos: página oficial no disponible; host inesperado; autenticación no completada; CAPTCHA/segundo factor pendiente; sesión expirada; ventana emergente; selector ausente o ambiguo; carga incompleta; lista vacía explícita; y estructura de portal cambiada. La interfaz explicará el paso que falló sin imprimir el contenido del portal. Solo se permitirán reintentos de lecturas idempotentes; nunca se reenviará una clave.

Un resultado se considerará válido si: (a) la URL usa HTTPS y corresponde a un host oficial reconocido; (b) se ve el área autenticada de ARCA y no el formulario de acceso/error; (c) se identifica la sección de servicios; y (d) el texto de cada servicio y el total coinciden con las filas visibles. Si cualquiera falla, no se mostrará un listado como exitoso.

Playwright verifica automáticamente que elementos sobre los que se hace clic estén visibles, estables, habilitados y no cubiertos; esto reduce errores de interacción, pero no garantiza que ARCA mantenga sus etiquetas o su estructura.

## 7. Instalación local propuesta

Primera entrega: código fuente Python, entorno virtual y dependencias fijadas en `requirements.txt`; guía de instalación para Windows; comando explícito para instalar el navegador Playwright; y comando para iniciar la interfaz. No se incluirá ningún secreto ni perfil de navegador. El usuario instalará y ejecutará localmente; no se enviará nada a un servidor propio. El `.exe` queda fuera de esta fase y solo se evaluará después de validar el RPA funcional.

## 8. Criterios de aceptación

- En modo manual, la aplicación no accede a la clave. En modo perfil, la clave solo se captura en un diálogo enmascarado al crear/actualizar un perfil, se escribe directamente en Windows Credential Manager y se recupera para completar el formulario oficial visible.
- Ambos modos son visibles, locales y de solo lectura. Los perfiles guardados son optativos, separados por cuenta, listables y eliminables desde la interfaz; su alta requiere explicar almacenamiento y riesgos. Ninguno genera cookies persistentes, resultados guardados ni artefactos de diagnóstico.
- Si aparece un desafío de seguridad, dominio desconocido, error o cambio de interfaz, el RPA se detiene de manera segura y explica qué hacer.
- El resultado muestra servicios de la cuenta activa desde «Ver todos» (cuando aplique), con un recuento coherente y sin incluir contenido ajeno a esa lista.
- Las instrucciones permiten instalar y ejecutar el código en Windows antes de considerar empaquetado.

## 9. Herramientas de credenciales consideradas

- **Windows Credential Manager desde Python:** opción local elegida para perfiles optativos; evita archivos y servicios externos y permite varios destinos. Facilita la administración desde la aplicación, pero el programa recibe la clave al guardarla y al iniciar sesión. Deben evitarse argumentos de línea de comandos y archivos temporales.
- **Diálogo nativo de Windows CredUI:** puede ofrecer una interfaz del sistema para solicitar credenciales. La API moderna `CredUIPromptForWindowsCredentials` no guarda credenciales por sí sola; la aplicación aún necesitaría escribirlas con Credential Manager. Conviene evaluar su integración, pero no asumir que elimina la exposición al proceso. Como alternativa implementable, un diálogo propio enmascarado puede explicar el contexto y guardar directamente mediante la API de Credential Manager.
- **UiPath Credential Manager local:** también puede guardar/recuperar credenciales del almacén de Windows y exponerlas como `SecureString`; ofrece capacidad similar con mayor dependencia de runtime, por lo que no se elige para la primera entrega.
- **UiPath Orchestrator Credential Assets:** cifra los activos en Orchestrator, pero introduce un servicio externo y transferencia al robot; queda descartado por el requisito local.
- **Autoguardado de Chrome/Edge:** descartado porque ARCA recomienda desactivar el autocompletado/guardado de contraseña.

## 10. Fuentes consultadas

- [ARCA: portal de Clave Fiscal](https://www.arca.gob.ar/claveFiscal/) y [enlace oficial actual de ingreso](https://auth.afip.gob.ar/contribuyente_/login.xhtml)
- [ARCA: Clave Fiscal y reglas de seguridad](https://www.arca.gob.ar/claveFiscal/)
- [ARCA: consejos de seguridad](https://www.arca.gob.ar/clavefiscal/ayuda/Consejos-de-seguridad.asp)
- [ARCA: búsqueda de servicios y Administración de Relaciones](https://serviciosweb.arca.gob.ar/genericos/guiasPasoPaso/VerGuia.aspx?id=26)
- [ARCA: documentación de WSAA y certificados para web services](https://www.arca.gob.ar/ws/documentacion/wsaa.asp)
- [Microsoft: Credential Manager, DPAPI y tratamiento de contraseñas](https://learn.microsoft.com/en-us/windows/win32/SecBP/handling-passwords)
- [Microsoft: diálogo CredUI para solicitar credenciales](https://learn.microsoft.com/en-us/windows/win32/api/wincred/nf-wincred-creduipromptforcredentialsa)
- [Microsoft: CredUIPromptForWindowsCredentials y persistencia](https://learn.microsoft.com/en-us/windows/win32/api/wincred/nf-wincred-creduipromptforwindowscredentialsw)
- [UiPath: recuperar credenciales de Windows Credential Manager como SecureString](https://docs.uipath.com/activities/other/latest/workflow/get-secure-credential)
- [UiPath: actividad local o Orchestrator para obtener credenciales](https://docs.uipath.com/activities/other/latest/workflow/get-username-password-x)
- [ARCA: términos del canal de reporte de vulnerabilidades](https://www.arca.gob.ar/seguridad/programa-divulgacion/terminos-y-condiciones.asp) — alcance específico: reporte de vulnerabilidades, no regla general encontrada para este RPA.
- [Playwright: aislamiento y contextos](https://playwright.dev/docs/browser-contexts)
- [Playwright: auto-waiting y actionability](https://playwright.dev/docs/actionability)
- [Python: estado de soporte y fin de vida de versiones](https://devguide.python.org/versions/)
- [Playwright 1.65.2 en PyPI](https://pypi.org/project/playwright/1.65.2/)
- [pywin32 312 en PyPI](https://pypi.org/project/pywin32/312/)

## Decisiones confirmadas

- La interfaz ofrecerá ingreso manual (por defecto) y perfiles opcionales en Windows Credential Manager. El modo perfil tendrá un campo enmascarado solo para crear o editar la credencial, nunca para iniciar sesión directamente desde la interfaz.
- Consulta de la cuenta activa, con alcance de solo lectura.
- Python + Playwright e instalación local en la primera etapa.
- El `.exe` se considera después de obtener un RPA funcional.
- Deben incorporarse manejo de errores, esperas explícitas y validación del resultado.
- No se autorizaron commits ni pushes.

## Pendiente

Validar el login y los selectores de la lista con la interfaz actual de ARCA durante la primera ejecución local, sin que se compartan credenciales ni datos de contribuyentes. La instalación permite seleccionar Python 3.11 o superior con soporte de seguridad y dependencias compatibles (Playwright 1.65.2 y pywin32 312), sin exigir 3.12. Se comprobó la resolución de dependencias para 3.15 de 64 bits; la validación funcional sigue pendiente. Python 3.9 y 3.10 se evitan por estar fuera de soporte. El diseño aprobado exige detenerse si la estructura no puede verificarse.






## Actualización: navegación automática tras el ingreso

Se reemplaza la confirmación manual de «Ver todos» por detección del portal y navegación al enlace observado `/portal/app/mis-servicios`. Se valida el host exacto, la ruta, la región principal, el título Mis servicios y las tarjetas con rol de botón y encabezado. No se exige un control Salir visible. La autenticación y desafíos siguen en manos del usuario. Las reglas de esta actualización prevalecen sobre las referencias anteriores al checkbox. Se conserva la sesión ante fallos recuperables y se permite reintentar. Validación automatizada con HTML sintético; validación real pendiente.
