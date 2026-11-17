# Software de terceros de la entrega portable

El visor es **DB Browser for SQLite 3.13.1, Windows x64**, distribuido sin modificar, con todas las DLL, plugins y licencias del ZIP oficial. No es una aplicación desarrollada para esta prueba. La versión se fija para reproducir el paquete; no se afirma que sea la última versión disponible.

- Binario oficial: https://github.com/sqlitebrowser/sqlitebrowser/releases/download/v3.13.1/DB.Browser.for.SQLite-v3.13.1-win64.zip
- SHA-256 del ZIP descargado: `22375e275ec42d96de1d3b8e9ea4ed86d2a3505c4d0ffcbd1af67aa4003e5e4d`.
- Release y procedencia: https://github.com/sqlitebrowser/sqlitebrowser/releases/tag/v3.13.1
- Código fuente de esa versión: https://github.com/sqlitebrowser/sqlitebrowser/tree/v3.13.1 . Se incluye además `terceros/dbbrowser-source.zip` en la entrega, con instrucciones de compilación y fuentes de dependencias integradas en el repositorio.

DB Browser se ofrece bajo MPL 2.0 y GPL 3.0 o posterior según sus avisos. Los textos originales están en `visor/licenses/` y en el código fuente. Se conservan los avisos MIT y de plugins. La disponibilidad del código fuente y sus licencias no depende de instalar el visor. Los hashes fijados por el empaquetador son controles de integridad/reproducibilidad, no una firma criptográfica del proveedor.

El ZIP oficial también incluye bibliotecas Qt 5.15.2 enlazadas dinámicamente. Se adjunta su LGPL 3.0 y el texto GPL 3.0 se conserva en las licencias del visor. Sus fuentes e instrucciones están disponibles en https://download.qt.io/archive/qt/5.15/5.15.2/single/ y https://code.qt.io/cgit/qt/qtbase.git/?h=v5.15.2 . No se imponen restricciones adicionales a reemplazar las DLL por versiones compatibles ni a depurar modificaciones de esos componentes, conforme a sus licencias. Las bibliotecas auxiliares mantienen sus respectivas licencias, no la del código del ejercicio.

Se incluye el aviso de licencia OpenSSL 1.1.1 para las DLL de la serie 1.1 distribuidas por el proveedor: https://github.com/openssl/openssl/blob/OpenSSL_1_1_1w/LICENSE . El proveedor empaqueta también el runtime de Microsoft Visual C++ necesario para su ejecución. Los avisos de plugins TIFF/WebP y demás recursos se conservan íntegros en `visor/licenses/LICENSE-PLUGINS`.

El paquete no instala servicios ni modifica asociaciones de archivos. El lanzador selecciona un archivo local de preferencias y desactiva el chequeo automático de versiones. El usuario puede usar las funciones propias del visor; no son parte del cargador ni del informe. La base se abre en modo lectura para evitar modificaciones accidentales.
