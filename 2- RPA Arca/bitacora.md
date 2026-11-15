# Bitácora — RPA ARCA

## 15 de noviembre de 2026 — enfoque y riesgos previos

Se eligió una automatización local en Python con Playwright y navegador visible. La clave fiscal se ingresará manualmente en el sitio oficial de ARCA; el RPA consultará solo los servicios de la cuenta activa, sin guardar resultados ni sesión y sin modificar relaciones o trámites. Se decidió posponer el `.exe` hasta contar con una versión funcional.

La revisión preliminar identificó como riesgos centrales la exposición inherente de una sesión autenticada al proceso automatizado, los cambios de la interfaz de ARCA, la variabilidad de los desafíos de autenticación y la posible diferencia entre accesos visibles y permisos efectivos. Se documentaron mitigaciones de contexto temporal, lectura mínima, validación por estados y detención segura ante incertidumbre. No se halló en lo revisado una API pública estable para este listado ni una regla general clara sobre RPA de consulta; ambos puntos se mantienen como límites a comprobar antes de uso real.

**Estado:** diseño escrito para revisión; no hay código implementado ni commits/pushes.

## Verificación adicional de acceso y dominios
La página oficial de Clave Fiscal enlaza actualmente el ingreso con `auth.afip.gob.ar`; se actualizó el diseño para iniciar desde ARCA, validar el host exacto antes de la clave y acotar las redirecciones posteriores a subdominios oficiales. La documentación pública de WSAA requiere certificados y asociación a servicios de negocio, por lo que no reemplaza el listado visible solicitado. La revisión técnica del plan señaló como puntos a comprobar el alcance de condiciones de uso y que «Ver todos» representa el resultado funcional acordado, no una auditoría independiente de permisos.

## Decisión de autenticación y perfiles
Se acordó ofrecer ingreso manual y una modalidad opcional con credenciales guardadas en Windows Credential Manager. Para que sea utilizable por alguien que no conoce esa herramienta, el plan ahora contempla crear perfiles desde la propia interfaz, manejar más de una cuenta y eliminar perfiles. El alta tendría un diálogo enmascarado, consentimiento explícito y escritura directa al almacén de Windows, sin archivos ni argumentos de proceso. La modalidad manual sigue siendo la predeterminada. Se registró el mayor riesgo: la app recibe la clave al crear el perfil y al iniciar sesión, por lo que permanece expuesta en memoria durante esos pasos. Se añadió una evaluación de CredUI nativo; la API moderna de diálogo no persiste por sí misma las credenciales.

**Estado en ese momento:** diseño actualizado para revisión; todavía no había código.

## Inicio de implementación
Se inició la primera versión en Python con Tkinter y Playwright visible. La capa de perfiles separa metadatos y claves en entradas diferentes de Credential Manager, de modo que listar cuentas no carga las contraseñas; solo se lee la seleccionada. La guía deja el alta, el envío del formulario y los desafíos de acceso bajo control de la persona.

La revisión técnica encontró que el acceso público de ARCA separa CUIT y clave. Se ajustó el modo de perfiles para completar la CUIT, esperar el avance manual y recuperar la clave solo después de verificar el paso HTTPS oficial, la CUIT visible y el campo concreto donde se completará. También se corrigió la lectura UTF-16 del blob de Credential Manager, se dejó la espera humana bombeando eventos de Playwright, y las cancelaciones, expiraciones y cierres fallan de forma segura.

**Ruling:** la aplicación pide que la persona abra manualmente «Ver todos» sin filtros y confirma el listado solo si detecta un indicador visible de sesión, título específico y sección semántica —la interfaz autenticada no se pudo validar con una cuenta de prueba—. Así reduce el riesgo de presentar páginas públicas, favoritos o enlaces generales como lista completa. Costo si es incorrecto: puede rechazar la UI real y requerir ajustar los marcadores después de la primera prueba local; la ausencia de filtros depende también de la confirmación humana.

**Ruling:** los resultados identifican el «perfil elegido» y no afirman que la cuenta autenticada coincida con él; en modo manual la identidad también queda sin verificar. No se inspecciona información adicional de la cuenta para comprobarla. Costo si es incorrecto: el usuario debe confirmar por su cuenta que abrió el CUIT esperado.

**Ruling:** la clave guardada solo se recupera si la segunda etapa muestra la CUIT del perfil, además de host HTTPS y un campo de contraseña reconocido. Costo si es incorrecto: puede detenerse cuando ARCA oculte o enmascare esa CUIT en el paso de clave y requerir que se use el modo manual.

**Ruling:** se recomienda Python 3.12 en lugar del 3.9 instalado, porque Python 3.9 y 3.10 ya están fuera de soporte en la fecha de implementación. Costo si es incorrecto: el usuario debe instalar otro intérprete antes de configurar el entorno.

**Estado:** implementación inicial revisada sintácticamente con Python 3.9.13; pendiente de validación visual del flujo real de ARCA y sus selectores. No hay commits ni pushes.


### Reconocimiento del portal y reducción de pasos manuales

La primera prueba real mostró que exigir «Salir» visible y un título de «servicios habilitados» no representaba la interfaz real. Las capturas y fragmentos HTML aportados permitieron identificar el enlace Ver todos y las tarjetas de Mis servicios. Se automatizó la navegación después del ingreso, eliminando el checkbox, y se mantuvo el navegador abierto ante errores recuperables. Se agregaron pruebas con datos ficticios para navegación, extracción de títulos, filtros y rechazo de páginas inesperadas/paginación. Queda pendiente repetir el flujo con ARCA real; las pruebas sintéticas no sustituyen esa validación.

### Empaquetado de la versión local

Se agrega una entrega ejecutable independiente sin reemplazar main.py. PyInstaller incluye intérprete y librerías; un lanzador verifica Chromium y lo instala si falta con el driver de Playwright incluido. El control inicial no lee credenciales ni abre ARCA. Los errores muestran mensajes de preparación sin volcados técnicos. Se agregaron pruebas de componentes presentes, instalación faltante y descarga fallida, más validación del binario con una caché de navegadores aislada. La prueba en una segunda PC sigue siendo necesaria.

### Corrección de detección de Chromium en el ejecutable

La prueba inicial con PLAYWRIGHT_BROWSERS_PATH explícito ocultó una diferencia del entorno empaquetado: Playwright buscaba el navegador junto al driver temporal, mientras el instalador lo descargaba en el perfil de Windows. Se unificó la ruta persistente antes de ambas operaciones y se agregaron pruebas sin configuración explícita y con el valor especial 0. Corrección preparada para la Release rpa-v1.0.1, autorizada por el usuario. Pasaron 22 pruebas y la comprobación del ejecutable con la configuración normal. La prueba con un perfil simulado fue bloqueada; queda pendiente verificar la instalación en la segunda PC.


### Release rpa-v1.0.2: perfiles y actualización de resultados

Se reprodujo un fallo exclusivo del empaquetado: faltaba win32timezone, importado dinámicamente al enumerar credenciales. Esto también interrumpía la inicialización antes de programar la recepción de mensajes, dejando la interfaz en Abriendo el portal. Se incluyó la dependencia y se añadió --check-app para probar el binario con un perfil ficticio aislado (eliminado al terminar), extracción sintética y visualización. La prueba empaquetada pasó y el usuario confirmó la corrección antes de autorizar esta Release.
