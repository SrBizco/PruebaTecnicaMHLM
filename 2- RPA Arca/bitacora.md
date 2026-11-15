# Bitácora — RPA ARCA

## 15 de noviembre de 2026 — enfoque y riesgos previos

Se eligió una automatización local en Python con Playwright y navegador visible. La clave fiscal se ingresará manualmente en el sitio oficial de ARCA; el RPA consultará solo los servicios de la cuenta activa, sin guardar resultados ni sesión y sin modificar relaciones o trámites. Se decidió posponer el `.exe` hasta contar con una versión funcional.

La revisión preliminar identificó como riesgos centrales la exposición inherente de una sesión autenticada al proceso automatizado, los cambios de la interfaz de ARCA, la variabilidad de los desafíos de autenticación y la posible diferencia entre accesos visibles y permisos efectivos. Se documentaron mitigaciones de contexto temporal, lectura mínima, validación por estados y detención segura ante incertidumbre. No se halló en lo revisado una API pública estable para este listado ni una regla general clara sobre RPA de consulta; ambos puntos se mantienen como límites a comprobar antes de uso real.

**Estado:** diseño escrito para revisión; no hay código implementado ni commits/pushes.

## Verificación adicional de acceso y dominios
La página oficial de Clave Fiscal enlaza actualmente el ingreso con `auth.afip.gob.ar`; se actualizó el diseño para iniciar desde ARCA, validar el host exacto antes de la clave y acotar las redirecciones posteriores a subdominios oficiales. La documentación pública de WSAA requiere certificados y asociación a servicios de negocio, por lo que no reemplaza el listado visible solicitado. La revisión técnica del plan señaló como puntos a comprobar el alcance de condiciones de uso y que «Ver todos» representa el resultado funcional acordado, no una auditoría independiente de permisos.

## Decisión de autenticación y perfiles
Se acordó ofrecer ingreso manual y una modalidad opcional con credenciales guardadas en Windows Credential Manager. Para que sea utilizable por alguien que no conoce esa herramienta, el plan ahora contempla crear perfiles desde la propia interfaz, manejar más de una cuenta y eliminar perfiles. El alta tendría un diálogo enmascarado, consentimiento explícito y escritura directa al almacén de Windows, sin archivos ni argumentos de proceso. La modalidad manual sigue siendo la predeterminada. Se registró el mayor riesgo: la app recibe la clave al crear el perfil y al iniciar sesión, por lo que permanece expuesta en memoria durante esos pasos. Se añadió una evaluación de CredUI nativo; la API moderna de diálogo no persiste por sí misma las credenciales.

**Estado:** diseño actualizado para revisión. No hay código ni commits.
